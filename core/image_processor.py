"""
VANTAGE Image Processor

Image I/O, transformation, and thumbnail generation utilities.
"""

from pathlib import Path
from typing import List, Tuple, Optional, Union
import numpy as np
import cv2
from concurrent.futures import ThreadPoolExecutor
import threading

from config.constants import THUMBNAIL_SIZE, IMAGE_LOAD_BATCH


# Supported image formats
SUPPORTED_FORMATS = {
    '.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif'
}


class ImageProcessor:
    """
    Image processing utilities for VANTAGE.
    
    Handles image loading, saving, thumbnail generation,
    and format conversions.
    """
    
    def __init__(self, thumbnail_size: int = THUMBNAIL_SIZE):
        """
        Initialize the image processor.
        
        Args:
            thumbnail_size: Target size for thumbnail generation
        """
        self.thumbnail_size = thumbnail_size
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.Lock()
    
    @staticmethod
    def is_supported(path: Union[str, Path]) -> bool:
        """Check if file format is supported."""
        return Path(path).suffix.lower() in SUPPORTED_FORMATS
    
    def load_image(self, path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        Load an image from disk.
        
        Args:
            path: Path to image file
            
        Returns:
            Image as numpy array (BGR format) or None if failed
        """
        try:
            path = Path(path)
            if not path.exists():
                print(f"[ImageProcessor] File not found: {path}")
                return None
            
            # Use numpy to read file bytes for Unicode path support on Windows
            # cv2.imread() doesn't handle non-ASCII paths properly on Windows
            file_bytes = np.fromfile(str(path), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            if image is None:
                print(f"[ImageProcessor] Failed to decode: {path}")
                return None
            
            return image
            
        except Exception as e:
            print(f"[ImageProcessor] Error loading {path}: {e}")
            return None
    
    def save_image(
        self,
        image: np.ndarray,
        path: Union[str, Path],
        quality: int = 95
    ) -> bool:
        """
        Save an image to disk.
        
        Args:
            image: Image as numpy array (BGR format)
            path: Output path
            quality: JPEG quality (1-100)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Set compression parameters based on format
            ext = path.suffix.lower()
            params = []
            
            if ext in ['.jpg', '.jpeg']:
                params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            elif ext == '.png':
                params = [cv2.IMWRITE_PNG_COMPRESSION, 6]
            elif ext == '.webp':
                params = [cv2.IMWRITE_WEBP_QUALITY, quality]
            
            # Use imencode + tofile for Unicode path support on Windows
            # cv2.imwrite() doesn't handle non-ASCII paths properly
            success, encoded = cv2.imencode(ext, image, params)
            
            if success:
                encoded.tofile(str(path))
                return True
            else:
                print(f"[ImageProcessor] Failed to encode: {path}")
                return False
            
        except Exception as e:
            print(f"[ImageProcessor] Error saving to {path}: {e}")
            return False
    
    def generate_thumbnail(
        self,
        image: np.ndarray,
        size: Optional[int] = None
    ) -> np.ndarray:
        """
        Generate a square thumbnail from an image.
        
        Maintains aspect ratio by fitting within square bounds.
        
        Args:
            image: Source image
            size: Target size (uses default if None)
            
        Returns:
            Thumbnail image
        """
        size = size or self.thumbnail_size
        h, w = image.shape[:2]
        
        # Calculate scale to fit within square
        scale = size / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize with high quality interpolation
        thumbnail = cv2.resize(
            image,
            (new_w, new_h),
            interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
        )
        
        return thumbnail
    
    def load_thumbnail(
        self,
        path: Union[str, Path],
        size: Optional[int] = None
    ) -> Optional[np.ndarray]:
        """
        Load an image and generate thumbnail in one operation.
        
        Args:
            path: Path to image file
            size: Target thumbnail size
            
        Returns:
            Thumbnail image or None if failed
        """
        image = self.load_image(path)
        if image is None:
            return None
        
        return self.generate_thumbnail(image, size)
    
    def scan_directory(
        self,
        directory: Union[str, Path],
        recursive: bool = False
    ) -> List[Path]:
        """
        Scan directory for supported image files.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of image file paths
        """
        directory = Path(directory)
        if not directory.is_dir():
            return []
        
        images = []
        pattern = '**/*' if recursive else '*'
        
        for path in directory.glob(pattern):
            if path.is_file() and self.is_supported(path):
                images.append(path)
        
        return sorted(images)
    
    def get_image_info(self, path: Union[str, Path]) -> Optional[dict]:
        """
        Get image metadata without loading full image.
        
        Args:
            path: Path to image file
            
        Returns:
            Dictionary with width, height, format, size_bytes
        """
        try:
            path = Path(path)
            if not path.exists():
                return None
            
            # Load with Unicode path support
            file_bytes = np.fromfile(str(path), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if image is None:
                return None
            
            h, w = image.shape[:2]
            channels = image.shape[2] if len(image.shape) > 2 else 1
            
            return {
                'width': w,
                'height': h,
                'channels': channels,
                'format': path.suffix.lower(),
                'size_bytes': path.stat().st_size,
                'path': str(path)
            }
            
        except Exception as e:
            print(f"[ImageProcessor] Error getting info for {path}: {e}")
            return None
    
    @staticmethod
    def bgr_to_rgb(image: np.ndarray) -> np.ndarray:
        """Convert BGR to RGB."""
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    @staticmethod
    def rgb_to_bgr(image: np.ndarray) -> np.ndarray:
        """Convert RGB to BGR."""
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    def shutdown(self) -> None:
        """Shutdown the thread pool."""
        self._executor.shutdown(wait=True)
