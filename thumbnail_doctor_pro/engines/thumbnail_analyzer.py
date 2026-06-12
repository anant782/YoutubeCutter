"""
Thumbnail Analysis Engine for Thumbnail Doctor Pro Ultimate
Lightweight AI-powered analysis using Gemini Vision API
Replaces heavy CV/OCR libraries to minimize RAM usage (<50MB)
"""
from PIL import Image
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

from utils.logger import get_logger
from models.gemini_manager import GeminiManager

logger = get_logger()


@dataclass
class ColorInfo:
    hex_color: str
    rgb: Tuple[int, int, int]
    percentage: float


class ThumbnailAnalyzer:
    """Analyzes thumbnails using Gemini Vision API to save RAM."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.gemini = GeminiManager(api_key)
        logger.info("ThumbnailAnalyzer initialized (Lightweight AI Mode)")

    def analyze(self, image_path: str) -> Dict[str, Any]:
        """Send image to Gemini Vision for comprehensive analysis."""
        logger.info(f"Analyzing thumbnail: {image_path}")
        
        try:
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            prompt = """
You are an expert YouTube thumbnail designer. Analyze this image and return ONLY valid JSON:
{
  "color_analysis": {
    "dominant_colors": ["#HEX1", "#HEX2"],
    "harmony_score": 85,
    "contrast_score": 90,
    "issues": [],
    "recommendations": []
  },
  "text_analysis": {
    "text_detected": true,
    "readability_score": 75,
    "word_count": 5,
    "font_suggestion": "Bebas Neue",
    "issues": [],
    "recommendations": []
  },
  "composition": {
    "rule_of_thirds_score": 80,
    "subject_position": "center",
    "negative_space_percentage": 25,
    "clutter_level": "low",
    "issues": [],
    "recommendations": []
  },
  "subject_analysis": {
    "faces_detected": 1,
    "emotion_detected": "excited",
    "eye_contact": true,
    "subject_visibility": "clear"
  },
  "ctr_prediction": {
    "estimated_ctr_score": 82,
    "verdict": "High potential",
    "psychological_triggers": [],
    "mobile_friendliness": 85
  },
  "photoshop_fixes": [
    {
      "issue": "Text lacks pop",
      "fix": "Add Outer Glow",
      "menu_path": "Layer > Layer Style > Outer Glow",
      "settings": {"blend_mode": "Screen", "opacity": "75%", "spread": "10px", "size": "40px", "color": "#FFD54F"}
    }
  ],
  "overall_score": 85,
  "summary": "Brief summary"
}
"""
            response_text = self.gemini.analyze_image(image, prompt)
            cleaned = response_text.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            try:
                result = json.loads(cleaned)
                result['success'] = True
                return result
            except json.JSONDecodeError as je:
                logger.warning(f"JSON parse error: {je}")
                return {'success': False, 'error': 'Failed to parse AI response', 'raw_response': cleaned}

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {"success": False, "error": str(e)}

    def get_color_palette(self, image_path: str) -> List[str]:
        """Extract dominant colors using simple pixel sampling (Very Low RAM)."""
        try:
            image = Image.open(image_path)
            image.thumbnail((100, 100))
            image = image.convert('RGB')
            colors = image.getcolors(256)
            if not colors:
                return []
            colors.sort(key=lambda x: x[0], reverse=True)
            palette = []
            for count, (r, g, b) in colors[:5]:
                hex_col = "#{:02x}{:02x}{:02x}".format(r, g, b)
                palette.append(hex_col)
            return palette
        except Exception as e:
            logger.error(f"Palette extraction failed: {e}")
            return []

    def quick_analyze(self, image_path: str) -> Dict[str, Any]:
        """Quick analysis for real-time preview (lower token usage)."""
        try:
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            prompt = """Quick analysis. Return JSON only:
{"overall_score": 0-100, "top_3_issues": [], "one_quick_fix": ""}
"""
            response = self.gemini.analyze_image(image, prompt)
            cleaned = response.replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned)
            result['success'] = True
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
