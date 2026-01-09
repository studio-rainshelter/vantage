"""
VANTAGE Image Viewer Dialog

새로운 창에서 이미지를 보여주고 ROI 영역을 편집할 수 있는 대화상자.
썸네일 더블 클릭 시 표시됨.
"""

from typing import Optional, List
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QFrame, QButtonGroup, QToolButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QKeySequence, QShortcut
import numpy as np

from config.constants import APP_NAME
from ui.styles import Styles
from core import RegionShape, ManualRegion, EffectType
from ui.components.roi_canvas import ROICanvas
from i18n import tr


class ImageViewerDialog(QDialog):
    """
    이미지 뷰어 및 ROI 편집 대화상자.
    
    Features:
    - 이미지 표시 및 확대/축소
    - ROI 영역 편집 (사각형/타원/올가미)
    - ESC 키로 닫기
    """
    
    regions_changed = Signal(str, list)  # path, regions
    
    def __init__(
        self,
        path: str,
        image: Optional[np.ndarray] = None,
        existing_regions: Optional[List[ManualRegion]] = None,
        detected_faces: Optional[List['FaceRegion']] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self._path = path
        self._image = image
        self._initial_regions = existing_regions or []
        self._initial_faces = detected_faces or []
        
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        
        if image is not None:
            self._canvas.set_image(image)
            self._canvas.set_regions(self._initial_regions)
            self._canvas.set_faces(self._initial_faces)
    
    def _setup_window(self):
        """Configure dialog window properties."""
        filename = Path(self._path).name
        self.setWindowTitle(f"{APP_NAME} - {filename}")
        self.setMinimumSize(600, 500)
        self.resize(900, 700)
        
        # 모달리스 대화상자로 설정 (메인 창과 독립적으로 작동)
        self.setModal(False)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        c = Styles.get_theme_colors()
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c['COLOR_BASE']};
            }}
            QFrame#toolbar {{
                background-color: {c['COLOR_BASE_LIGHT']};
                border-bottom: 1px solid {c['COLOR_BORDER']};
                padding: 4px;
            }}
            QToolButton {{
                background-color: transparent;
                border: 1px solid {c['COLOR_BORDER']};
                border-radius: 0px;
                padding: 6px 12px;
                color: {c['COLOR_TEXT']};
                font-size: 12px;
                min-width: 60px;
            }}
            QToolButton:hover {{
                background-color: {c['COLOR_BORDER_FOCUS']};
            }}
            QToolButton:checked {{
                background-color: {c['COLOR_ACCENT']};
                color: {c['COLOR_TEXT_ACCENT']};
                border-color: {c['COLOR_ACCENT']};
            }}
            QPushButton {{
                background-color: {c['COLOR_BASE_LIGHT']};
                border: 1px solid {c['COLOR_BORDER']};
                border-radius: 0px;
                padding: 8px 16px;
                color: {c['COLOR_TEXT']};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {c['COLOR_BORDER_FOCUS']};
            }}
            QPushButton#confirmBtn {{
                background-color: {c['COLOR_ACCENT']};
                border-color: {c['COLOR_ACCENT']};
                color: {c['COLOR_TEXT_ACCENT']};
            }}
            QPushButton#confirmBtn:hover {{
                background-color: {c['COLOR_ACCENT_HOVER']};
            }}
        """)
    
    def _setup_ui(self):
        """Initialize the viewer UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)
        toolbar_layout.setSpacing(4)
        
        # Shape buttons
        shape_label = QLabel(tr("viewer.shape") + ":")
        shape_label.setStyleSheet("color: #808080; margin-right: 8px;")
        toolbar_layout.addWidget(shape_label)
        
        self._shape_group = QButtonGroup(self)
        self._shape_group.setExclusive(True)
        
        # Select button
        self._select_btn = QToolButton()
        self._select_btn.setText("↖ " + tr("viewer.select"))
        self._select_btn.setCheckable(True)
        self._shape_group.addButton(self._select_btn, 3)
        toolbar_layout.addWidget(self._select_btn)

        # Rectangle button
        self._rect_btn = QToolButton()
        self._rect_btn.setText("▭ " + tr("viewer.rectangle"))
        self._rect_btn.setCheckable(True)
        self._rect_btn.setChecked(True)
        self._shape_group.addButton(self._rect_btn, 0)
        toolbar_layout.addWidget(self._rect_btn)
        
        # Ellipse button
        self._ellipse_btn = QToolButton()
        self._ellipse_btn.setText("⬭ " + tr("viewer.ellipse"))
        self._ellipse_btn.setCheckable(True)
        self._shape_group.addButton(self._ellipse_btn, 1)
        toolbar_layout.addWidget(self._ellipse_btn)
        
        # Freehand button
        self._freehand_btn = QToolButton()
        self._freehand_btn.setText("✎ " + tr("viewer.freehand"))
        self._freehand_btn.setCheckable(True)
        self._shape_group.addButton(self._freehand_btn, 2)
        toolbar_layout.addWidget(self._freehand_btn)
        
        toolbar_layout.addStretch()
        
        # Delete button
        self._delete_btn = QPushButton(tr("viewer.delete_selected"))
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._on_delete)
        toolbar_layout.addWidget(self._delete_btn)

        # Clear button
        self._clear_btn = QPushButton(tr("viewer.clear"))
        self._clear_btn.clicked.connect(self._on_clear)
        toolbar_layout.addWidget(self._clear_btn)
        
        # Region count
        self._count_label = QLabel("0 " + tr("viewer.regions"))
        self._count_label.setStyleSheet("color: #808080; margin-left: 16px;")
        toolbar_layout.addWidget(self._count_label)
        
        layout.addWidget(toolbar)
        
        # ROI Canvas
        self._canvas = ROICanvas()
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._canvas, 1)
        
        # Bottom buttons
        button_bar = QFrame()
        c = Styles.get_theme_colors()
        button_bar.setStyleSheet(f"background-color: {c['COLOR_BASE_LIGHT']}; border-top: 1px solid {c['COLOR_BORDER']};")
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(8, 8, 8, 8)
        button_layout.setSpacing(8)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton(tr("dialog.cancel"))
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton(tr("dialog.confirm"))
        confirm_btn.setObjectName("confirmBtn")
        confirm_btn.clicked.connect(self._on_confirm)
        button_layout.addWidget(confirm_btn)
        
        layout.addWidget(button_bar)
    
    def _connect_signals(self):
        """Connect UI signals."""
        self._shape_group.idClicked.connect(self._on_shape_changed)
        self._canvas.region_added.connect(self._on_region_changed)
        self._canvas.region_deleted.connect(self._on_region_changed)
        self._canvas.region_selected.connect(self._on_region_selected)
        
        # Zoom shortcuts
        QShortcut(QKeySequence.ZoomIn, self, activated=lambda: self._canvas.zoom(1.2))
        QShortcut(QKeySequence.ZoomOut, self, activated=lambda: self._canvas.zoom(1/1.2))
        QShortcut(QKeySequence("Ctrl+="), self, activated=lambda: self._canvas.zoom(1.2))
    
    def _on_shape_changed(self, id: int):
        """Handle shape tool selection."""
        # Deselect any selected region when changing tool
        self._canvas._selected_index = -1
        self._canvas.update()
        self._delete_btn.setEnabled(False)

        if id == 3:
            self._canvas.set_current_shape(None)
        else:
            shapes = [RegionShape.RECTANGLE, RegionShape.ELLIPSE, RegionShape.FREEHAND]
            if 0 <= id < len(shapes):
                self._canvas.set_current_shape(shapes[id])
    
    def _on_region_selected(self, index: int):
        """Handle region selection."""
        # Enable delete button if region is selected
        self._delete_btn.setEnabled(index >= 0)
        
        # Switch to select tool if not already
        if index >= 0 and self._shape_group.checkedId() != 3:
             self._select_btn.setChecked(True)
             self._canvas.set_current_shape(None)
    
    def _on_region_changed(self, *args):
        """Update region count display."""
        count = len(self._canvas.regions)
        self._count_label.setText(f"{count} " + tr("viewer.regions"))
    
    def _on_clear(self):
        """Clear all regions."""
        self._canvas.clear_regions()
        self._on_region_changed()
        self._delete_btn.setEnabled(False)
    
    def _on_delete(self):
        """Delete selected region."""
        selected = self._canvas.selected_region
        if selected:
            idx = self._canvas.regions.index(selected)
            self._canvas.remove_region(idx)
            self._delete_btn.setEnabled(False)
    
    def _on_confirm(self):
        """Save regions and close."""
        regions = self._canvas.regions
        self.regions_changed.emit(self._path, regions)
        self.accept()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Delete:
            # Delete selected region
            selected = self._canvas.selected_region
            if selected:
                idx = self._canvas.regions.index(selected)
                self._canvas.remove_region(idx)
        else:
            super().keyPressEvent(event)
