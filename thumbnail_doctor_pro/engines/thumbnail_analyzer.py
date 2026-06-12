"""
Thumbnail Analysis Engine for Thumbnail Doctor Pro Ultimate
Analyzes colors, fonts, composition, subjects, and CTR potential
"""
import cv2
import numpy as np
from PIL import Image
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import colorsys
from utils.logger import get_logger

logger = get_logger()

@dataclass
class ColorInfo:
    hex_color: str
    rgb: Tuple[int, int, int]
    percentage: float
    is_dominant: bool

@dataclass
class FontDetection:
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]

@dataclass
class SubjectDetection:
    type: str
    confidence: float
    bbox: Tuple[int, int, int, int]
    visibility_score: float

class ThumbnailAnalysisEngine:
    def __init__(self):
        self._ocr_engine = None
    
    def _get_ocr_engine(self):
        if self._ocr_engine is None:
            try:
                import easyocr
                self._ocr_engine = easyocr.Reader(['en'], gpu=False)
            except Exception as e:
                logger.warning(f"EasyOCR not available: {e}")
        return self._ocr_engine
    
    def analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        results = {
            'color_analysis': self._analyze_colors(image),
            'font_analysis': self._analyze_fonts(image),
            'composition_analysis': self._analyze_composition(image),
            'subject_analysis': self._analyze_subjects(image),
            'ctr_analysis': self._analyze_ctr(image)
        }
        
        results['scores'] = self._calculate_scores(results)
        results['recommendations'] = self._generate_recommendations(results)
        results['photoshop_fixes'] = self._generate_photoshop_fixes(results)
        
        return results
    
    def _analyze_colors(self, image: Image.Image) -> Dict[str, Any]:
        img_array = np.array(image.convert('RGB'))
        pixels = img_array.reshape(-1, 3)
        
        color_counts = Counter(map(tuple, pixels))
        total_pixels = len(pixels)
        
        dominant_colors = []
        for color, count in color_counts.most_common(10):
            percentage = (count / total_pixels) * 100
            if percentage > 1:
                hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
                dominant_colors.append(ColorInfo(
                    hex_color=hex_color,
                    rgb=color,
                    percentage=percentage,
                    is_dominant=len(dominant_colors) < 5
                ))
        
        color_harmony = self._analyze_color_harmony(dominant_colors)
        contrast_ratio = self._calculate_contrast_ratio(dominant_colors)
        
        issues = []
        if contrast_ratio < 4.5:
            issues.append({
                'type': 'low_contrast',
                'severity': 'high',
                'message': 'Low contrast between dominant colors'
            })
        
        if len(dominant_colors) > 7:
            issues.append({
                'type': 'too_many_colors',
                'severity': 'medium',
                'message': 'Too many colors may reduce visual impact'
            })
        
        return {
            'dominant_colors': [vars(c) for c in dominant_colors[:5]],
            'palette': [c.hex_color for c in dominant_colors],
            'harmony': color_harmony,
            'contrast_ratio': contrast_ratio,
            'issues': issues,
            'color_score': self._score_colors(dominant_colors, contrast_ratio)
        }
    
    def _analyze_color_harmony(self, colors: List[ColorInfo]) -> Dict[str, Any]:
        if len(colors) < 2:
            return {'type': 'monochromatic', 'score': 50}
        
        hues = []
        for color in colors[:5]:
            r, g, b = color.rgb
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            hues.append(h * 360)
        
        hue_diffs = []
        for i in range(len(hues) - 1):
            diff = abs(hues[i] - hues[i+1])
            if diff > 180:
                diff = 360 - diff
            hue_diffs.append(diff)
        
        avg_diff = np.mean(hue_diffs) if hue_diffs else 0
        
        harmony_type = 'analogous'
        if 120 <= avg_diff <= 150:
            harmony_type = 'triadic'
        elif 150 <= avg_diff <= 180:
            harmony_type = 'complementary'
        elif 90 <= avg_diff <= 120:
            harmony_type = 'split_complementary'
        
        return {
            'type': harmony_type,
            'average_hue_difference': avg_diff,
            'score': min(100, 100 - abs(avg_diff - 120) / 2)
        }
    
    def _calculate_contrast_ratio(self, colors: List[ColorInfo]) -> float:
        if len(colors) < 2:
            return 21
        
        def luminance(rgb):
            r, g, b = rgb
            return 0.2126 * (r/255)**2.2 + 0.7152 * (g/255)**2.2 + 0.0722 * (b/255)**2.2
        
        lightest = max(colors, key=lambda c: luminance(c.rgb))
        darkest = min(colors, key=lambda c: luminance(c.rgb))
        
        l1 = luminance(lightest.rgb)
        l2 = luminance(darkest.rgb)
        
        return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
    
    def _score_colors(self, colors: List[ColorInfo], contrast: float) -> float:
        score = 70
        
        if 3 <= len(colors) <= 5:
            score += 15
        elif len(colors) > 7:
            score -= 10
        
        if contrast >= 7:
            score += 15
        elif contrast >= 4.5:
            score += 10
        elif contrast < 3:
            score -= 15
        
        return min(100, max(0, score))
    
    def _analyze_fonts(self, image: Image.Image) -> Dict[str, Any]:
        ocr = self._get_ocr_engine()
        
        detected_text = []
        font_issues = []
        
        if ocr:
            try:
                img_array = np.array(image)
                results = ocr.readtext(img_array)
                
                for bbox, text, confidence in results:
                    if confidence > 0.5 and len(text.strip()) > 0:
                        (tl, tr, br, bl) = bbox
                        x_min = min(p[0] for p in [tl, tr, br, bl])
                        y_min = min(p[1] for p in [tl, tr, br, bl])
                        x_max = max(p[0] for p in [tl, tr, br, bl])
                        y_max = max(p[1] for p in [tl, tr, br, bl])
                        
                        width = x_max - x_min
                        height = y_max - y_min
                        
                        detected_text.append(FontDetection(
                            text=text,
                            confidence=confidence,
                            bbox=(x_min, y_min, width, height)
                        ))
                        
                        if width < 50 or height < 20:
                            font_issues.append({
                                'type': 'text_too_small',
                                'severity': 'high',
                                'message': f'Text "{text}" may be too small for mobile'
                            })
                
            except Exception as e:
                logger.error(f"OCR analysis failed: {e}")
        
        text_coverage = sum(d.bbox[2] * d.bbox[3] for d in detected_text) / (image.width * image.height)
        
        if text_coverage > 0.4:
            font_issues.append({
                'type': 'too_much_text',
                'severity': 'medium',
                'message': 'Too much text coverage reduces readability'
            })
        
        recommended_fonts = []
        if detected_text:
            recommended_fonts = [
                {'name': 'Anton', 'use_case': 'Gaming, Bold headlines'},
                {'name': 'Bebas Neue', 'use_case': 'Modern, Clean titles'},
                {'name': 'Montserrat ExtraBold', 'use_case': 'Professional, Tech'},
                {'name': 'League Spartan', 'use_case': 'Educational, Clear'},
                {'name': 'Impact', 'use_case': 'Classic, High contrast'}
            ]
        
        return {
            'detected_text': [vars(t) for t in detected_text],
            'text_count': len(detected_text),
            'readability_score': self._score_readability(detected_text, text_coverage),
            'issues': font_issues,
            'recommended_fonts': recommended_fonts
        }
    
    def _score_readability(self, text_detections: List[FontDetection], 
                          coverage: float) -> float:
        score = 70
        
        if len(text_detections) == 0:
            return 50
        
        avg_confidence = sum(t.confidence for t in text_detections) / len(text_detections)
        score += avg_confidence * 20
        
        if 0.1 <= coverage <= 0.3:
            score += 10
        elif coverage > 0.4:
            score -= 15
        
        return min(100, max(0, score))
    
    def _analyze_composition(self, image: Image.Image) -> Dict[str, Any]:
        width, height = image.size
        aspect_ratio = width / height
        
        img_array = np.array(image.convert('L'))
        
        edges = cv2.Canny(img_array, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        thirds_lines = {
            'vertical': [width // 3, 2 * width // 3],
            'horizontal': [height // 3, 2 * height // 3]
        }
        
        composition_issues = []
        
        if edge_density > 0.5:
            composition_issues.append({
                'type': 'visual_clutter',
                'severity': 'medium',
                'message': 'High visual complexity may distract viewers'
            })
        
        if aspect_ratio < 1.5:
            composition_issues.append({
                'type': 'non_standard_aspect',
                'severity': 'low',
                'message': 'Consider 16:9 aspect ratio for YouTube'
            })
        
        return {
            'aspect_ratio': aspect_ratio,
            'dimensions': {'width': width, 'height': height},
            'edge_density': edge_density,
            'rule_of_thirds_grid': thirds_lines,
            'balance_score': self._score_balance(img_array),
            'negative_space_score': self._score_negative_space(img_array),
            'issues': composition_issues
        }
    
    def _score_balance(self, img_array: np.ndarray) -> float:
        height, width = img_array.shape
        left_half = img_array[:, :width//2]
        right_half = img_array[:, width//2:]
        
        left_mean = np.mean(left_half)
        right_mean = np.mean(right_half)
        
        balance = 100 - abs(left_mean - right_mean) * 2
        return min(100, max(0, balance))
    
    def _score_negative_space(self, img_array: np.ndarray) -> float:
        _, binary = cv2.threshold(img_array, 200, 255, cv2.THRESH_BINARY)
        negative_space_ratio = np.sum(binary == 255) / binary.size
        
        if 0.2 <= negative_space_ratio <= 0.4:
            return 90
        elif 0.1 <= negative_space_ratio <= 0.5:
            return 70
        else:
            return 50
    
    def _analyze_subjects(self, image: Image.Image) -> Dict[str, Any]:
        img_array = np.array(image)
        
        faces_detected = self._detect_faces_simple(img_array)
        
        subjects = []
        if faces_detected:
            for face in faces_detected:
                subjects.append(SubjectDetection(
                    type='face',
                    confidence=0.8,
                    bbox=face,
                    visibility_score=0.85
                ))
        
        subject_issues = []
        if not subjects:
            subject_issues.append({
                'type': 'no_clear_subject',
                'severity': 'medium',
                'message': 'No clear subject detected. Consider adding a focal point.'
            })
        
        return {
            'subjects': [vars(s) for s in subjects],
            'subject_count': len(subjects),
            'focal_point': self._find_focal_point(img_array),
            'issues': subject_issues
        }
    
    def _detect_faces_simple(self, img_array: np.ndarray) -> List[Tuple[int, int, int, int]]:
        try:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(cascade_path)
            
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
            
        except Exception as e:
            logger.warning(f"Face detection failed: {e}")
            return []
    
    def _find_focal_point(self, img_array: np.ndarray) -> Dict[str, int]:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        saliency = cv2.saliency.StaticSaliencyFineGrained_create()
        try:
            (success, saliency_map) = saliency.computeSaliency(gray)
            
            if success:
                coords = np.unravel_index(np.argmax(saliency_map), saliency_map.shape)
                return {'x': int(coords[1]), 'y': int(coords[0])}
        except Exception:
            pass
        
        height, width = gray.shape
        return {'x': width // 2, 'y': height // 2}
    
    def _analyze_ctr(self, image: Image.Image) -> Dict[str, Any]:
        color_analysis = self._analyze_colors(image)
        font_analysis = self._analyze_fonts(image)
        composition_analysis = self._analyze_composition(image)
        
        curiosity_score = 60
        if composition_analysis.get('negative_space_score', 0) > 70:
            curiosity_score += 15
        
        emotional_impact = 65
        if color_analysis.get('color_score', 0) > 75:
            emotional_impact += 20
        
        professional_appearance = 70
        if font_analysis.get('readability_score', 0) > 70:
            professional_appearance += 15
        
        ctr_estimate = (curiosity_score + emotional_impact + 
                       professional_appearance + font_analysis.get('readability_score', 50)) / 4
        
        return {
            'curiosity_score': min(100, curiosity_score),
            'emotional_impact': min(100, emotional_impact),
            'professional_appearance': min(100, professional_appearance),
            'estimated_ctr_score': round(ctr_estimate, 1),
            'mobile_visibility': self._check_mobile_visibility(image, font_analysis)
        }
    
    def _check_mobile_visibility(self, image: Image.Image, 
                                font_analysis: Dict) -> Dict[str, Any]:
        width, height = image.size
        
        mobile_scale = 320 / width
        
        text_elements = font_analysis.get('detected_text', [])
        readable_on_mobile = all(
            t['bbox'][3] * mobile_scale >= 12 for t in text_elements
        )
        
        return {
            'readable_on_mobile': readable_on_mobile,
            'recommended_min_font_size': 16,
            'current_text_sizes': [t['bbox'][3] for t in text_elements]
        }
    
    def _calculate_scores(self, results: Dict[str, Any]) -> Dict[str, float]:
        color_score = results['color_analysis'].get('color_score', 50)
        font_score = results['font_analysis'].get('readability_score', 50)
        composition_score = (
            results['composition_analysis'].get('balance_score', 50) * 0.5 +
            results['composition_analysis'].get('negative_space_score', 50) * 0.5
        )
        subject_score = 70 if results['subject_analysis'].get('subject_count', 0) > 0 else 50
        ctr_score = results['ctr_analysis'].get('estimated_ctr_score', 50)
        
        overall = (color_score * 0.2 + font_score * 0.2 + 
                  composition_score * 0.2 + subject_score * 0.15 + ctr_score * 0.25)
        
        return {
            'color': round(color_score, 1),
            'font': round(font_score, 1),
            'composition': round(composition_score, 1),
            'subject': round(subject_score, 1),
            'ctr': round(ctr_score, 1),
            'overall': round(overall, 1)
        }
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        recommendations = []
        
        if results['color_analysis'].get('contrast_ratio', 0) < 4.5:
            recommendations.append({
                'category': 'color',
                'priority': 'high',
                'title': 'Increase Color Contrast',
                'description': 'Improve contrast between text and background for better readability',
                'action': 'Use complementary colors or increase brightness difference'
            })
        
        if results['font_analysis'].get('text_count', 0) > 5:
            recommendations.append({
                'category': 'font',
                'priority': 'medium',
                'title': 'Reduce Text Elements',
                'description': 'Too many text elements can overwhelm viewers',
                'action': 'Limit to 2-3 key text elements maximum'
            })
        
        if results['composition_analysis'].get('edge_density', 0) > 0.5:
            recommendations.append({
                'category': 'composition',
                'priority': 'medium',
                'title': 'Simplify Composition',
                'description': 'Reduce visual clutter for clearer message',
                'action': 'Remove unnecessary elements, use negative space'
            })
        
        if results['subject_analysis'].get('subject_count', 0) == 0:
            recommendations.append({
                'category': 'subject',
                'priority': 'high',
                'title': 'Add Clear Focal Point',
                'description': 'Thumbnails with clear subjects perform better',
                'action': 'Add a person, product, or clear focal element'
            })
        
        return recommendations
    
    def _generate_photoshop_fixes(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        fixes = []
        
        if results['color_analysis'].get('contrast_ratio', 0) < 4.5:
            fixes.append({
                'problem': 'Low contrast',
                'photoshop_fix': {
                    'menu_path': 'Layer > Layer Style > Outer Glow',
                    'settings': {
                        'Blend Mode': 'Screen',
                        'Opacity': '75%',
                        'Spread': '10',
                        'Size': '40',
                        'Color': '#FFFFFF'
                    },
                    'expected_result': 'Text will have better separation from background'
                }
            })
        
        if results['composition_analysis'].get('edge_density', 0) > 0.5:
            fixes.append({
                'problem': 'Visual clutter',
                'photoshop_fix': {
                    'menu_path': 'Filter > Blur > Gaussian Blur',
                    'settings': {
                        'Radius': '3-5 pixels',
                        'apply_to': 'Background layer only'
                    },
                    'expected_result': 'Background blur helps subject stand out'
                }
            })
        
        return fixes
