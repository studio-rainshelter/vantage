"""
VANTAGE Inspector Pane

Slide-in panel for detailed image editing and inspection.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QSizePolicy, QComboBox, QSlider
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QPixmap, QImage
import numpy as np

from config.constants import (
    INSPECTOR_WIDTH, COLOR_BORDER, COLOR_TEXT, COLOR_TEXT_DIM,
    FONT_SIZE_SM, SPACING_MD, MosaicMode
)
from i18n import tr


class InspectorPane(QFrame):
    """
    Slide-in inspector panel for image editing.
    
    Features:
    - Image preview with ruler
    - Face detection results display
    - Manual region editing controls
    - Mode selection (Auto/Manual/Override/Append)
    """
    
    mode_changed = Signal(str)
    apply_requested = Signal()
    close_requested = Signal()
    edit_requested = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._current_path: Optional[str] = None
        self._is_visible = False
        self._faces: list = [] # Initialize _faces
        self._manual_regions: list = [] # Initialize _manual_regions
        
        self._setup_ui()
        self._setup_animation()
    
    def _setup_ui(self):
        """Initialize the inspector UI."""
        self.setFixedWidth(INSPECTOR_WIDTH)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1A1A1A;
                border-left: 1px solid {COLOR_BORDER};
            }}
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)
        
        # Header
        header = QHBoxLayout()
        
        self.title_label = QLabel(tr("inspector.title"))
        self.title_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLOR_TEXT};
        """)
        header.addWidget(self.title_label)
        
        layout.addLayout(header)
        
        # Image preview
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet(f"""
            background-color: #0F0F0F;
            border: 1px solid {COLOR_BORDER};
        """)
        layout.addWidget(self.preview_label)
        
        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        # Filename
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel(tr("inspector.filename") + ":"))
        self.filename_label = QLabel("—")
        self.filename_label.setStyleSheet(f"color: {COLOR_TEXT_DIM};")
        filename_layout.addWidget(self.filename_label, 1)
        info_layout.addLayout(filename_layout)
        
        # Dimensions
        dims_layout = QHBoxLayout()
        dims_layout.addWidget(QLabel(tr("inspector.dimensions") + ":"))
        self.dims_label = QLabel("—")
        self.dims_label.setStyleSheet(f"color: {COLOR_TEXT_DIM};")
        dims_layout.addWidget(self.dims_label, 1)
        info_layout.addLayout(dims_layout)
        
        # Detected faces
        faces_layout = QHBoxLayout()
        self.faces_label_title = QLabel(tr("inspector.faces") + ":") # Added for translation update
        faces_layout.addWidget(self.faces_label_title)
        self.faces_label = QLabel("0")
        self.faces_label.setStyleSheet(f"color: {COLOR_TEXT_DIM};")
        faces_layout.addWidget(self.faces_label, 1)
        info_layout.addLayout(faces_layout)
        
        layout.addLayout(info_layout)
        
        # Mode selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel(tr("inspector.mode") + ":"))
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItem(tr("mode.auto"), MosaicMode.AUTO)
        self.mode_combo.addItem(tr("mode.manual"), MosaicMode.MANUAL)
        self.mode_combo.addItem(tr("mode.override"), MosaicMode.OVERRIDE)
        self.mode_combo.addItem(tr("mode.append"), MosaicMode.APPEND)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo, 1)
        
        layout.addLayout(mode_layout)

        # Mode description
        self.mode_desc_label = QLabel()
        self.mode_desc_label.setWordWrap(True)
        self.mode_desc_label.setStyleSheet(f"""
            color: {COLOR_TEXT_DIM};
            font-size: {FONT_SIZE_SM}px;
            margin-top: 4px;
            margin-bottom: 8px;
            padding-bottom: 4px;
        """)
        layout.addWidget(self.mode_desc_label)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Edit Button
        self.edit_btn = QPushButton(tr("inspector.edit"))
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.clicked.connect(self.edit_requested.emit)
        button_layout.addWidget(self.edit_btn)
        
        # Save Button
        self.apply_btn = QPushButton(tr("inspector.save"))
        self.apply_btn.setCursor(Qt.PointingHandCursor)
        self.apply_btn.setProperty("accent", True)
        self.apply_btn.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(self.apply_btn)

        layout.addLayout(button_layout)
    
    def _on_save_clicked(self):
        """Handle save button click with animation."""
        self.apply_requested.emit()
        
        # Flash animation
        self.apply_btn.setProperty("success", True)
        self.style().polish(self.apply_btn)
        self.apply_btn.setEnabled(False)
        
        # Reset after 200ms
        QTimer.singleShot(200, self._reset_save_button)
        
    def _reset_save_button(self):
        """Reset save button style."""
        self.apply_btn.setProperty("success", False)
        self.style().polish(self.apply_btn)
        self.apply_btn.setEnabled(True)
    
    def _setup_animation(self):
        """Setup slide animation."""
        self._animation = QPropertyAnimation(self, b"maximumWidth")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def show_panel(self):
        """Slide in the panel."""
        if self._is_visible:
            return
        
        self._is_visible = True
        self.show()
        
        # Initial description update
        self._update_mode_description()
        
        self._animation.stop()
        self._animation.setStartValue(0)
        self._animation.setEndValue(INSPECTOR_WIDTH)
        self._animation.start()
    
    def hide_panel(self):
        """Slide out the panel."""
        if not self._is_visible:
            return
        
        self._is_visible = False
        
        self._animation.stop()
        self._animation.setStartValue(INSPECTOR_WIDTH)
        self._animation.setEndValue(0)
        self._animation.finished.connect(self._on_hide_finished)
        self._animation.start()
    
    def _on_hide_finished(self):
        """Called when hide animation completes."""
        self._animation.finished.disconnect(self._on_hide_finished)
        self.hide()
        self.close_requested.emit()
    
    @property
    def current_path(self) -> Optional[str]:
        """Get currently inspected image path."""
        return self._current_path

    def set_image(
        self,
        path: str,
        preview: Optional[np.ndarray] = None,
        dimensions: Optional[tuple] = None,
        face_count: int = 0,
        mode: Optional[str] = None,
        faces: Optional[list] = None,
        manual_regions: Optional[list] = None
    ):
        """Set the image to inspect."""
        from pathlib import Path
        
        self._current_path = path
        self._faces = faces or []
        self._manual_regions = manual_regions or []
        self.filename_label.setText(Path(path).name)
        
        if dimensions:
            self.dims_label.setText(f"{dimensions[0]} × {dimensions[1]}")
        else:
            self.dims_label.setText("—")
        
        self.faces_label.setText(str(face_count))
        
        if preview is not None:
            self._set_preview_image(preview)
            
        # Update mode if provided
        if mode:
            index = self.mode_combo.findData(mode)
            if index >= 0:
                self.mode_combo.setCurrentIndex(index)
            
        # Update description in case language changed or first load
        self._update_mode_description()
    
    def _set_preview_image(self, image: np.ndarray):
        """Set preview image from numpy array."""
        if image is None:
            return
        
        h, w = image.shape[:2]
        
        # Convert numpy array to QImage
        if len(image.shape) == 3:
            import cv2
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            qimage = QImage(
                rgb.data, w, h, w * 3,
                QImage.Format_RGB888
            )
        else:
            qimage = QImage(
                image.data, w, h, w,
                QImage.Format_Grayscale8
            )
        
        pixmap = QPixmap.fromImage(qimage)
        
        # Draw Overlays using QPainter
        if self._faces or self._manual_regions:
            from PySide6.QtGui import QPainter, QColor, QPen
            painter = QPainter(pixmap)
            
            # Draw Faces (Blue)
            pen_face = QPen(QColor(0, 120, 255), 2)
            painter.setPen(pen_face)
            for face in self._faces:
                if hasattr(face, 'x'):
                    x, y, fw, fh = face.x, face.y, face.width, face.height
                else:
                    x, y, fw, fh = face
                painter.drawRect(x, y, fw, fh)
                
            # Draw Manual Regions (Red)
            pen_manual = QPen(QColor(255, 50, 50), 2)
            painter.setPen(pen_manual)
            for region in self._manual_regions:
                # region is ManualRegion object
                x, y, w, h = int(region.x), int(region.y), int(region.width), int(region.height)
                painter.drawRect(x, y, w, h)
                
            painter.end()

        # Scale to fit width while maintaining aspect ratio
        scaled = pixmap.scaledToWidth(INSPECTOR_WIDTH - SPACING_MD * 2, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)
    
    def _on_mode_changed(self, index: int):
        """Handle mode selection change."""
        mode = self.mode_combo.currentData()
        self.mode_changed.emit(mode)
        self._update_mode_description()

    def _update_mode_description(self):
        """Update the description label based on selected mode."""
        mode = self.mode_combo.currentData()
        if not mode:
            return
            
        desc_key = f"mode_desc.{mode}"
        self.mode_desc_label.setText(tr(desc_key))
    
    @property
    def current_mode(self) -> str:
        """Get currently selected mode."""
        return self.mode_combo.currentData()
    
    def update_translations(self):
        """Update UI text after language change."""
        self.title_label.setText(tr("inspector.title"))
        self.faces_label_title.setText(tr("inspector.faces") + ":")
        self.apply_btn.setText(tr("inspector.save"))
        self.edit_btn.setText(tr("inspector.edit"))
        
        # Update mode combo items
        current_mode = self.mode_combo.currentData()
        self.mode_combo.clear()
        self.mode_combo.addItem(tr("mode.auto"), MosaicMode.AUTO)
        self.mode_combo.addItem(tr("mode.manual"), MosaicMode.MANUAL)
        self.mode_combo.addItem(tr("mode.override"), MosaicMode.OVERRIDE)
        self.mode_combo.addItem(tr("mode.append"), MosaicMode.APPEND)
        
        # Restore selection
        index = self.mode_combo.findData(current_mode)
        if index >= 0:
            self.mode_combo.setCurrentIndex(index)
            
        self._update_mode_description()
