"""
Thumbnail Doctor Pro Ultimate - Main Application Entry Point
"""
import sys
import os
from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import Qt
from core.database import DatabaseManager
from core.settings_manager import SettingsManager
from ui.main_window import MainWindow
from utils.logger import setup_logger

def main():
    # Enable High DPI scaling before creating QApplication
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # Set application metadata
    app.setApplicationName("Thumbnail Doctor Pro Ultimate")
    app.setOrganizationName("ThumbnailDoctor")
    app.setApplicationVersion("1.0.0")
    
    setup_logger()
    
    db_manager = DatabaseManager.get_instance()
    settings_manager = SettingsManager.get_instance()
    
    window = MainWindow(db_manager, settings_manager)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
