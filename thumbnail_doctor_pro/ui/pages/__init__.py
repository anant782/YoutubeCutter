"""
UI Pages for Thumbnail Doctor Pro Ultimate
All page widgets for different application modes
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QFileDialog, QMessageBox, QTextEdit,
    QProgressBar, QListWidget, QListWidgetItem, QSplitter,
    QTreeWidget, QTreeWidgetItem, QComboBox, QLineEdit,
    QGroupBox, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QPixmap, QImage
from typing import Optional, Dict, Any
import os
from PIL import Image
import io

from utils.logger import get_logger
from core.database import DatabaseManager
from core.settings_manager import SettingsManager
from engines.screen_capture import ScreenCaptureEngine, CaptureRegion
from engines.thumbnail_analyzer import ThumbnailAnalysisEngine
from engines.python_doctor import PythonProjectDoctor
from models.gemini_manager import GeminiModelManager

logger = get_logger()

class BasePage(QFrame):
    def __init__(self, db: DatabaseManager, settings: SettingsManager):
        super().__init__()
        self.db = db
        self.settings = settings
        self.setStyleSheet("background-color: #1A1A1A; border-radius: 0px;")
        self._setup_ui()
    
    def _setup_ui(self):
        raise NotImplementedError

class DashboardPage(BasePage):
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("📊 Dashboard")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(title)
        
        stats_grid = QGridLayout()
        stats_grid.setSpacing(15)
        
        stat_cards = [
            ("🖼️ Thumbnails Analyzed", str(self.db.get_setting('thumbnail_count', '0')), "#4F46E5"),
            ("🐍 Projects Reviewed", str(self.db.get_setting('project_count', '0')), "#10B981"),
            ("⚠️ Issues Found", str(self.db.get_setting('issues_count', '0')), "#F59E0B"),
            ("✅ Fixes Applied", str(self.db.get_setting('fixes_count', '0')), "#EF4444")
        ]
        
        for i, (label, value, color) in enumerate(stat_cards):
            card = QFrame()
            card.setStyleSheet(f"""
                background-color: #2D2D2D;
                border-radius: 12px;
                border-left: 4px solid {color};
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 20, 20, 20)
            
            card_label = QLabel(label)
            card_label.setStyleSheet("color: #B0B0B0; font-size: 14px;")
            card_layout.addWidget(card_label)
            
            card_value = QLabel(value)
            card_value.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold;")
            card_layout.addWidget(card_value)
            
            row = i // 2
            col = i % 2
            stats_grid.addWidget(card, row, col)
        
        layout.addLayout(stats_grid)
        
        recent_activity = QGroupBox("Recent Activity")
        recent_layout = QVBoxLayout(recent_activity)
        
        self.activity_list = QListWidget()
        self.activity_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                border: none;
                border-radius: 8px;
                color: #B0B0B0;
            }
        """)
        recent_layout.addWidget(self.activity_list)
        
        layout.addWidget(recent_activity)
        layout.addStretch()
        
        self._load_recent_activity()
    
    def _load_recent_activity(self):
        history = self.db.get_history(limit=10)
        for item in history:
            timestamp = item.get('created_at', '')[:16] if item.get('created_at') else ''
            summary = f"{timestamp} - {item.get('analysis_type', 'Unknown')}: Score {item.get('score', 0):.0f}"
            self.activity_list.addItem(summary)

class ThumbnailCoachPage(BasePage):
    analysis_complete = Signal(dict)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QLabel("🖼️ Thumbnail Coach")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(header)
        
        splitter = QSplitter(Qt.Horizontal)
        
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel("Drop thumbnail image or press Ctrl+Shift+A to capture")
        self.image_label.setMinimumSize(600, 400)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            background-color: #2D2D2D;
            border-radius: 12px;
            color: #666666;
            font-size: 16px;
        """)
        left_layout.addWidget(self.image_label)
        
        btn_layout = QHBoxLayout()
        
        self.capture_btn = QPushButton("📸 Capture Screen (Ctrl+Shift+A)")
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4338CA;
            }
        """)
        self.capture_btn.clicked.connect(self.capture_screen)
        btn_layout.addWidget(self.capture_btn)
        
        self.load_btn = QPushButton("📁 Load Image")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
        """)
        self.load_btn.clicked.connect(self.load_image)
        btn_layout.addWidget(self.load_btn)
        
        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)
        
        splitter.addWidget(left_panel)
        
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                border: none;
                border-radius: 8px;
                color: #B0B0B0;
                padding: 15px;
            }
        """)
        right_layout.addWidget(self.results_text)
        
        right_panel.setWidget(right_widget)
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        self.current_image: Optional[Image.Image] = None
        self.capture_engine = ScreenCaptureEngine()
        self.analysis_engine = ThumbnailAnalysisEngine()
    
    def capture_screen(self):
        try:
            self.current_image = self.capture_engine.capture_full_screen()
            self._display_image(self.current_image)
            self.run_analysis()
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            QMessageBox.warning(self, "Capture Failed", str(e))
    
    def load_image(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load Thumbnail Image", "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if filepath:
            try:
                self.current_image = Image.open(filepath)
                self._display_image(self.current_image)
                self.run_analysis()
            except Exception as e:
                logger.error(f"Image load failed: {e}")
                QMessageBox.warning(self, "Load Failed", str(e))
    
    def _display_image(self, image: Image.Image):
        img_data = image.convert('RGB').tobytes()
        qimg = QImage(img_data, image.width, image.height, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        scaled = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)
    
    def run_analysis(self):
        if not self.current_image:
            return
        
        self.results_text.setText("Analyzing thumbnail...\n")
        
        try:
            results = self.analysis_engine.analyze_image(self.current_image)
            self._display_results(results)
            
            scores = results.get('scores', {})
            self.parent().parent().right_panel.update_scores(scores)
            
            for rec in results.get('recommendations', []):
                self.parent().parent().right_panel.add_recommendation(
                    rec.get('title', ''),
                    rec.get('description', ''),
                    rec.get('priority', 'medium')
                )
            
            self.db.save_thumbnail_analysis(
                "current_session",
                scores,
                results.get('color_analysis', {}),
                results.get('recommendations', []),
                results.get('photoshop_fixes', [])
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.results_text.setText(f"Analysis failed: {str(e)}")
    
    def _display_results(self, results: Dict[str, Any]):
        output = []
        output.append("=" * 50)
        output.append("THUMBNAIL ANALYSIS RESULTS")
        output.append("=" * 50)
        
        scores = results.get('scores', {})
        output.append(f"\n📊 SCORES:")
        output.append(f"   Overall: {scores.get('overall', 0)}/100")
        output.append(f"   Color: {scores.get('color', 0)}/100")
        output.append(f"   Font: {scores.get('font', 0)}/100")
        output.append(f"   Composition: {scores.get('composition', 0)}/100")
        output.append(f"   CTR Estimate: {scores.get('ctr', 0)}/100")
        
        color_analysis = results.get('color_analysis', {})
        output.append(f"\n🎨 COLOR PALETTE:")
        for color in color_analysis.get('palette', [])[:5]:
            output.append(f"   {color}")
        
        font_analysis = results.get('font_analysis', {})
        output.append(f"\n📝 TEXT DETECTED: {font_analysis.get('text_count', 0)} elements")
        
        recommendations = results.get('recommendations', [])
        if recommendations:
            output.append(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                output.append(f"   • {rec.get('title', '')}: {rec.get('action', '')}")
        
        self.results_text.setText('\n'.join(output))

class PhotoshopCoachPage(BasePage):
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("🎨 Photoshop Coach")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(header)
        
        info = QLabel("Upload a screenshot of your Photoshop workspace for AI-powered coaching")
        info.setStyleSheet("color: #B0B0B0; font-size: 14px; padding: 10px;")
        layout.addWidget(info)
        
        self.image_display = QLabel("Drag and drop Photoshop screenshot here")
        self.image_display.setMinimumHeight(300)
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.setStyleSheet("""
            background-color: #2D2D2D;
            border-radius: 12px;
            color: #666666;
        """)
        layout.addWidget(self.image_display)
        
        btn_layout = QHBoxLayout()
        
        capture_btn = QPushButton("📸 Capture Photoshop Window")
        capture_btn.clicked.connect(self.capture_photoshop)
        btn_layout.addWidget(capture_btn)
        
        analyze_btn = QPushButton("🔍 Get Photoshop Tips")
        analyze_btn.clicked.connect(self.get_tips)
        btn_layout.addWidget(analyze_btn)
        
        layout.addLayout(btn_layout)
        
        self.tips_display = QTextEdit()
        self.tips_display.setReadOnly(True)
        layout.addWidget(self.tips_display)
        
        layout.addStretch()
    
    def capture_photoshop(self):
        self.tips_display.setText("Capturing Photoshop window...")
    
    def get_tips(self):
        api_key = self.settings.get_api_key('gemini')
        if not api_key:
            self.tips_display.setText("Please set your Gemini API key in Settings first.")
            return
        
        self.tips_display.setText("Analyzing with AI...")

class PythonDoctorPage(BasePage):
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("🐍 Python Project Doctor")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(header)
        
        splitter = QSplitter(Qt.Horizontal)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Files"])
        self.file_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1E1E1E;
                border: none;
                border-radius: 8px;
                color: #B0B0B0;
            }
        """)
        left_layout.addWidget(self.file_tree)
        
        load_btn = QPushButton("📁 Load Project Folder")
        load_btn.clicked.connect(self.load_project)
        left_layout.addWidget(load_btn)
        
        splitter.addWidget(left_panel)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.code_viewer = QTextEdit()
        self.code_viewer.setReadOnly(True)
        self.code_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                border: none;
                border-radius: 8px;
                color: #B0B0B0;
                font-family: monospace;
            }
        """)
        right_layout.addWidget(self.code_viewer)
        
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        self.doctor = PythonProjectDoctor()
        self.current_project_path: Optional[str] = None
    
    def load_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.current_project_path = folder
            self._populate_file_tree(folder)
    
    def _populate_file_tree(self, path: str):
        self.file_tree.clear()
        
        for root, dirs, files in os.walk(path):
            if any(p.startswith('.') for p in root.split(os.sep)):
                continue
            
            rel_root = os.path.relpath(root, path)
            parent = self.file_tree if rel_root == '.' else None
            
            for file in sorted(files):
                if file.endswith('.py'):
                    item = QTreeWidgetItem([file])
                    if parent:
                        parent.addChild(item)
                    else:
                        self.file_tree.addTopLevelItem(item)
    
    def run_analysis(self):
        if not self.current_project_path:
            QMessageBox.warning(self, "No Project", "Please load a project first")
            return
        
        self.code_viewer.setText("Analyzing project...")
        
        try:
            results = self.doctor.analyze_project(self.current_project_path)
            self._display_analysis(results)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.code_viewer.setText(f"Analysis failed: {str(e)}")
    
    def _display_analysis(self, results: Dict[str, Any]):
        output = []
        output.append("=" * 50)
        output.append("PYTHON PROJECT ANALYSIS")
        output.append("=" * 50)
        
        output.append(f"\n📁 Files Analyzed: {results.get('files_analyzed', 0)}")
        
        scores = results.get('scores', {})
        output.append(f"\n📊 SCORES:")
        output.append(f"   Overall: {scores.get('overall', 0)}/100")
        output.append(f"   Code Quality: {scores.get('code_quality', 0)}/100")
        output.append(f"   Security: {scores.get('security', 0)}/100")
        output.append(f"   Maintainability: {scores.get('maintainability', 0)}/100")
        
        security_issues = results.get('security_issues', [])
        if security_issues:
            output.append(f"\n🔴 SECURITY ISSUES ({len(security_issues)}):")
            for issue in security_issues[:5]:
                output.append(f"   • {issue.get('message', '')}")
        
        recommendations = results.get('recommendations', [])
        if recommendations:
            output.append(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                output.append(f"   • {rec.get('title', '')}: {rec.get('action', '')}")
        
        self.code_viewer.setText('\n'.join(output))

class CodeReviewPage(PythonDoctorPage):
    def _setup_ui(self):
        super()._setup_ui()
        header = self.findChild(QLabel)
        if header:
            header.setText("📝 Code Review")

class SecurityAuditPage(PythonDoctorPage):
    def _setup_ui(self):
        super()._setup_ui()
        header = self.findChild(QLabel)
        if header:
            header.setText("🔒 Security Audit")

class ReportsPage(BasePage):
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("📈 Reports")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(header)
        
        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        layout.addWidget(self.report_display)
        
        btn_layout = QHBoxLayout()
        
        export_pdf = QPushButton("📄 Export PDF")
        export_pdf.clicked.connect(lambda: self.export_report('pdf'))
        btn_layout.addWidget(export_pdf)
        
        export_html = QPushButton("🌐 Export HTML")
        export_html.clicked.connect(lambda: self.export_report('html'))
        btn_layout.addWidget(export_html)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
    
    def export_report(self, format: str):
        QMessageBox.information(self, "Export", f"Exporting report as {format.upper()}")

class HistoryPage(BasePage):
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("📜 History")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(header)
        
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                border: none;
                border-radius: 8px;
                color: #B0B0B0;
            }
        """)
        layout.addWidget(self.history_list)
        
        self._load_history()
    
    def _load_history(self):
        history = self.db.get_history(limit=100)
        for item in history:
            timestamp = item.get('created_at', '')[:19] if item.get('created_at') else ''
            text = f"[{timestamp}] {item.get('analysis_type', 'Unknown')} - Score: {item.get('score', 0):.1f}"
            self.history_list.addItem(text)

