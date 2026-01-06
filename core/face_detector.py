"""
VANTAGE Face Detector

Pure OpenCV-based face detection for automatic anonymization.
"""

from typing import List, Tuple
from dataclasses import dataclass
import numpy as np
import cv2
import os

from config.constants import FACE_DETECTION_CONFIDENCE


@dataclass
class FaceRegion:
    """Detected face region with bounding box."""
    x: int          # Top-left X
    y: int          # Top-left Y
    width: int      # Width
    height: int     # Height
    confidence: float
    
    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Return (x, y, w, h) tuple."""
        return (self.x, self.y, self.width, self.height)
    
    @property
    def center(self) -> Tuple[int, int]:
        """Return center point."""
        return (self.x + self.width // 2, self.y + self.height // 2)


class FaceDetector:
    """
    OpenCV-based face detection.
    
    Uses multiple Haar Cascades (Frontal + Profile) with aggressive settings
    to maximize detection rate.
    """
    
    def __init__(self, min_confidence: float = FACE_DETECTION_CONFIDENCE):
        """
        Initialize the face detector.
        
        Args:
            min_confidence: Unused in Haar Cascade (kept for API compatibility)
        """
        self._haar_cascades = []
        self._initialized = False
    
    def _ensure_initialized(self) -> None:
        """Lazy initialization of OpenCV Haar Cascades."""
        if self._initialized:
            return
            
        self._haar_cascades = []
        
        # Cascades to try (Order matters: most specific to most general)
        cascade_names = [
            'haarcascade_frontalface_alt2.xml',  # Often best performance
            'haarcascade_frontalface_default.xml',
            'haarcascade_frontalface_alt.xml',
            'haarcascade_profileface.xml'
        ]
        
        for name in cascade_names:
            # Try system path first
            path = os.path.join(cv2.data.haarcascades, name)
            if not os.path.exists(path):
                # Fallback to local
                path = name
            
            try:
                cascade = cv2.CascadeClassifier(path)
                if not cascade.empty():
                    self._haar_cascades.append(cascade)
                    print(f"[FaceDetector] Loaded cascade: {name}")
            except Exception as e:
                print(f"[FaceDetector] Failed to load {name}: {e}")
        
        if not self._haar_cascades:
            print("[FaceDetector] WARNING: No Haar Cascades loaded. Detection will fail.")
            
        self._initialized = True
    
    def detect(self, image: np.ndarray) -> List[FaceRegion]:
        """
        Detect faces in an image using multi-orientation scan.
        
        Args:
            image: Input image as numpy array (BGR or RGB)
            
        Returns:
            List of FaceRegion objects for detected faces
        """
        self._ensure_initialized()
        
        if image is None or image.size == 0:
            return []
        
        # 1. Try original orientation
        faces = self._detect_single(image)
        
        # If faces found, we return them. 
        # OPTIONAL: You could continue to search rotations even if faces are found
        # to catch mixed-orientation faces, but usually not needed for normal photos.
        if faces:
            return faces
            
        # 2. Try rotations if no faces found
        h, w = image.shape[:2]
        
        # Try 90 degrees CW
        img_90 = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        faces_90 = self._detect_single(img_90)
        if faces_90:
            return [self._map_from_90(f, h, w) for f in faces_90]
            
        # Try 270 degrees CW (90 CCW)
        img_270 = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        faces_270 = self._detect_single(img_270)
        if faces_270:
            return [self._map_from_270(f, h, w) for f in faces_270]
            
        # Try 180 degrees
        img_180 = cv2.rotate(image, cv2.ROTATE_180)
        faces_180 = self._detect_single(img_180)
        if faces_180:
            return [self._map_from_180(f, h, w) for f in faces_180]
            
        return []

    def _detect_single(self, image: np.ndarray) -> List[FaceRegion]:
        """Run multi-cascade detection on a single image instance."""
        if not self._haar_cascades:
            return []
            
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Enhance contrast (Critical for Haar accuracy)
        gray = cv2.equalizeHist(gray)
            
        all_rects = []
        
        # Detect with all loaded cascades
        for cascade in self._haar_cascades:
            faces = cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,  # 1.05 = High granular search (slower but finds more)
                minNeighbors=3,    # 3 = High sensitivity (more false positives possible)
                minSize=(30, 30),  # Minimum face size
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            for (x, y, w, h) in faces:
                all_rects.append((x, y, w, h))
                
        # Simple deduplication (NMS-like) not implemented to maximize safety.
        # We process all detected regions.
        
        regions: List[FaceRegion] = []
        for (x, y, w, h) in all_rects:
            regions.append(FaceRegion(
                x=int(x),
                y=int(y),
                width=int(w),
                height=int(h),
                confidence=1.0  # Haar doesn't provide confidence
            ))
            
        return regions

    def _map_from_90(self, face: FaceRegion, orig_h: int, orig_w: int) -> FaceRegion:
        """Map coordinates from 90 deg CW rotated image back to original."""
        x1, y1 = face.x, face.y
        x2, y2 = face.x + face.width, face.y + face.height
        
        pts = [
            (y1, orig_h - 1 - x1),
            (y1, orig_h - 1 - x2),
            (y2, orig_h - 1 - x1),
            (y2, orig_h - 1 - x2)
        ]
        
        min_x = min(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        max_x = max(p[0] for p in pts)
        max_y = max(p[1] for p in pts)
        
        return FaceRegion(
            x=int(min_x),
            y=int(min_y),
            width=int(max_x - min_x),
            height=int(max_y - min_y),
            confidence=face.confidence
        )

    def _map_from_270(self, face: FaceRegion, orig_h: int, orig_w: int) -> FaceRegion:
        """Map coordinates from 270 deg CW (90 CCW) rotated image back to original."""
        x1, y1 = face.x, face.y
        x2, y2 = face.x + face.width, face.y + face.height
        
        pts = [
            (orig_w - 1 - y1, x1),
            (orig_w - 1 - y1, x2),
            (orig_w - 1 - y2, x1),
            (orig_w - 1 - y2, x2)
        ]
        
        min_x = min(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        max_x = max(p[0] for p in pts)
        max_y = max(p[1] for p in pts)
        
        return FaceRegion(
            x=int(min_x),
            y=int(min_y),
            width=int(max_x - min_x),
            height=int(max_y - min_y),
            confidence=face.confidence
        )
        
    def _map_from_180(self, face: FaceRegion, orig_h: int, orig_w: int) -> FaceRegion:
        """Map coordinates from 180 deg rotated image back to original."""
        x1, y1 = face.x, face.y
        x2, y2 = face.x + face.width, face.y + face.height
        
        pts = [
            (orig_w - 1 - x1, orig_h - 1 - y1),
            (orig_w - 1 - x1, orig_h - 1 - y2),
            (orig_w - 1 - x2, orig_h - 1 - y1),
            (orig_w - 1 - x2, orig_h - 1 - y2)
        ]
        
        min_x = min(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        max_x = max(p[0] for p in pts)
        max_y = max(p[1] for p in pts)
        
        return FaceRegion(
            x=int(min_x),
            y=int(min_y),
            width=int(max_x - min_x),
            height=int(max_y - min_y),
            confidence=face.confidence
        )

    def detect_batch(self, images: List[np.ndarray]) -> List[List[FaceRegion]]:
        """
        Detect faces in multiple images.
        """
        return [self.detect(img) for img in images]
    
    def set_confidence(self, confidence: float) -> None:
        """Unused in Haar Cascade (kept for API compatibility)."""
        pass
    
    def release(self) -> None:
        """No resources to release for Haar Cascade."""
        pass
    
    def __del__(self):
        self.release()
