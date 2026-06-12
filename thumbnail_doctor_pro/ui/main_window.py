"""
Main Window for Thumbnail Doctor Pro Ultimate
Professional dark-themed desktop application UI
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QStackedWidget, QPushButton, QLabel, QFrame, QScrollArea,
    QToolBar, QStatusBar, QMenu, QMenuBar, QSystemTrayIcon,
    QMessageBox, QFileDialog, QDialog, QListWidget, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QProgressBar, QGroupBox,
    QComboBox, QLineEdit, QCheckBox, QSpinBox, QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal, Slot, QTimer, QThread
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor, QPalette, QAction, QActionGroup
from typing import Optional, Dict, Any
import os

from utils.logger import get_logger
from core.database import DatabaseManager
from core.settings_manager import SettingsManager

logger = get_logger()

class SidebarButton(QPushButton):
    def __init__(self, text: str, icon_path: Optional[str] = None):
        super().__init__(text)
        self.setFixedHeight(50)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding-left: 20px;
                text-align: left;
                font-size: 14px;
                color: #B0B0B0;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: rgba(79, 70, 229, 0.2);
                color: #818CF8;
                border-left: 3px solid #818CF8;
            }
        """)

class MainSidebar(QFrame):
    mode_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(250)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(5)
        
        logo_label = QLabel("🎯 Thumbnail Doctor")
        logo_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #818CF8;
            padding: 15px;
        """)
        layout.addWidget(logo_label)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #333333;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        self.buttons = {}
        modes = [
            ("dashboard", "📊 Dashboard"),
            ("thumbnail", "🖼️ Thumbnail Coach"),
            ("photoshop", "🎨 Photoshop Coach"),
            ("doctor", "🐍 Python Doctor"),
            ("review", "📝 Code Review"),
            ("security", "🔒 Security Audit"),
            ("reports", "📈 Reports"),
            ("history", "📜 History"),
            ("settings", "⚙️ Settings")
        ]
        
        button_group = []
        for mode_id, mode_name in modes:
            btn = SidebarButton(mode_name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=mode_id: self._on_button_clicked(m))
            layout.addWidget(btn)
            self.buttons[mode_id] = btn
            button_group.append(btn)
        
        layout.addStretch()
        
        version_label = QLabel("v1.0.0 Ultimate")
        version_label.setStyleSheet("color: #666; font-size: 11px; padding: 10px;")
        layout.addWidget(version_label)
    
    def _on_button_clicked(self, mode_id: str):
        for btn in self.buttons.values():
            btn.setChecked(False)
        self.buttons[mode_id].setChecked(True)
        self.mode_changed.emit(mode_id)
    
    def set_active_mode(self, mode_id: str):
        if mode_id in self.buttons:
            for btn in self.buttons.values():
                btn.setChecked(False)
            self.buttons[mode_id].setChecked(True)

class TopBar(QFrame):
    analyze_clicked = Signal()
    quick_scan_clicked = Signal()
    export_clicked = Signal()
    search_triggered = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(60)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.search_triggered.emit)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 8px 15px;
                color: #FFFFFF;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #818CF8;
            }
        """)
        layout.addWidget(self.search_input)
        
        layout.addStretch()
        
        action_buttons = [
            ("🔍 Analyze", self.analyze_clicked),
            ("⚡ Quick Scan", self.quick_scan_clicked),
            ("📤 Export", self.export_clicked)
        ]
        
        for text, signal_obj in action_buttons:
            btn = QPushButton(text)
            btn.setFixedHeight(36)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4F46E5;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 0 20px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #4338CA;
                }
            """)
            btn.clicked.connect(signal_obj.emit)
            layout.addWidget(btn)
        
        layout.addSpacing(20)
        
        self.notification_btn = QPushButton("🔔")
        self.notification_btn.setFixedSize(36, 36)
        self.notification_btn.setCursor(Qt.PointingHandCursor)
        self.notification_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 18px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        layout.addWidget(self.notification_btn)
        
        self.theme_toggle = QPushButton("🌙")
        self.theme_toggle.setFixedSize(36, 36)
        self.theme_toggle.setCursor(Qt.PointingHandCursor)
        self.theme_toggle.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 18px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        layout.addWidget(self.theme_toggle)

class ContentArea(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(800)
        self._pages = {}
    
    def add_page(self, name: str, widget: QWidget):
        self.addWidget(widget)
        self._pages[name] = widget
    
    def show_page(self, name: str):
        if name in self._pages:
            self.setCurrentWidget(self._pages[name])

class RightPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(350)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        title = QLabel("Analysis Results")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #FFFFFF;
            padding-bottom: 10px;
        """)
        layout.addWidget(title)
        
        self.scores_group = QGroupBox("Scores")
        scores_layout = QVBoxLayout(self.scores_group)
        
        self.score_bars = {}
        score_labels = ["Overall", "Quality", "Security", "Performance"]
        for label in score_labels:
            bar_container = QWidget()
            bar_layout = QHBoxLayout(bar_container)
            bar_layout.setContentsMargins(0, 0, 0, 0)
            
            lbl = QLabel(label)
            lbl.setFixedWidth(100)
            lbl.setStyleSheet("color: #B0B0B0; font-size: 13px;")
            bar_layout.addWidget(lbl)
            
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(0)
            progress.setTextVisible(False)
            progress.setFixedHeight(8)
            progress.setStyleSheet("""
                QProgressBar {
                    background-color: #2D2D2D;
                    border-radius: 4px;
                }
                QProgressBar::chunk {
                    background-color: #818CF8;
                    border-radius: 4px;
                }
            """)
            bar_layout.addWidget(progress)
            
            value_lbl = QLabel("0")
            value_lbl.setFixedWidth(40)
            value_lbl.setStyleSheet("color: #818CF8; font-weight: bold;")
            bar_layout.addWidget(value_lbl)
            
            scores_layout.addWidget(bar_container)
            self.score_bars[label.lower()] = (progress, value_lbl)
        
        layout.addWidget(self.scores_group)
        
        self.recommendations_group = QGroupBox("Recommendations")
        rec_layout = QVBoxLayout(self.recommendations_group)
        
        self.recommendations_list = QListWidget()
        self.recommendations_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                border: none;
                border-radius: 8px;
                color: #B0B0B0;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #2D2D2D;
            }
            QListWidget::item:selected {
                background-color: rgba(129, 140, 248, 0.2);
            }
        """)
        rec_layout.addWidget(self.recommendations_list)
        
        layout.addWidget(self.recommendations_group)
        
        layout.addStretch()
    
    def update_scores(self, scores: Dict[str, float]):
        colors = {
            'overall': '#818CF8',
            'quality': '#34D399',
            'security': '#F87171',
            'performance': '#FBBF24'
        }
        
        for key, (progress, value_lbl) in self.score_bars.items():
            score = scores.get(key, 0)
            progress.setValue(int(score))
            value_lbl.setText(f"{score:.0f}")
            
            progress.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #2D2D2D;
                    border-radius: 4px;
                }}
                QProgressBar::chunk {{
                    background-color: {colors.get(key, '#818CF8')};
                    border-radius: 4px;
                }}
            """)
    
    def add_recommendation(self, title: str, description: str, priority: str = "medium"):
        item_text = f"{'🔴' if priority == 'high' else '🟡' if priority == 'medium' else '🟢'} {title}"
        item = QListWidgetItem(item_text)
        item.setToolTip(description)
        self.recommendations_list.addItem(item)
    
    def clear_recommendations(self):
        self.recommendations_list.clear()

