"""
VANTAGE Settings Dialog

Application preferences and configuration.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt

from config import Settings
from config.constants import (
    COLOR_BASE, COLOR_BORDER, COLOR_TEXT,
    MOSAIC_BLOCK_SIZE, BLUR_KERNEL_SIZE, FACE_DETECTION_CONFIDENCE,
    SUPPORTED_LANGUAGES
)
from i18n import tr, Translator


class SettingsDialog(QDialog):
    """
    Settings/preferences dialog.
    
    Allows user to configure:
    - Default language
    - Mosaic block size
    - Blur kernel size
    - Face detection confidence
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._settings = Settings()
        self._translator = Translator()
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Initialize dialog UI."""
        self.setWindowTitle(tr("menu.settings.preferences"))
        self.setMinimumWidth(400)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_BASE};
                color: {COLOR_TEXT};
            }}
            QGroupBox {{
                border: 1px solid {COLOR_BORDER};
                margin-top: 16px;
                padding-top: 16px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Language group
        lang_group = QGroupBox("Language / 언어")
        lang_layout = QFormLayout(lang_group)
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("한국어", "ko")
        lang_layout.addRow("Language:", self.lang_combo)
        
        layout.addWidget(lang_group)
        
        # Processing group
        proc_group = QGroupBox(tr("menu.process.title"))
        proc_layout = QFormLayout(proc_group)
        
        self.block_size_spin = QSpinBox()
        self.block_size_spin.setRange(2, 50)
        self.block_size_spin.setValue(MOSAIC_BLOCK_SIZE)
        proc_layout.addRow("Mosaic Block Size:", self.block_size_spin)
        
        self.blur_spin = QSpinBox()
        self.blur_spin.setRange(3, 101)
        self.blur_spin.setSingleStep(2)
        self.blur_spin.setValue(BLUR_KERNEL_SIZE)
        proc_layout.addRow("Blur Kernel Size:", self.blur_spin)
        
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setSingleStep(0.1)
        self.confidence_spin.setValue(FACE_DETECTION_CONFIDENCE)
        proc_layout.addRow("Detection Confidence:", self.confidence_spin)
        
        layout.addWidget(proc_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton(tr("dialog.cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton(tr("dialog.ok"))
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_settings(self):
        """Load current settings into UI."""
        # Language
        lang = self._settings.language
        index = self.lang_combo.findData(lang)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)
        
        # Processing
        self.block_size_spin.setValue(
            self._settings.get('mosaic_block_size', MOSAIC_BLOCK_SIZE)
        )
        self.blur_spin.setValue(
            self._settings.get('blur_kernel_size', BLUR_KERNEL_SIZE)
        )
        self.confidence_spin.setValue(
            self._settings.get('face_detection_confidence', FACE_DETECTION_CONFIDENCE)
        )
    
    def _save_and_close(self):
        """Save settings and close dialog."""
        # Language
        new_lang = self.lang_combo.currentData()
        if new_lang != self._settings.language:
            self._settings.language = new_lang
            self._translator.set_language(new_lang)
        
        # Processing
        self._settings.set('mosaic_block_size', self.block_size_spin.value())
        self._settings.set('blur_kernel_size', self.blur_spin.value())
        self._settings.set('face_detection_confidence', self.confidence_spin.value())
        
        self._settings.save()
        self.accept()
