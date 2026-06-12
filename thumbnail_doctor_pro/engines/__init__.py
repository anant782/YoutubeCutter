"""
Engines package for Thumbnail Doctor Pro
"""
from .screen_capture import ScreenCaptureEngine, CaptureRegion
from .thumbnail_analyzer import ThumbnailAnalysisEngine
from .python_doctor import PythonProjectDoctor, ASTCodeAnalyzer, CodeIssue

__all__ = [
    "ScreenCaptureEngine", 
    "CaptureRegion", 
    "ThumbnailAnalysisEngine",
    "PythonProjectDoctor",
    "ASTCodeAnalyzer",
    "CodeIssue"
]
