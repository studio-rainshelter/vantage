"""
VANTAGE Settings Dialog

Application preferences and configuration.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout, QWidget,
    QAbstractSpinBox, QSlider, QSizePolicy
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QFont, QCursor

from config import Settings
from config.constants import (
    MOSAIC_BLOCK_SIZE, BLUR_KERNEL_SIZE,
    FACE_MIN_NEIGHBORS, FACE_SCALE_FACTOR, FACE_DETECTION_CONFIDENCE
)
from ui.styles import Styles
from i18n import tr


class ModernSpinBox(QWidget):
    """
    Custom SpinBox with slider control.
    """
    def __init__(self, value_type=int, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        self.value_type = value_type

        # Slider (Left)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimumWidth(120)
        self.slider.setCursor(Qt.PointingHandCursor)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Spinbox (Right)
        if value_type == float:
            self.spin = QDoubleSpinBox()
        else:
            self.spin = QSpinBox()
            
        self.spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin.setAlignment(Qt.AlignCenter)
        self.spin.setFixedWidth(70) # Fixed width for clean alignment
        
        layout.addWidget(self.slider)
        layout.addWidget(self.spin)
        
        # Sync Slider <-> SpinBox
        self.spin.valueChanged.connect(self._on_spin_changed)
        self.slider.valueChanged.connect(self._on_slider_changed)
        
        # Internal state to prevent loop
        self._updating = False

    def _on_spin_changed(self, val):
        if self._updating: return
        self._updating = True
        
        if self.value_type == float:
            min_val = self.spin.minimum()
            max_val = self.spin.maximum()
            
            if max_val > min_val:
                ratio = (val - min_val) / (max_val - min_val)
                slider_val = int(ratio * 1000)
                self.slider.setValue(slider_val)
        else:
            self.slider.setValue(val)
            
        self._updating = False

    def _on_slider_changed(self, val):
        if self._updating: return
        self._updating = True
        
        if self.value_type == float:
            min_val = self.spin.minimum()
            max_val = self.spin.maximum()
            
            ratio = val / 1000.0
            new_val = min_val + ratio * (max_val - min_val)
            self.spin.setValue(new_val)
        else:
            self.spin.setValue(val)
            
        self._updating = False

    def setRange(self, min_val, max_val):
        self.spin.setRange(min_val, max_val)
        if self.value_type == float:
            self.slider.setRange(0, 1000)
        else:
            self.slider.setRange(min_val, max_val)
        
    def setValue(self, val):
        self.spin.setValue(val)
        
    def value(self):
        return self.spin.value()
        
    def setSingleStep(self, step):
        self.spin.setSingleStep(step)
        if self.value_type == int:
            self.slider.setSingleStep(step)



class SettingsDialog(QDialog):
    """
    Settings/preferences dialog.
    
    Allows user to configure:
    - Mosaic block size
    - Blur kernel size
    - Face detection parameters (Neighbors, Scale, IOU)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._settings = Settings()
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Initialize dialog UI."""
        self.setWindowTitle(tr("menu.settings.preferences"))
        self.setMinimumWidth(450) # Slightly wider for descriptions
        
        # Determine colors dynamically based on current theme
        c = Styles.get_theme_colors()
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c['COLOR_BASE']};
                color: {c['COLOR_TEXT']};
            }}
            QGroupBox {{
                border: 1px solid {c['COLOR_BORDER']};
                margin-top: 24px;
                padding-top: 16px;
                font-weight: bold;
                color: {c['COLOR_TEXT']};
                background-color: transparent;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                background-color: {c['COLOR_BASE']};
            }}
            QLabel {{
                color: {c['COLOR_TEXT']};
            }}
            QLabel.hint {{
                color: {c['COLOR_TEXT_DIM']};
                font-size: 11px;
                font-weight: normal;
                margin-bottom: 4px;
            }}
            QSpinBox, QDoubleSpinBox {{
                background-color: {c['COLOR_BASE_LIGHT']};
                color: {c['COLOR_TEXT']};
                border: 1px solid {c['COLOR_BORDER']};
                padding: 4px;
                min-width: 80px;
            }}
            QPushButton {{
                background-color: {c['COLOR_BASE_LIGHT']};
                color: {c['COLOR_TEXT']};
                border: 1px solid {c['COLOR_BORDER']};
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background-color: {c['COLOR_BORDER_FOCUS']};
            }}
            QPushButton[class="primary"] {{
                background-color: {c['COLOR_ACCENT']};
                color: {c['COLOR_TEXT_ACCENT']};
                border-color: {c['COLOR_ACCENT']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Processing group
        proc_group = QGroupBox(tr("menu.process.title"))
        proc_layout = QFormLayout(proc_group)
        proc_layout.setSpacing(12)
        
        self.block_size_spin = ModernSpinBox(int)
        self.block_size_spin.setRange(2, 50)
        self.block_size_spin.setValue(MOSAIC_BLOCK_SIZE)
        
        self.blur_spin = ModernSpinBox(int)
        self.blur_spin.setRange(3, 101)
        self.blur_spin.setSingleStep(2)
        self.blur_spin.setValue(BLUR_KERNEL_SIZE)
        
        proc_layout.addRow(tr("settings.mosaic_size") + ":", self.block_size_spin)
        proc_layout.addRow(tr("settings.blur_size") + ":", self.blur_spin)
        
        layout.addWidget(proc_group)
        
        # Face Detection Group
        face_group = QGroupBox(tr("settings.face_detection"))
        face_layout = QFormLayout(face_group)
        face_layout.setSpacing(16) # More spacing for descriptions
        
        # Helper to add row with description
        def add_setting(label_key, widget, hint_key=None):
            label = QLabel(tr(label_key) + ":")
            
            container = QWidget()
            v_layout = QVBoxLayout(container)
            v_layout.setContentsMargins(0, 0, 0, 0)
            v_layout.setSpacing(4)
            
            v_layout.addWidget(widget)
            
            if hint_key:
                hint = QLabel(tr(hint_key))
                hint.setProperty("class", "hint")
                hint.setWordWrap(True)
                v_layout.addWidget(hint)
            
            face_layout.addRow(label, container)
        
        # Min Neighbors
        self.min_neighbors_spin = ModernSpinBox(int)
        self.min_neighbors_spin.setRange(1, 15)
        self.min_neighbors_spin.setValue(FACE_MIN_NEIGHBORS)
        add_setting("settings.min_neighbors", self.min_neighbors_spin, "settings.hint_neighbors")
        
        # Scale Factor
        self.scale_factor_spin = ModernSpinBox(float)
        self.scale_factor_spin.setRange(1.01, 1.5)
        self.scale_factor_spin.setSingleStep(0.01)
        self.scale_factor_spin.setValue(FACE_SCALE_FACTOR)
        add_setting("settings.scale_factor", self.scale_factor_spin, "settings.hint_scale")
        
        # IOU Threshold
        self.iou_spin = ModernSpinBox(float)
        self.iou_spin.setRange(0.1, 1.0)
        self.iou_spin.setSingleStep(0.1)
        self.iou_spin.setValue(0.3)
        add_setting("settings.iou_threshold", self.iou_spin, "settings.hint_iou")
        
        layout.addWidget(face_group)
        
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
        # Processing
        self.block_size_spin.setValue(
            self._settings.get('mosaic_block_size', MOSAIC_BLOCK_SIZE)
        )
        self.blur_spin.setValue(
            self._settings.get('blur_kernel_size', BLUR_KERNEL_SIZE)
        )
        
        # Face Detection
        self.min_neighbors_spin.setValue(
            self._settings.get('face_min_neighbors', FACE_MIN_NEIGHBORS)
        )
        self.scale_factor_spin.setValue(
            self._settings.get('face_scale_factor', FACE_SCALE_FACTOR)
        )
        self.iou_spin.setValue(
            self._settings.get('face_iou_threshold', 0.3)
        )
    
    def _save_and_close(self):
        """Save settings and close dialog."""
        # Processing
        self._settings.set('mosaic_block_size', self.block_size_spin.value())
        self._settings.set('blur_kernel_size', self.blur_spin.value())
        
        # Face Detection
        self._settings.set('face_min_neighbors', self.min_neighbors_spin.value())
        self._settings.set('face_scale_factor', self.scale_factor_spin.value())
        self._settings.set('face_iou_threshold', self.iou_spin.value())
        
        self._settings.save()
        self.accept()
