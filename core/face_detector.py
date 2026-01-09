"""
VANTAGE Face Detector

MediaPipe-based face detection (Tasks API) for automatic anonymization.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
import cv2
import os
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

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
    MediaPipe-based face detection using Tasks API.
    
    Uses BlazeFace (short range) model.
    """
    
    def __init__(self, min_confidence: float = FACE_DETECTION_CONFIDENCE):
        """
        Initialize the face detector.
        
        Args:
            min_confidence: Minimum confidence threshold (0.0 - 1.0)
        """
        self._min_confidence = min_confidence
        self._detector = None
        
        # Model path - robust resolution
        # Try relative to CWD first, then relative to this file
        cwd_path = "resources/blaze_face_short_range.tflite"
        if os.path.exists(cwd_path):
            self._model_path = os.path.abspath(cwd_path)
        else:
            # Fallback for when running from elsewhere (e.g. tests in different dir)
            # Assuming core/face_detector.py is 2 levels deep from root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(os.path.dirname(current_dir))
            self._model_path = os.path.join(root_dir, "resources", "blaze_face_short_range.tflite")
    
    def _ensure_initialized(self) -> None:
        """Lazy initialization of MediaPipe Detector."""
        if getattr(self, '_detector', None) is not None:
            return
            
        try:
            if not os.path.exists(self._model_path):
                raise FileNotFoundError(f"Model not found at: {self._model_path}")

            base_options = python.BaseOptions(model_asset_path=self._model_path)
            options = vision.FaceDetectorOptions(
                base_options=base_options,
                min_detection_confidence=self._min_confidence
            )
            self._detector = vision.FaceDetector.create_from_options(options)
            print("[FaceDetector] Initialized MediaPipe Tasks API successfully")
        except Exception as e:
            print(f"[FaceDetector] Init failed: {e}")
            raise
    
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
        """Run MediaPipe detection on a single image instance."""
        # MediaPipe requires RGB
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            
        # Create MP Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        # Detect
        detection_result = self._detector.detect(mp_image)
        
        if not detection_result.detections:
            return []
            
        regions: List[FaceRegion] = []
        
        for detection in detection_result.detections:
            bbox = detection.bounding_box
            score = detection.categories[0].score if detection.categories else 0.0
            
            # Tasks API returns absolute coordinates
            abs_x = bbox.origin_x
            abs_y = bbox.origin_y
            abs_w = bbox.width
            abs_h = bbox.height
            
            regions.append(FaceRegion(
                x=abs_x,
                y=abs_y,
                width=abs_w,
                height=abs_h,
                confidence=score
            ))
            
        return regions

    def _map_from_90(self, face: FaceRegion, orig_h: int, orig_w: int) -> FaceRegion:
        """Map coordinates from 90 deg CW rotated image back to original."""
        x1, y1 = face.x, face.y
        x2, y2 = face.x + face.width, face.y + face.height
        
        # New coordinates in original space
        # (x, y) in 90deg -> (y, h-1-x) in orig
        
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
        
        # New coordinates in original space
        # (x, y) in 270deg -> (w-1-y, x) in orig
        
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
        
        # New coordinates in original space
        # (x, y) in 180deg -> (w-1-x, h-1-y) in orig
        
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
        """Update detection confidence threshold."""
        self._min_confidence = confidence
        # Re-init detector with new confidence if needed
        if self._detector:
            self.release()
            self._ensure_initialized()
    
    def release(self) -> None:
        """Release MediaPipe resources."""
        detector = getattr(self, '_detector', None)
        if detector:
            detector.close()
            self._detector = None
    
    def __del__(self):
        self.release()

