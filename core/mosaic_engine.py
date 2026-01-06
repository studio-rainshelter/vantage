"""
VANTAGE Mosaic Engine

Applies mosaic and blur effects to specified image regions.
Supports Auto, Manual, Override, and Append modes.
"""

from typing import List, Tuple, Optional, Union
from enum import Enum
import numpy as np
import cv2

from config.constants import (
    MOSAIC_BLOCK_SIZE,
    BLUR_KERNEL_SIZE,
    MosaicMode
)
from .face_detector import FaceRegion


class EffectType(Enum):
    """Type of anonymization effect."""
    MOSAIC = "mosaic"
    BLUR = "blur"


class RegionShape(Enum):
    """Shape of manual region."""
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    FREEHAND = "freehand"


class ManualRegion:
    """User-defined region for manual anonymization."""
    
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        effect: EffectType = EffectType.MOSAIC,
        shape: RegionShape = RegionShape.RECTANGLE,
        points: Optional[List[Tuple[int, int]]] = None
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.effect = effect
        self.shape = shape
        self.points = points or []  # For freehand shape
    
    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'effect': self.effect.value,
            'shape': self.shape.value,
            'points': self.points
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ManualRegion':
        """Deserialize from dictionary."""
        return cls(
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height'],
            effect=EffectType(data.get('effect', 'mosaic')),
            shape=RegionShape(data.get('shape', 'rectangle')),
            points=data.get('points', [])
        )


