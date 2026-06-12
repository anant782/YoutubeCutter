"""
Thumbnail Doctor Pro Ultimate - Main Application Entry Point
"""
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QStyleFactory
from core.database import DatabaseManager
from core.settings_manager import SettingsManager
from ui.main_window import MainWindow
from utils.logger import setup_logger

def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    setup_logger()
    
    db_manager = DatabaseManager.get_instance()
    settings_manager = SettingsManager.get_instance()
    
    window = MainWindow(db_manager, settings_manager)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
