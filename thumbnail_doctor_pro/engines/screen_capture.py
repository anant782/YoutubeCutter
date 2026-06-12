"""
Screen Capture Engine for Thumbnail Doctor Pro Ultimate
Supports full screen, region, and window capture using MSS, OpenCV, and Pillow
"""
import mss
import mss.tools
from PIL import Image, ImageGrab
import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
import io
from utils.logger import get_logger

logger = get_logger()

@dataclass
class CaptureRegion:
    x: int
    y: int
    width: int
    height: int

class ScreenCaptureEngine:
    def __init__(self):
        self.sct = mss.mss()
        self.last_capture: Optional[Image.Image] = None
    
    def capture_full_screen(self, monitor: int = 1) -> Image.Image:
        try:
            monitors = self.sct.monitors
            if monitor >= len(monitors):
                monitor = 1
            
            monitor_rect = monitors[monitor]
            screenshot = self.sct.grab(monitor_rect)
            
            img = Image.frombytes(
                'RGB',
                (screenshot.width, screenshot.height),
                screenshot.bgra,
                'raw',
                'BGRX'
            )
            
            self.last_capture = img
            logger.info(f"Captured full screen: {screenshot.width}x{screenshot.height}")
            return img
            
        except Exception as e:
            logger.error(f"Full screen capture failed: {e}")
            return ImageGrab.grab()
    
    def capture_region(self, region: CaptureRegion, monitor: int = 1) -> Image.Image:
        try:
            monitors = self.sct.monitors
            if monitor >= len(monitors):
                monitor = 1
            
            base_monitor = monitors[monitor]
            
            capture_rect = {
                'left': base_monitor['left'] + region.x,
                'top': base_monitor['top'] + region.y,
                'width': region.width,
                'height': region.height
            }
            
            screenshot = self.sct.grab(capture_rect)
            
            img = Image.frombytes(
                'RGB',
                (screenshot.width, screenshot.height),
                screenshot.bgra,
                'raw',
                'BGRX'
            )
            
            self.last_capture = img
            logger.info(f"Captured region: {region.width}x{region.height}")
            return img
            
        except Exception as e:
            logger.error(f"Region capture failed: {e}")
            raise e
    
    def capture_window(self, window_title: Optional[str] = None) -> Image.Image:
        try:
            if window_title:
                windows = self._find_windows(window_title)
                if windows:
                    return self.capture_region(windows[0])
            
            return self.capture_full_screen()
            
        except Exception as e:
            logger.error(f"Window capture failed: {e}")
            return self.capture_full_screen()
    
    def _find_windows(self, title_pattern: str) -> list:
        try:
            from ewmh import EWMH
            ewmh = EWMH()
            windows = ewmh.getClientList()
            
            matching = []
            for win in windows:
                win_name = ewmh.getWmName(win)
                if win_name and title_pattern.lower() in win_name.lower():
                    geom = ewmh.getWindowGeometry(win)
                    if geom:
                        matching.append(CaptureRegion(
                            x=geom.x,
                            y=geom.y,
                            width=geom.width,
                            height=geom.height
                        ))
            
            return matching
            
        except Exception as e:
            logger.warning(f"Could not find windows: {e}")
            return []
    
    def capture_to_cv2(self, image: Optional[Image.Image] = None) -> np.ndarray:
        img = image or self.last_capture
        if img is None:
            img = self.capture_full_screen()
        
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    def capture_to_bytes(self, image: Optional[Image.Image] = None, 
                        format: str = 'PNG') -> bytes:
        img = image or self.last_capture
        if img is None:
            img = self.capture_full_screen()
        
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        return buffer.getvalue()
    
    def save_capture(self, filepath: str, image: Optional[Image.Image] = None):
        img = image or self.last_capture
        if img is None:
            img = self.capture_full_screen()
        
        img.save(filepath)
        logger.info(f"Saved capture to {filepath}")
    
    def get_monitor_info(self) -> list:
        monitors = []
        for i, mon in enumerate(self.sct.monitors):
            monitors.append({
                'index': i,
                'left': mon['left'],
                'top': mon['top'],
                'width': mon['width'],
                'height': mon['height']
            })
        return monitors
    
    def live_monitor_start(self, region: Optional[CaptureRegion] = None,
                          callback=None):
        import threading
        
        def monitor_loop():
            while self._monitoring:
                if region:
                    img = self.capture_region(region)
                else:
                    img = self.capture_full_screen()
                
                if callback:
                    callback(img)
                
                import time
                time.sleep(0.1)
        
        self._monitoring = True
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        return thread
    
    def live_monitor_stop(self):
        self._monitoring = False
    
    def detect_photoshop_window(self) -> Optional[CaptureRegion]:
        photoshop_patterns = ['Adobe Photoshop', 'Photoshop']
        for pattern in photoshop_patterns:
            windows = self._find_windows(pattern)
            if windows:
                return windows[0]
        return None
    
    def capture_active_window(self) -> Image.Image:
        try:
            import pyautogui
            active_window = pyautogui.getActiveWindow()
            if active_window:
                return self.capture_region(CaptureRegion(
                    x=active_window.left,
                    y=active_window.top,
                    width=active_window.width,
                    height=active_window.height
                ))
        except Exception:
            pass
        
        return self.capture_full_screen()
    
    def close(self):
        self.sct.close()