class SettingsPage(BasePage):
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        header = QLabel("⚙️ Settings")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(header)
        
        api_group = QGroupBox("Google AI Settings")
        api_layout = QVBoxLayout(api_group)
        
        api_label = QLabel("Gemini API Key:")
        api_label.setStyleSheet("color: #B0B0B0;")
        api_layout.addWidget(api_label)
        
        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.Password)
        self.api_input.setPlaceholderText("Enter your Gemini API key")
        self.api_input.setStyleSheet("""
            QLineEdit {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 10px;
                color: #FFFFFF;
            }
        """)
        api_layout.addWidget(self.api_input)
        
        save_api_btn = QPushButton("💾 Save API Key")
        save_api_btn.clicked.connect(self.save_api_key)
        api_layout.addWidget(save_api_btn)
        
        layout.addWidget(api_group)
        
        theme_group = QGroupBox("Appearance")
        theme_layout = QVBoxLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 10px;
                color: #FFFFFF;
            }
        """)
        theme_layout.addWidget(self.theme_combo)
        
        layout.addWidget(theme_group)
        layout.addStretch()
    
    def save_api_key(self):
        api_key = self.api_input.text().strip()
        if api_key:
            self.settings.save_api_key('gemini', api_key)
            QMessageBox.information(self, "Success", "API key saved successfully!")
        else:
            QMessageBox.warning(self, "Error", "Please enter a valid API key")