class MainWindow(QMainWindow):
    def __init__(self, db_manager: DatabaseManager, settings_manager: SettingsManager):
        super().__init__()
        
        self.db = db_manager
        self.settings = settings_manager
        
        self.setWindowTitle("Thumbnail Doctor Pro Ultimate")
        self.setMinimumSize(1400, 900)
        
        self._setup_styles()
        self._setup_ui()
        self._setup_menu()
        self._connect_signals()
        
        logger.info("Main window initialized")
    
    def _setup_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0F0F0F;
            }
            QFrame {
                background-color: #1A1A1A;
            }
        """)
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.sidebar = MainSidebar()
        main_layout.addWidget(self.sidebar)
        
        center_splitter = QSplitter(Qt.Vertical)
        
        self.top_bar = TopBar()
        center_splitter.addWidget(self.top_bar)
        
        content_splitter = QSplitter(Qt.Horizontal)
        
        self.content_area = ContentArea()
        self._setup_content_pages()
        content_splitter.addWidget(self.content_area)
        
        self.right_panel = RightPanel()
        content_splitter.addWidget(self.right_panel)
        
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 0)
        
        center_splitter.addWidget(content_splitter)
        
        main_layout.addWidget(center_splitter)
    
    def _setup_content_pages(self):
        from ui.pages import (
            DashboardPage, ThumbnailCoachPage, PhotoshopCoachPage,
            PythonDoctorPage, CodeReviewPage, SecurityAuditPage,
            ReportsPage, HistoryPage, SettingsPage
        )
        
        pages = [
            ("dashboard", DashboardPage(self.db, self.settings)),
            ("thumbnail", ThumbnailCoachPage(self.db, self.settings)),
            ("photoshop", PhotoshopCoachPage(self.db, self.settings)),
            ("doctor", PythonDoctorPage(self.db, self.settings)),
            ("review", CodeReviewPage(self.db, self.settings)),
            ("security", SecurityAuditPage(self.db, self.settings)),
            ("reports", ReportsPage(self.db, self.settings)),
            ("history", HistoryPage(self.db, self.settings)),
            ("settings", SettingsPage(self.db, self.settings))
        ]
        
        for name, page_widget in pages:
            self.content_area.add_page(name, page_widget)
    
    def _setup_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #1A1A1A;
                color: #FFFFFF;
                border-bottom: 1px solid #2D2D2D;
            }
            QMenuBar::item:selected {
                background-color: #2D2D2D;
            }
            QMenu {
                background-color: #1A1A1A;
                color: #FFFFFF;
                border: 1px solid #2D2D2D;
            }
            QMenu::item:selected {
                background-color: #4F46E5;
            }
        """)
        
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open Project", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save Report", self)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        tools_menu = menubar.addMenu("Tools")
        
        capture_action = QAction("Capture Screen", self)
        capture_action.setShortcut("Ctrl+Shift+A")
        capture_action.triggered.connect(self._capture_screen)
        tools_menu.addAction(capture_action)
        
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _connect_signals(self):
        self.sidebar.mode_changed.connect(self._switch_mode)
        self.top_bar.analyze_clicked.connect(self._run_analysis)
        self.top_bar.quick_scan_clicked.connect(self._quick_scan)
        self.top_bar.export_clicked.connect(self._export_results)
    
    def _switch_mode(self, mode: str):
        self.content_area.show_page(mode)
        logger.info(f"Switched to mode: {mode}")
    
    def _open_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            current_page = self.content_area.currentWidget()
            if hasattr(current_page, 'load_project'):
                current_page.load_project(folder)
    
    def _capture_screen(self):
        current_page = self.content_area.currentWidget()
        if hasattr(current_page, 'capture_screen'):
            current_page.capture_screen()
    
    def _run_analysis(self):
        current_page = self.content_area.currentWidget()
        if hasattr(current_page, 'run_analysis'):
            current_page.run_analysis()
    
    def _quick_scan(self):
        current_page = self.content_area.currentWidget()
        if hasattr(current_page, 'quick_scan'):
            current_page.quick_scan()
    
    def _export_results(self):
        current_page = self.content_area.currentWidget()
        if hasattr(current_page, 'export_results'):
            current_page.export_results()
    
    def _show_about(self):
        QMessageBox.about(
            self,
            "About Thumbnail Doctor Pro Ultimate",
            """<h2>Thumbnail Doctor Pro Ultimate</h2>
            <p>Version 1.0.0</p>
            <p>AI-powered thumbnail analysis and Python code review tool.</p>
            <p>Built with PySide6 and Google Gemini AI.</p>"""
        )
    
    def closeEvent(self, event):
        logger.info("Application closing")
        event.accept()
