"""
VANTAGE Thumbnail Grid

Virtualized grid view for displaying image thumbnails.
"""

from typing import List, Optional, Callable
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QFrame, QLabel,
    QVBoxLayout, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QImage
import numpy as np

from config.constants import THUMBNAIL_SIZE, THUMBNAIL_GAP, COLOR_ACCENT
from ui.styles import Styles


class ThumbnailItem(QFrame):
    """
    Single thumbnail item widget.
    
    Displays image thumbnail with optional 'M' marker
    for manually edited images.
    """
    
    clicked = Signal(str)       # Emits path on single click
    double_clicked = Signal(str)  # Emits path on double click
    toggled = Signal(str, bool)   # Emits path and checked state
    
    def __init__(
        self,
        path: str,
        thumbnail: Optional[np.ndarray] = None,
        has_manual_edit: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.path = path
        self.has_manual_edit = has_manual_edit
        self._selected = False
        self._checked = False
        self._faces = []
        self._manual_regions = []
        self._original_size = (0, 0)
        
        self._setup_ui()
        
        if thumbnail is not None:
            self.set_thumbnail(thumbnail)
    
    def _setup_ui(self):
        """Initialize the UI components."""
        self.setFixedSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        self.setStyleSheet(Styles.get_thumbnail_style(False))
        self.setCursor(Qt.PointingHandCursor)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(False)
        layout.addWidget(self.image_label)
        
        # Manual edit marker ('M')
        self.marker_label = QLabel("M")
        self.marker_label.setStyleSheet(Styles.get_manual_marker_style())
        self.marker_label.setFixedSize(24, 24)
        self.marker_label.setVisible(self.has_manual_edit)
        
        # Position marker in top-right corner
        # Helper for positioning
        self.marker_label.setParent(self)
        self.marker_label.move(THUMBNAIL_SIZE - 28, 4)

        # Checkbox overlay
        self.checkbox = QCheckBox(self)
        self.checkbox.setStyleSheet(f"""
            QCheckBox {{
                spacing: 0px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                background-color: #2A2A2A;
                border: 1px solid {COLOR_ACCENT};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLOR_ACCENT};
            }}
        """)
        self.checkbox.move(6, 6)
        self.checkbox.toggled.connect(self._on_toggled)
        self.update_style()
        
    def update_style(self):
        """Update style based on current theme."""
        c = Styles.get_theme_colors()
        self.setStyleSheet(Styles.get_thumbnail_style(self._selected))
        self.marker_label.setStyleSheet(Styles.get_manual_marker_style())
        
        self.checkbox.setStyleSheet(f"""
            QCheckBox {{
                spacing: 0px;
                background-color: transparent;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                background-color: #2A2A2A;
                border: 1px solid {c['COLOR_ACCENT']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {c['COLOR_ACCENT']};
            }}
        """)
        
    def _on_toggled(self, checked: bool):
        """Handle internal toggle."""
        self._checked = checked
        self.toggled.emit(self.path, checked)
        
    def set_checked(self, checked: bool):
        """Set checked state."""
        self.checkbox.setChecked(checked)
        
    @property
    def is_checked(self) -> bool:
        return self._checked
    
    def set_thumbnail(self, thumbnail: np.ndarray):
        """Set the thumbnail image from numpy array."""
        self._thumbnail_data = thumbnail
        self._update_display()

    def set_overlays(self, faces: list, manual_regions: list, original_w: int, original_h: int):
        """Set detected faces and manual regions to display overlay."""
        self._faces = faces
        self._manual_regions = manual_regions
        self._original_size = (original_w, original_h)
        self._update_display()
        
    def _update_display(self):
        """Update the displayed pixmap with overlays."""
        if not hasattr(self, '_thumbnail_data') or self._thumbnail_data is None:
            return
            
        # Convert to QImage/QPixmap
        h, w = self._thumbnail_data.shape[:2]
        channels = self._thumbnail_data.shape[2] if len(self._thumbnail_data.shape) > 2 else 1
        
        if channels == 3:
            import cv2
            rgb = cv2.cvtColor(self._thumbnail_data, cv2.COLOR_BGR2RGB)
            image = QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888)
        elif channels == 4:
            image = QImage(self._thumbnail_data.data, w, h, w * 4, QImage.Format_RGBA8888)
        else:
            image = QImage(self._thumbnail_data.data, w, h, w, QImage.Format_Grayscale8)
            
        # Create mutable pixmap
        pixmap = QPixmap.fromImage(image)
        
        # Draw overlays if present
        if (self._faces or self._manual_regions) and self._original_size[0] > 0:
            from PySide6.QtGui import QPainter, QColor, QPen
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Scale factor
            scale_x = w / self._original_size[0]
            scale_y = h / self._original_size[1]
            scale = min(scale_x, scale_y) # Uniform scaling
            
            # Draw Faces (Blue)
            if self._faces:
                painter.setPen(QPen(QColor(0, 120, 255), 2))
                painter.setBrush(Qt.NoBrush)
                for face in self._faces:
                    # Check if face is object or tuple/list
                    if hasattr(face, 'x'):
                        fx = int(face.x * scale)
                        fy = int(face.y * scale)
                        fw = int(face.width * scale)
                        fh = int(face.height * scale)
                    else:
                        fx = int(face[0] * scale)
                        fy = int(face[1] * scale)
                        fw = int(face[2] * scale)
                        fh = int(face[3] * scale)
                    
                    painter.drawRect(fx, fy, fw, fh)

            # Draw Manual Regions (Red)
            if self._manual_regions:
                painter.setPen(QPen(QColor(255, 50, 50), 2))
                painter.setBrush(Qt.NoBrush)
                for region in self._manual_regions:
                    # region is ManualRegion object with x, y, width, height
                    rx = int(region.x * scale)
                    ry = int(region.y * scale)
                    rw = int(region.width * scale)
                    rh = int(region.height * scale)
                    painter.drawRect(rx, ry, rw, rh)

            painter.end()
            
        self.image_label.setPixmap(pixmap)
    
    def set_manual_edit(self, has_edit: bool):
        """Update manual edit marker visibility."""
        self.has_manual_edit = has_edit
        self.marker_label.setVisible(has_edit)
    
    def set_selected(self, selected: bool):
        """Update selection state."""
        self._selected = selected
        self.setStyleSheet(Styles.get_thumbnail_style(selected))
    
    @property
    def is_selected(self) -> bool:
        return self._selected
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.path)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click."""
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.path)
        super().mouseDoubleClickEvent(event)


class ThumbnailGrid(QScrollArea):
    """
    Scrollable grid view for image thumbnails.
    
    Features:
    - Virtualized rendering for performance
    - Grid layout with automatic column adjustment
    - Selection support
    - Drag and drop target
    """
    
    item_clicked = Signal(str)
    item_double_clicked = Signal(str)
    selection_changed = Signal(list)  # Emits list of CHECKED paths (for batch ops)
    active_changed = Signal(str)      # Emits ACTIVE path (for inspector)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._items: dict[str, ThumbnailItem] = {}
        self._checked_paths: List[str] = []
        self._active_path: Optional[str] = None
        self._columns = 4
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialize the grid layout."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container widget
        self.container = QWidget()
        self.container.setObjectName("gridContainer")
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(THUMBNAIL_GAP)
        self.grid_layout.setContentsMargins(
            THUMBNAIL_GAP, THUMBNAIL_GAP,
            THUMBNAIL_GAP, THUMBNAIL_GAP
        )
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.setWidget(self.container)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Apply initial style
        self.update_style()
    
    def add_thumbnail(
        self,
        path: str,
        thumbnail: Optional[np.ndarray] = None,
        has_manual_edit: bool = False
    ) -> ThumbnailItem:
        """Add a new thumbnail to the grid."""
        if path in self._items:
            return self._items[path]
        
        item = ThumbnailItem(path, thumbnail, has_manual_edit)
        item.clicked.connect(self._on_item_clicked)
        item.double_clicked.connect(self._on_item_double_clicked)
        item.toggled.connect(self._on_item_toggled)
        
        self._items[path] = item
        self._relayout()
        
        return item
    
    def remove_thumbnail(self, path: str):
        """Remove a thumbnail from the grid."""
        if path in self._items:
            item = self._items.pop(path)
            item.deleteLater()
            
            # Remove from checked
            if path in self._checked_paths:
                self._checked_paths.remove(path)
                self.selection_changed.emit(self._checked_paths)
            
            # Reset active if removed
            if path == self._active_path:
                self._active_path = None
                self.active_changed.emit(None)
                
            self._relayout()
    
    def clear(self):
        """Remove all thumbnails."""
        for item in self._items.values():
            item.deleteLater()
        self._items.clear()
        self._checked_paths.clear()
        self._active_path = None
        self.selection_changed.emit([])
        self.active_changed.emit(None)
    
    def set_overlays(self, path: str, faces: list, manual_regions: list, w: int, h: int):
        """Update overlays for a specific thumbnail."""
        if path in self._items:
            self._items[path].set_overlays(faces, manual_regions, w, h)
            
    def update_thumbnail(self, path: str, thumbnail: np.ndarray):
        """Update an existing thumbnail's image."""
        if path in self._items:
            self._items[path].set_thumbnail(thumbnail)
    
    def set_manual_edit(self, path: str, has_edit: bool):
        """Update manual edit marker for a thumbnail."""
        if path in self._items:
            self._items[path].set_manual_edit(has_edit)
    
    def _relayout(self):
        """Reorganize grid layout."""
        # Clear layout
        while self.grid_layout.count():
            self.grid_layout.takeAt(0)
        
        # Re-add items in grid
        for i, (path, item) in enumerate(self._items.items()):
            row = i // self._columns
            col = i % self._columns
            self.grid_layout.addWidget(item, row, col)
    
    
    def select_all(self):
        """Check all items."""
        for path, item in self._items.items():
            if path not in self._checked_paths:
                item.set_checked(True)
                # _on_item_toggled will handle list update
        
    def deselect_all(self):
        """Uncheck all items."""
        for path in self._checked_paths[:]: # Copy list as it changes
            if path in self._items:
                self._items[path].set_checked(False)
        # _on_item_toggled will handle list update
        
    def toggle_select_all(self):
        """Toggle check all / uncheck all."""
        if len(self._checked_paths) == len(self._items) and len(self._items) > 0:
            self.deselect_all()
        else:
            self.select_all()
            
    def _on_item_clicked(self, path: str):
        """Handle thumbnail click (Active Selection)."""
        # Set as single active item (Red Border)
        if self._active_path and self._active_path != path:
             if self._active_path in self._items:
                 self._items[self._active_path].set_selected(False)
        
        self._active_path = path
        if path in self._items:
            self._items[path].set_selected(True)
        
        self.item_clicked.emit(path)
        self.active_changed.emit(path)
        
    def _on_item_toggled(self, path: str, checked: bool):
        """Handle thumbnail checkbox toggle."""
        if checked:
            if path not in self._checked_paths:
                self._checked_paths.append(path)
        else:
            if path in self._checked_paths:
                self._checked_paths.remove(path)
        
        self.selection_changed.emit(self._checked_paths)
    
    def _on_item_double_clicked(self, path: str):
        """Handle thumbnail double click."""
        self.item_double_clicked.emit(path)
    
    def resizeEvent(self, event):
        """Adjust columns on resize."""
        super().resizeEvent(event)
        
        available_width = self.viewport().width() - THUMBNAIL_GAP * 2
        new_columns = max(1, available_width // (THUMBNAIL_SIZE + THUMBNAIL_GAP))
        
        if new_columns != self._columns:
            self._columns = new_columns
            self._relayout()
    
    @property
    def checked_paths(self) -> List[str]:
        """Get list of checked thumbnail paths."""
        return self._checked_paths.copy()
        
    @property
    def selected_paths(self) -> List[str]:
        """DEPRECATED: Use checked_paths for batch, active_path for single."""
        # Keeping this for compatibility temporarily, but modifying MainWindow next
        return self._checked_paths.copy()
        
    @property
    def active_path(self) -> Optional[str]:
        """Get currently active (red border) path."""
        return self._active_path
    
    @property
    def item_count(self) -> int:
        """Get number of thumbnails."""
        return len(self._items)

    def update_style(self):
        """Update style based on current theme."""
        c = Styles.get_theme_colors()
        
        # Style the scroll area and container
        # Style the scroll area and container
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {c['COLOR_BASE']};
                border: none;
            }}
            #gridContainer {{
                background-color: {c['COLOR_BASE']};
            }}
        """)
        
        # Update styling for all items
        for item in self._items.values():
            item.update_style()
