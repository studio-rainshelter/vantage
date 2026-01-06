"""
VANTAGE Image Data Model

Manages image state including detected faces and manual edits.
"""

from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
import json

from core.face_detector import FaceRegion
from core.mosaic_engine import ManualRegion, EffectType
from config.constants import MosaicMode


@dataclass
class ImageData:
    """
    Data model for a single image.
    
    Stores the image path, detected faces, manual regions,
    and processing state.
    """
    
    path: str
    width: int = 0
    height: int = 0
    
    # Detected faces (from auto detection)
    faces: List[FaceRegion] = field(default_factory=list)
    
    # Manual regions (user-defined)
    manual_regions: List[ManualRegion] = field(default_factory=list)
    
    # Processing state
    mode: str = MosaicMode.AUTO
    effect: EffectType = EffectType.MOSAIC
    is_processed: bool = False
    has_manual_edit: bool = False
    
    @property
    def filename(self) -> str:
        return Path(self.path).name
    
    @property
    def face_count(self) -> int:
        return len(self.faces)
    
    @property
    def manual_region_count(self) -> int:
        return len(self.manual_regions)
    
    def add_manual_region(self, region: ManualRegion):
        """Add a manual region."""
        self.manual_regions.append(region)
        self.has_manual_edit = True
    
    def remove_manual_region(self, index: int):
        """Remove a manual region by index."""
        if 0 <= index < len(self.manual_regions):
            self.manual_regions.pop(index)
            self.has_manual_edit = len(self.manual_regions) > 0
    
    def clear_manual_regions(self):
        """Clear all manual regions."""
        self.manual_regions.clear()
        self.has_manual_edit = False
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            'path': self.path,
            'width': self.width,
            'height': self.height,
            'mode': self.mode,
            'effect': self.effect.value,
            'has_manual_edit': self.has_manual_edit,
            'manual_regions': [r.to_dict() for r in self.manual_regions]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ImageData':
        """Deserialize from dictionary."""
        img = cls(
            path=data['path'],
            width=data.get('width', 0),
            height=data.get('height', 0),
            mode=data.get('mode', MosaicMode.AUTO),
            effect=EffectType(data.get('effect', 'mosaic')),
            has_manual_edit=data.get('has_manual_edit', False)
        )
        
        # Load manual regions
        for region_data in data.get('manual_regions', []):
            img.manual_regions.append(ManualRegion.from_dict(region_data))
        
        return img


class ImageDataManager:
    """
    Manages collection of ImageData objects.
    
    Provides operations for batch processing and state management.
    """
    
    def __init__(self):
        self._images: Dict[str, ImageData] = {}
    
    def add(self, path: str, width: int = 0, height: int = 0) -> ImageData:
        """Add a new image to the collection."""
        if path not in self._images:
            self._images[path] = ImageData(path=path, width=width, height=height)
        return self._images[path]
    
    def get(self, path: str) -> Optional[ImageData]:
        """Get image data by path."""
        return self._images.get(path)
    
    def remove(self, path: str) -> bool:
        """Remove an image from the collection."""
        if path in self._images:
            del self._images[path]
            return True
        return False
    
    def clear(self):
        """Clear all images."""
        self._images.clear()
    
    def set_faces(self, path: str, faces: List[FaceRegion]):
        """Set detected faces for an image."""
        if path in self._images:
            self._images[path].faces = faces
    
    def get_all_paths(self) -> List[str]:
        """Get all image paths."""
        return list(self._images.keys())
    
    def get_images_with_faces(self) -> List[ImageData]:
        """Get all images that have detected faces."""
        return [img for img in self._images.values() if img.face_count > 0]
    
    def get_images_with_edits(self) -> List[ImageData]:
        """Get all images that have manual edits."""
        return [img for img in self._images.values() if img.has_manual_edit]
    
    def get_processing_data(self) -> List[dict]:
        """Get data formatted for ProcessingWorker."""
        return [
            {
                'path': img.path,
                'faces': img.faces,
                'manual_regions': img.manual_regions,
                'mode': img.mode
            }
            for img in self._images.values()
        ]
    
    @property
    def count(self) -> int:
        """Total number of images."""
        return len(self._images)
    
    @property
    def total_faces(self) -> int:
        """Total number of detected faces across all images."""
        return sum(img.face_count for img in self._images.values())
    
    def save_session(self, filepath: Path):
        """Save current session data to JSON."""
        data = {
            'images': [img.to_dict() for img in self._images.values()]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_session(self, filepath: Path) -> bool:
        """Load session data from JSON."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._images.clear()
            
            for img_data in data.get('images', []):
                img = ImageData.from_dict(img_data)
                self._images[img.path] = img
            
            return True
            
        except Exception as e:
            print(f"[ImageDataManager] Failed to load session: {e}")
            return False
