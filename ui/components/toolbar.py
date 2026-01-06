"""
VANTAGE Main Toolbar

Top toolbar with primary action buttons and language switcher.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QToolBar, QToolButton, QWidget, QLabel, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction

from config.constants import TOOLBAR_HEIGHT, COLOR_BORDER, COLOR_ACCENT
from i18n import tr, Translator
from .language_switcher import LanguageSwitcher


class MainToolbar(QToolBar):
    """
    Main application toolbar.
    
    Contains primary actions:
    - Open files/folders
    - Auto detect
    - Mosaic/Blur
    - Save/Export
    - Language switcher
    """
    
    open_files = Signal()
    open_folder = Signal()
    save_triggered = Signal()
    export_triggered = Signal()
    auto_detect = Signal()
    apply_mosaic = Signal()
    apply_blur = Signal()
    revert_mosaic = Signal()
    select_all = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._translator = Translator()
        
        self._setup_ui()
        self._translator.add_observer(self._update_translations)
    
    def _setup_ui(self):
        """Initialize toolbar layout and actions."""
        self.setMovable(False)
        self.setFloatable(False)
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.setMinimumHeight(TOOLBAR_HEIGHT)
        self.setStyleSheet(f"""
            QToolBar {{
                spacing: 4px;
                padding: 8px;
                border-bottom: 1px solid {COLOR_BORDER};
            }}
            QToolBar::separator {{
                width: 1px;
                background-color: {COLOR_BORDER};
                margin: 4px 8px;
            }}
        """)
        
        # === File Operations ===
        
        # Open Files action
        self.open_action = QAction(tr("toolbar.open"), self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_files.emit)
        self.addAction(self.open_action)
        
        # Open Folder action
        self.open_folder_action = QAction(tr("menu.file.open_folder"), self)
        self.open_folder_action.setShortcut("Ctrl+Shift+O")
        self.open_folder_action.triggered.connect(self.open_folder.emit)
        self.addAction(self.open_folder_action)
        
        self.addSeparator()
        
        # === Selection ===
        
        # Select All action
        self.select_all_action = QAction(tr("toolbar.select_all"), self)
        self.select_all_action.setShortcut("Ctrl+A")
        self.select_all_action.triggered.connect(self.select_all.emit)
        self.addAction(self.select_all_action)
        
        self.addSeparator()
        
        # === Processing ===
        
        # Auto detect action
        self.auto_action = QAction(tr("toolbar.auto"), self)
        self.auto_action.setShortcut("Ctrl+D")
        self.auto_action.triggered.connect(self.auto_detect.emit)
        self.addAction(self.auto_action)
        
        # Mosaic action
        self.mosaic_action = QAction(tr("toolbar.mosaic"), self)
        self.mosaic_action.setShortcut("Ctrl+M")
        self.mosaic_action.triggered.connect(self.apply_mosaic.emit)
        self.addAction(self.mosaic_action)
        
        # Blur action
        self.blur_action = QAction(tr("toolbar.blur"), self)
        self.blur_action.setShortcut("Ctrl+B")
        self.blur_action.triggered.connect(self.apply_blur.emit)
        self.addAction(self.blur_action)
        
        # Revert action
        self.revert_action = QAction(tr("toolbar.revert"), self)
        self.revert_action.setShortcut("Ctrl+Z")
        self.revert_action.triggered.connect(self.revert_mosaic.emit)
        self.addAction(self.revert_action)
        
        self.addSeparator()
        
        # === Export ===
        
        # Save action
        self.save_action = QAction(tr("toolbar.save"), self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_triggered.emit)
        self.addAction(self.save_action)
        
        # Export action
        self.export_action = QAction(tr("toolbar.export"), self)
        self.export_action.setShortcut("Ctrl+E")
        self.export_action.triggered.connect(self.export_triggered.emit)
        self.addAction(self.export_action)
        
        # === Spacer ===
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)
        
        # === Language Switcher (Right side) ===
        self.lang_switcher = LanguageSwitcher()
        self.addWidget(self.lang_switcher)
    
    def _update_translations(self, lang: str = None):
        """Update action text after language change."""
        self.open_action.setText(tr("toolbar.open"))
        self.open_folder_action.setText(tr("menu.file.open_folder"))
        self.select_all_action.setText(tr("toolbar.select_all"))
        self.auto_action.setText(tr("toolbar.auto"))
        self.mosaic_action.setText(tr("toolbar.mosaic"))
        self.blur_action.setText(tr("toolbar.blur"))
        self.revert_action.setText(tr("toolbar.revert"))
        self.save_action.setText(tr("toolbar.save"))
        self.export_action.setText(tr("toolbar.export"))