class MosaicEngine:
    """
    Anonymization engine for applying mosaic and blur effects.
    
    Supports multiple modes:
    - AUTO: Use face detector results only
    - MANUAL: Use user-defined regions only
    - OVERRIDE: Manual regions override auto detection
    - APPEND: Combine auto detection and manual regions
    """
    
    def __init__(
        self,
        block_size: int = MOSAIC_BLOCK_SIZE,
        blur_kernel: int = BLUR_KERNEL_SIZE
    ):
        """
        Initialize the mosaic engine.
        
        Args:
            block_size: Size of mosaic blocks in pixels
            blur_kernel: Blur kernel size (must be odd)
        """
        self.block_size = block_size
        self.blur_kernel = blur_kernel if blur_kernel % 2 == 1 else blur_kernel + 1
    
    def apply_mosaic(
        self,
        image: np.ndarray,
        region: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        Apply mosaic effect to a region.
        
        Args:
            image: Input image (will be modified in place)
            region: (x, y, width, height) tuple
            
        Returns:
            Modified image
        """
        x, y, w, h = region
        
        # Clamp to image bounds
        x = max(0, x)
        y = max(0, y)
        w = min(w, image.shape[1] - x)
        h = min(h, image.shape[0] - y)
        
        if w <= 0 or h <= 0:
            return image
        
        # Extract region
        roi = image[y:y+h, x:x+w]
        
        # Downscale
        small_h = max(1, h // self.block_size)
        small_w = max(1, w // self.block_size)
        small = cv2.resize(roi, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
        
        # Upscale back (creates blocky effect)
        mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        
        # Apply to original image
        image[y:y+h, x:x+w] = mosaic
        
        return image
    
    def apply_blur(
        self,
        image: np.ndarray,
        region: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        Apply Gaussian blur to a region.
        
        Args:
            image: Input image (will be modified in place)
            region: (x, y, width, height) tuple
            
        Returns:
            Modified image
        """
        x, y, w, h = region
        
        # Clamp to image bounds
        x = max(0, x)
        y = max(0, y)
        w = min(w, image.shape[1] - x)
        h = min(h, image.shape[0] - y)
        
        if w <= 0 or h <= 0:
            return image
        
        # Extract and blur region
        roi = image[y:y+h, x:x+w]
        blurred = cv2.GaussianBlur(roi, (self.blur_kernel, self.blur_kernel), 0)
        
        # Apply to original image
        image[y:y+h, x:x+w] = blurred
        
        return image
    
    def process(
        self,
        image: np.ndarray,
        auto_regions: Optional[List[FaceRegion]] = None,
        manual_regions: Optional[List[ManualRegion]] = None,
        mode: str = MosaicMode.AUTO,
        effect: EffectType = EffectType.MOSAIC
    ) -> np.ndarray:
        """
        Process image with anonymization based on mode.
        
        Args:
            image: Input image
            auto_regions: Face regions from auto detection
            manual_regions: User-defined regions
            mode: Processing mode (AUTO, MANUAL, OVERRIDE, APPEND)
            effect: Default effect type for auto regions
            
        Returns:
            Processed image with anonymization applied
        """
        # Make a copy to avoid modifying original
        result = image.copy()
        
        regions_to_process: List[Tuple[Union[ManualRegion, Tuple[int, int, int, int]], EffectType]] = []
        
        # Determine which regions to process based on mode
        if mode == MosaicMode.AUTO:
            # Only auto-detected regions
            if auto_regions:
                for region in auto_regions:
                    regions_to_process.append((region.bbox, effect))
                    
        elif mode == MosaicMode.MANUAL:
            # Only manual regions
            if manual_regions:
                for region in manual_regions:
                    regions_to_process.append((region, region.effect))
                    
        elif mode == MosaicMode.OVERRIDE:
            # Manual regions only (overrides auto)
            if manual_regions:
                for region in manual_regions:
                    regions_to_process.append((region, region.effect))
            elif auto_regions:
                # Fall back to auto if no manual regions
                for region in auto_regions:
                    regions_to_process.append((region.bbox, effect))
                    
        elif mode == MosaicMode.APPEND:
            # Both auto and manual regions
            if auto_regions:
                for region in auto_regions:
                    regions_to_process.append((region.bbox, effect))
            if manual_regions:
                for region in manual_regions:
                    regions_to_process.append((region, region.effect))
        
        # Apply effects
        # Apply effects
        for item, fx in regions_to_process:
            if isinstance(item, ManualRegion):
                self._apply_shape_effect(result, item, fx)
            else:
                # Handle FaceRegion or raw bbox tuple
                bbox = item if isinstance(item, tuple) else item
                if fx == EffectType.MOSAIC:
                    self.apply_mosaic(result, bbox)
                else:
                    self.apply_blur(result, bbox)
        
        return result
    
    def _apply_shape_effect(
        self,
        image: np.ndarray,
        region: ManualRegion,
        effect: EffectType
    ):
        """Apply effect with specific shape masking."""
        x, y, w, h = region.bbox
        
        # Clamp to image bounds
        x = max(0, x)
        y = max(0, y)
        w = min(w, image.shape[1] - x)
        h = min(h, image.shape[0] - y)
        
        if w <= 0 or h <= 0:
            return

        # Extract ROI
        roi = image[y:y+h, x:x+w]
        
        # Create mask for the shape within ROI
        mask = np.zeros((h, w), dtype=np.uint8)
        
        if region.shape == RegionShape.ELLIPSE:
            center = (w // 2, h // 2)
            axes = (w // 2, h // 2)
            cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
            
        elif region.shape == RegionShape.FREEHAND and region.points:
            # Adjust points to be relative to ROI
            pts = np.array([(p[0] - x, p[1] - y) for p in region.points], dtype=np.int32)
            cv2.fillPoly(mask, [pts], 255)
            
        else:  # RECTANGLE
            mask.fill(255)
            
        # Apply effect to ROI
        if effect == EffectType.MOSAIC:
            # Downscale
            small_h = max(1, h // self.block_size)
            small_w = max(1, w // self.block_size)
            small = cv2.resize(roi, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
            processed_roi = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        else:
            # Blur
            processed_roi = cv2.GaussianBlur(roi, (self.blur_kernel, self.blur_kernel), 0)
            
        # Composite using mask
        # Copy processed pixels where mask is 255
        np.copyto(roi, processed_roi, where=(mask > 0)[:, :, None])
    
    def set_block_size(self, size: int) -> None:
        """Update mosaic block size."""
        self.block_size = max(2, size)
    
    def set_blur_kernel(self, size: int) -> None:
        """Update blur kernel size (will be made odd if even)."""
        self.blur_kernel = size if size % 2 == 1 else size + 1
