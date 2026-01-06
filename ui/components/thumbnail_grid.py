"""
VANTAGE Thumbnail Grid

Virtualized grid view for displaying image thumbnails.
"""

from typing import List, Optional, Callable
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QFrame, QLabel,
    QVBoxLayout, QSizePolicy
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
        self.marker_label.setParent(self)
        self.marker_label.move(THUMBNAIL_SIZE - 28, 4)
    
    def set_thumbnail(self, thumbnail: np.ndarray):
        """Set the thumbnail image from numpy array."""
        if thumbnail is None:
            return
        
        h, w = thumbnail.shape[:2]
        channels = thumbnail.shape[2] if len(thumbnail.shape) > 2 else 1
        
        if channels == 3:
            # Convert BGR to RGB for Qt
            import cv2
            rgb = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
            image = QImage(
                rgb.data, w, h, w * 3,
                QImage.Format_RGB888
            )
        elif channels == 4:
            image = QImage(
                thumbnail.data, w, h, w * 4,
                QImage.Format_RGBA8888
            )
        else:
            image = QImage(
                thumbnail.data, w, h, w,
                QImage.Format_Grayscale8
            )
        
        pixmap = QPixmap.fromImage(image)
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
    selection_changed = Signal(list)  # List of selected paths
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._items: dict[str, ThumbnailItem] = {}
        self._selected_paths: List[str] = []
        self._columns = 4
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialize the grid layout."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container widget
        self.container = QWidget()
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
        
        self._items[path] = item
        self._relayout()
        
        return item
    
    def remove_thumbnail(self, path: str):
        """Remove a thumbnail from the grid."""
        if path in self._items:
            item = self._items.pop(path)
            item.deleteLater()
            self._relayout()
    
    def clear(self):
        """Remove all thumbnails."""
        for item in self._items.values():
            item.deleteLater()
        self._items.clear()
        self._selected_paths.clear()
    
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
    
    def _on_item_clicked(self, path: str):
        """Handle thumbnail click."""
        # Clear previous selection
        for p in self._selected_paths:
            if p in self._items:
                self._items[p].set_selected(False)
        
        # Set new selection
        self._selected_paths = [path]
        if path in self._items:
            self._items[path].set_selected(True)
        
        self.item_clicked.emit(path)
        self.selection_changed.emit(self._selected_paths)
    
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
    def selected_paths(self) -> List[str]:
        """Get list of selected thumbnail paths."""
        return self._selected_paths.copy()
    
    @property
    def item_count(self) -> int:
        """Get number of thumbnails."""
        return len(self._items)
