"""
VANTAGE Core Module

Contains the core business logic for image processing and anonymization.
"""

from .cache import ThumbnailCache
from .face_detector import FaceDetector, FaceRegion
from .mosaic_engine import MosaicEngine, ManualRegion, EffectType, RegionShape
from .image_processor import ImageProcessor
from .data_model import ImageData, ImageDataManager
from .workers import (
    ImageLoaderWorker,
    FaceDetectionWorker,
    ProcessingWorker,
    ExportWorker
)

__all__ = [
    'ThumbnailCache',
    'FaceDetector',
    'FaceRegion',
    'MosaicEngine',
    'ManualRegion',
    'EffectType',
    'RegionShape',
    'ImageProcessor',
    'ImageData',
    'ImageDataManager',
    'ImageLoaderWorker',
    'FaceDetectionWorker',
    'ProcessingWorker',
    'ExportWorker',
]
