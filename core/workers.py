"""
VANTAGE Async Workers

QThread-based workers for background processing.
"""

from typing import List, Optional, Callable
from pathlib import Path
from PySide6.QtCore import QThread, Signal, QObject
import numpy as np

from core.image_processor import ImageProcessor
from core.face_detector import FaceDetector, FaceRegion
from core.mosaic_engine import MosaicEngine, EffectType
from config.constants import MosaicMode


class ImageLoaderWorker(QThread):
    """
    Background worker for loading and generating thumbnails.
    
    Signals:
        thumbnail_ready: Emits (path, thumbnail) when a thumbnail is generated
        progress: Emits (current, total) for progress tracking
        finished: Emits when all images are processed
        error: Emits (path, error_message) on failure
    """
    
    thumbnail_ready = Signal(str, np.ndarray)
    progress = Signal(int, int)
    finished = Signal()
    error = Signal(str, str)
    
    def __init__(self, paths: List[Path], parent: Optional[QObject] = None):
        super().__init__(parent)
        
        self._paths = paths
        self._processor = ImageProcessor()
        self._cancelled = False
    
    def run(self):
        """Process all images in background."""
        total = len(self._paths)
        
        for i, path in enumerate(self._paths):
            if self._cancelled:
                break
            
            try:
                thumbnail = self._processor.load_thumbnail(path)
                
                if thumbnail is not None:
                    self.thumbnail_ready.emit(str(path), thumbnail)
                else:
                    self.error.emit(str(path), "Failed to load image")
                    
            except Exception as e:
                self.error.emit(str(path), str(e))
            
            self.progress.emit(i + 1, total)
        
        self.finished.emit()
    
    def cancel(self):
        """Request cancellation."""
        self._cancelled = True


class FaceDetectionWorker(QThread):
    """
    Background worker for face detection.
    
    Signals:
        detection_complete: Emits (path, faces) when detection finishes
        progress: Emits (current, total) for progress tracking
        finished: Emits when all images are processed
        error: Emits (path, error_message) on failure
    """
    
    detection_complete = Signal(str, list, tuple)  # path, List[FaceRegion], (width, height)
    progress = Signal(int, int)
    finished = Signal()
    error = Signal(str, str)
    
    def __init__(
        self,
        image_paths: List[str],
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        
        from config import Settings
        settings = Settings()
        
        self._paths = image_paths
        self._detector = FaceDetector(
            min_neighbors=settings.get('face_min_neighbors', 6),
            scale_factor=settings.get('face_scale_factor', 1.1),
            iou_threshold=settings.get('face_iou_threshold', 0.3)
        )
        self._processor = ImageProcessor()
        self._cancelled = False
    
    def run(self):
        """Detect faces in all images."""
        total = len(self._paths)
        
        for i, path in enumerate(self._paths):
            if self._cancelled:
                break
            
            try:
                # Load image
                image = self._processor.load_image(path)
                
                if image is not None:
                    # Detect faces
                    faces = self._detector.detect(image)
                    h, w = image.shape[:2]
                    self.detection_complete.emit(path, faces, (w, h))
                else:
                    self.error.emit(path, "Failed to load image")
                    
            except Exception as e:
                self.error.emit(path, str(e))
            
            self.progress.emit(i + 1, total)
        
        self._detector.release()
        self.finished.emit()
    
    def cancel(self):
        """Request cancellation."""
        self._cancelled = True


class ProcessingWorker(QThread):
    """
    Background worker for applying mosaic/blur effects.
    
    Signals:
        image_processed: Emits (path, processed_image) when done
        progress: Emits (current, total) for progress tracking
        finished: Emits when all images are processed
        error: Emits (path, error_message) on failure
    """
    
    image_processed = Signal(str, np.ndarray)
    progress = Signal(int, int)
    finished = Signal()
    error = Signal(str, str)
    
    def __init__(
        self,
        image_data: List[dict],  # [{path, faces, manual_regions, mode}]
        effect: EffectType = EffectType.MOSAIC,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        
        self._image_data = image_data
        self._effect = effect
        self._processor = ImageProcessor()
        self._engine = MosaicEngine()
        self._cancelled = False
    
    def run(self):
        """Apply mosaic/blur to all images."""
        total = len(self._image_data)
        
        for i, data in enumerate(self._image_data):
            if self._cancelled:
                break
            
            path = data['path']
            
            try:
                # Load image
                image = self._processor.load_image(path)
                
                if image is not None:
                    # Apply effect
                    processed = self._engine.process(
                        image=image,
                        auto_regions=data.get('faces'),
                        manual_regions=data.get('manual_regions'),
                        mode=data.get('mode', MosaicMode.AUTO),
                        effect=self._effect
                    )
                    
                    self.image_processed.emit(path, processed)
                else:
                    self.error.emit(path, "Failed to load image")
                    
            except Exception as e:
                self.error.emit(path, str(e))
            
            self.progress.emit(i + 1, total)
        
        self.finished.emit()
    
    def cancel(self):
        """Request cancellation."""
        self._cancelled = True


class ExportWorker(QThread):
    """
    Background worker for exporting processed images.
    
    Signals:
        export_complete: Emits (original_path, export_path) when saved
        progress: Emits (current, total) for progress tracking
        finished: Emits when all images are exported
        error: Emits (path, error_message) on failure
    """
    
    export_complete = Signal(str, str)
    progress = Signal(int, int)
    finished = Signal()
    error = Signal(str, str)
    
    def __init__(
        self,
        export_data: List[dict],  # [{path, image, output_path}]
        quality: int = 95,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        
        self._export_data = export_data
        self._quality = quality
        self._processor = ImageProcessor()
        self._cancelled = False
    
    def run(self):
        """Export all processed images."""
        total = len(self._export_data)
        
        for i, data in enumerate(self._export_data):
            if self._cancelled:
                break
            
            path = data['path']
            image = data['image']
            output_path = data['output_path']
            
            try:
                success = self._processor.save_image(
                    image,
                    output_path,
                    self._quality
                )
                
                if success:
                    self.export_complete.emit(path, str(output_path))
                else:
                    self.error.emit(path, "Failed to save image")
                    
            except Exception as e:
                self.error.emit(path, str(e))
            
            self.progress.emit(i + 1, total)
        
        self.finished.emit()
    
    def cancel(self):
        """Request cancellation."""
        self._cancelled = True
