"""
VANTAGE ROI Canvas

Interactive canvas for drawing manual regions (ROI).
"""

from typing import Optional, List, Tuple
from PySide6.QtWidgets import QLabel, QWidget
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import (
    QPainter, QPen, QColor, QPixmap, QImage, QMouseEvent, QPaintEvent
)
import numpy as np
import cv2

from config.constants import COLOR_ACCENT, COLOR_BORDER
from core.mosaic_engine import ManualRegion, EffectType, RegionShape


class ROICanvas(QLabel):
    """
    Interactive canvas for drawing and editing ROI regions.
    
    Features:
    - Draw rectangles by click-drag
    - Display existing regions
    - Select and delete regions
    - Ruler overlay (optional)
    """
    
    region_added = Signal(object)  # ManualRegion
    region_selected = Signal(int)  # index
    region_deleted = Signal(int)   # index
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._image: Optional[np.ndarray] = None
        self._pixmap: Optional[QPixmap] = None
        self._scale: float = 1.0
        self._offset: QPoint = QPoint(0, 0)
        
        # Regions
        self._regions: List[ManualRegion] = []
        self._faces: List['FaceRegion'] = []  # Added: Store detected faces
        self._selected_index: int = -1
        # Drawing state
        self._drawing = False
        self._draw_start: Optional[QPoint] = None
        self._draw_current: Optional[QPoint] = None
        self._freehand_points: List[QPoint] = []  # For freehand drawing
        
        # Panning state
        self._panning = False
        self._pan_start: Optional[QPoint] = None
        self._pan_start_offset: Optional[QPoint] = None
        
        # Settings
        self._show_ruler = True
        self._current_effect = EffectType.MOSAIC
        self._current_shape: Optional[RegionShape] = RegionShape.RECTANGLE  # None = Selection Mode
        
        # Style
        self._region_color = QColor(COLOR_ACCENT)
        self._region_color.setAlpha(128)
        self._border_color = QColor(COLOR_ACCENT)
        
        # Face Overlay Style (Blue)
        self._face_color = QColor(0, 120, 255, 60)  # Semi-transparent blue
        self._face_border = QColor(0, 120, 255, 180)
        
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        self.setMinimumSize(200, 200)
    
    def set_image(self, image: np.ndarray):
        """Set the image to display."""
        self._image = image
        self._update_pixmap()
    
    def set_faces(self, faces: List['FaceRegion']):
        """Set detected faces to display."""
        self._faces = faces
        self.update()

    def _update_pixmap(self):
        """Update the display pixmap."""
        if self._image is None:
            return
        
        h, w = self._image.shape[:2]
        
        # Convert BGR to RGB
        if len(self._image.shape) == 3:
            rgb = cv2.cvtColor(self._image, cv2.COLOR_BGR2RGB)
        else:
            rgb = cv2.cvtColor(self._image, cv2.COLOR_GRAY2RGB)
        
        # Create QImage
        qimg = QImage(
            rgb.data, w, h, w * 3,
            QImage.Format_RGB888
        )
        
        self._pixmap = QPixmap.fromImage(qimg)
        
        # Calculate scale to fit widget
        self._calculate_scale()
        self.update()
    
    def _calculate_scale(self):
        """Calculate scale factor to fit image in widget."""
        if self._pixmap is None:
            return
        
        widget_w = self.width()
        widget_h = self.height()
        pixmap_w = self._pixmap.width()
        pixmap_h = self._pixmap.height()
        
        scale_w = widget_w / pixmap_w
        scale_h = widget_h / pixmap_h
        self._scale = min(scale_w, scale_h)
        
        # Calculate offset to center image
        scaled_w = pixmap_w * self._scale
        scaled_h = pixmap_h * self._scale
        self._offset = QPoint(
            int((widget_w - scaled_w) / 2),
            int((widget_h - scaled_h) / 2)
        )
    
    def set_regions(self, regions: List[ManualRegion]):
        """Set the list of manual regions."""
        self._regions = regions.copy()
        self._selected_index = -1
        self.update()
    
    def add_region(self, region: ManualRegion):
        """Add a new region."""
        self._regions.append(region)
        self.region_added.emit(region)
        self.update()
    
    def remove_region(self, index: int):
        """Remove a region by index."""
        if 0 <= index < len(self._regions):
            self._regions.pop(index)
            self._selected_index = -1
            self.region_deleted.emit(index)
            self.update()
    
    def clear_regions(self):
        """Clear all regions."""
        self._regions.clear()
        self._selected_index = -1
        self.update()
    
    def set_current_effect(self, effect: EffectType):
        """Set effect type for new regions."""
        self._current_effect = effect
    
    def set_current_shape(self, shape: Optional[RegionShape]):
        """Set shape type for new regions. None means selection mode."""
        self._current_shape = shape
        
        # Update cursor based on mode
        if shape is None:
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.CrossCursor)
    
    def _widget_to_image(self, pos: QPoint) -> Tuple[int, int]:
        """Convert widget coordinates to image coordinates."""
        if self._pixmap is None:
            return (0, 0)
        
        x = int((pos.x() - self._offset.x()) / self._scale)
        y = int((pos.y() - self._offset.y()) / self._scale)
        
        # Clamp to image bounds
        x = max(0, min(x, self._pixmap.width() - 1))
        y = max(0, min(y, self._pixmap.height() - 1))
        
        return (x, y)
    
    def _image_to_widget(self, x: int, y: int) -> QPoint:
        """Convert image coordinates to widget coordinates."""
        wx = int(x * self._scale) + self._offset.x()
        wy = int(y * self._scale) + self._offset.y()
        return QPoint(wx, wy)
    
    def _get_region_at(self, pos: QPoint) -> int:
        """Get index of region at widget position, or -1."""
        img_x, img_y = self._widget_to_image(pos)
        
        for i, region in enumerate(self._regions):
            if (region.x <= img_x <= region.x + region.width and
                region.y <= img_y <= region.y + region.height):
                return i
        
        return -1
    
    # =========================================================================
    # EVENTS
    # =========================================================================
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            # Check for existing region - ONLY in selection mode
            index = -1
            if self._current_shape is None:  # Selection Mode
                index = self._get_region_at(event.pos())
            
            if index >= 0:
                # Select existing region (Selection Mode only)
                self._selected_index = index
                self.region_selected.emit(index)
                self.update()
            else:
                # Clicked empty space or in Drawing Mode
                if self._selected_index != -1 and self._current_shape is None:
                    # Deselect if clicked empty space in selection mode
                    self._selected_index = -1
                    self.region_selected.emit(-1)
                    self.update()
                
                if self._current_shape is not None:
                    # Drawing Mode: Start drawing
                    self._drawing = True
                    self._draw_start = event.pos()
                    self._draw_current = event.pos()
                    
                    # Clear freehand points for new drawing
                    if self._current_shape == RegionShape.FREEHAND:
                        self._freehand_points = [event.pos()]
                else:
                    # Selection Mode + Empty Space: Start Panning
                    self._panning = True
                    self._pan_start = event.pos()
                    self._pan_start_offset = QPoint(self._offset)
        
        elif event.button() == Qt.RightButton:
            # Delete selected region
            if self._selected_index >= 0:
                self.remove_region(self._selected_index)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move."""
        if self._drawing:
            self._draw_current = event.pos()
            
            # Collect points for freehand drawing
            if self._current_shape == RegionShape.FREEHAND:
                # Add point only if moved enough specific distance
                if not self._freehand_points:
                    self._freehand_points.append(event.pos())
                else:
                    last_pt = self._freehand_points[-1]
                    # Simple manhattan length check for performance
                    if (event.pos() - last_pt).manhattanLength() > 5:
                        self._freehand_points.append(event.pos())
            
            self.update()
            
        elif self._panning and self._pan_start:
            # Handle Panning
            delta = event.pos() - self._pan_start
            self._offset = self._pan_start_offset + delta
            self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release."""
        if event.button() == Qt.LeftButton:
            if self._drawing:
                self._drawing = False
                
                region = None
                
                if self._current_shape == RegionShape.FREEHAND and len(self._freehand_points) >= 3:
                    # Create freehand region from points
                    points = [self._widget_to_image(p) for p in self._freehand_points]
                    
                    # Calculate bounding box
                    xs = [p[0] for p in points]
                    ys = [p[1] for p in points]
                    x, y = min(xs), min(ys)
                    w, h = max(xs) - x, max(ys) - y
                    
                    if w >= 10 and h >= 10:
                        region = ManualRegion(
                            x=x, y=y, width=w, height=h,
                            effect=self._current_effect,
                            shape=RegionShape.FREEHAND,
                            points=points
                        )
                    
                    self._freehand_points = []
                    
                elif self._draw_start and self._draw_current:
                    # Create rectangle or ellipse region
                    start_x, start_y = self._widget_to_image(self._draw_start)
                    end_x, end_y = self._widget_to_image(self._draw_current)
                    
                    # Ensure positive dimensions
                    x = min(start_x, end_x)
                    y = min(start_y, end_y)
                    w = abs(end_x - start_x)
                    h = abs(end_y - start_y)
                    
                    # Minimum size check
                    if w >= 10 and h >= 10:
                        region = ManualRegion(
                            x=x, y=y, width=w, height=h,
                            effect=self._current_effect,
                            shape=self._current_shape
                        )
                
                if region:
                    self.add_region(region)
                
                self._draw_start = None
                self._draw_current = None
                self.update()
            
            elif self._panning:
                self._panning = False
                self._pan_start = None
                self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        """Handle mouse wheel for zoom."""
        # Zoom in/out
        delta = event.angleDelta().y()
        # Use position().toPoint() for PySide6/Qt6 compatibility
        center = event.position().toPoint()
        if delta > 0:
            self.zoom(1.1, center)
        else:
            self.zoom(1 / 1.1, center)
    
    def zoom(self, factor: float, center: Optional[QPoint] = None):
        """Zoom canvas."""
        if self._pixmap is None:
            return
            
        old_scale = self._scale
        new_scale = old_scale * factor
        
        # Limits
        new_scale = max(0.1, min(new_scale, 5.0))
        
        if new_scale != old_scale:
            if center is None:
                center = QPoint(self.width() // 2, self.height() // 2)
                
            # Adjust offset to keep center fixed
            # (center - offset) / old_scale = image_point
            # center - new_offset = image_point * new_scale
            # new_offset = center - (center - offset) * (new_scale / old_scale)
            
            self._offset = center - (center - self._offset) * (new_scale / old_scale)
            self._scale = new_scale
            self.update()
    
    def paintEvent(self, event: QPaintEvent):
        """Custom paint for image and regions."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw image
        if self._pixmap:
            scaled_pixmap = self._pixmap.scaled(
                int(self._pixmap.width() * self._scale),
                int(self._pixmap.height() * self._scale),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            painter.drawPixmap(self._offset, scaled_pixmap)
        
        # Draw detected faces (under manual regions)
        for face in self._faces:
            self._draw_face(painter, face)
        
        # Draw existing regions
        for i, region in enumerate(self._regions):
            self._draw_region(painter, region, i == self._selected_index)
        
        # Draw current drawing shape
        if self._drawing:
            pen = QPen(self._border_color, 2, Qt.DashLine)
            painter.setPen(pen)
            
            if self._current_shape == RegionShape.FREEHAND and len(self._freehand_points) >= 2:
                # Draw freehand path (no fill, open line)
                painter.setBrush(Qt.NoBrush)
                from PySide6.QtGui import QPolygon
                polygon = QPolygon(self._freehand_points)
                painter.drawPolyline(polygon)
            elif self._draw_start and self._draw_current:
                painter.setBrush(self._region_color)
                rect = QRect(self._draw_start, self._draw_current).normalized()
                if self._current_shape == RegionShape.ELLIPSE:
                    painter.drawEllipse(rect)
                else:  # RECTANGLE
                    painter.drawRect(rect)

        
        # Draw ruler if enabled
        if self._show_ruler and self._pixmap:
            self._draw_ruler(painter)
        
        painter.end()
    
    def _draw_face(self, painter: QPainter, face: 'FaceRegion'):
        """Draw a single detected face."""
        # Convert to widget coords
        top_left = self._image_to_widget(face.x, face.y)
        w = int(face.width * self._scale)
        h = int(face.height * self._scale)
        
        # Draw fill (Blue semi-transparent)
        painter.setBrush(self._face_color)
        
        # Draw border
        painter.setPen(QPen(self._face_border, 2))
        
        # Draw rectangle
        painter.drawRect(top_left.x(), top_left.y(), w, h)

    
    def _draw_region(self, painter: QPainter, region: ManualRegion, selected: bool):
        """Draw a single region."""
        # Convert to widget coords
        top_left = self._image_to_widget(region.x, region.y)
        w = int(region.width * self._scale)
        h = int(region.height * self._scale)
        
        # Draw fill
        color = QColor(COLOR_ACCENT)
        color.setAlpha(80 if not selected else 150)
        painter.setBrush(color)
        
        # Draw border
        pen_width = 3 if selected else 2
        painter.setPen(QPen(self._border_color, pen_width))
        
        # Draw based on shape
        if region.shape == RegionShape.ELLIPSE:
            painter.drawEllipse(top_left.x(), top_left.y(), w, h)
        elif region.shape == RegionShape.FREEHAND and region.points:
            # Draw freehand polygon
            from PySide6.QtGui import QPolygon
            widget_points = [self._image_to_widget(p[0], p[1]) for p in region.points]
            polygon = QPolygon(widget_points)
            painter.drawPolygon(polygon)
        else:  # RECTANGLE
            painter.drawRect(top_left.x(), top_left.y(), w, h)
        
        # Draw effect label
        label = "M" if region.effect == EffectType.MOSAIC else "B"
        painter.setPen(QPen(Qt.white))
        painter.drawText(top_left.x() + 5, top_left.y() + 15, label)
    
    def _draw_ruler(self, painter: QPainter):
        """Draw ruler overlay."""
        if self._pixmap is None:
            return
        
        painter.setPen(QPen(QColor(COLOR_BORDER), 1))
        
        # Draw tick marks at 100px intervals
        step = 100
        
        # Horizontal ruler
        for x in range(0, self._pixmap.width(), step):
            wx = int(x * self._scale) + self._offset.x()
            painter.drawLine(wx, self._offset.y() - 10, wx, self._offset.y())
            painter.drawText(wx + 2, self._offset.y() - 2, str(x))
        
        # Vertical ruler  
        for y in range(0, self._pixmap.height(), step):
            wy = int(y * self._scale) + self._offset.y()
            painter.drawLine(self._offset.x() - 10, wy, self._offset.x(), wy)
            painter.drawText(self._offset.x() - 30, wy + 4, str(y))
    
    def resizeEvent(self, event):
        """Handle resize."""
        super().resizeEvent(event)
        self._calculate_scale()
        self.update()
    
    @property
    def regions(self) -> List[ManualRegion]:
        """Get all regions."""
        return self._regions.copy()
    
    @property
    def selected_region(self) -> Optional[ManualRegion]:
        """Get currently selected region."""
        if 0 <= self._selected_index < len(self._regions):
            return self._regions[self._selected_index]
        return None
