#!/usr/bin/env python3
"""
VANTAGE - Visual Anonymization & Tactical Graphics Editor

Industrial-grade image anonymization application.

Usage:
    python main.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    """Application entry point."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    
    from config import Settings
    from config.constants import (
        APP_NAME, FONT_UI, FONT_FALLBACK, FONT_SIZE_MD
    )
    from ui import MainWindow
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Studio RainShelter")
    
    # Set default font
    font = QFont(FONT_UI)
    font.setPixelSize(FONT_SIZE_MD)
    if not font.exactMatch():
        font = QFont(FONT_FALLBACK)
        font.setPixelSize(FONT_SIZE_MD)
    app.setFont(font)
    
    # Load settings
    settings = Settings()
    
    # Set language from settings
    from i18n import Translator
    translator = Translator()
    translator.set_language(settings.language)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
