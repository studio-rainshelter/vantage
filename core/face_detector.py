"""
VANTAGE Face Detector

MediaPipe-based face detection for automatic anonymization.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np

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
    MediaPipe-based face detection.
    
    Detects faces in images and returns bounding box regions
    for anonymization processing.
    """
    
    def __init__(self, min_confidence: float = FACE_DETECTION_CONFIDENCE):
        """
        Initialize the face detector.
        
        Args:
            min_confidence: Minimum detection confidence (0.0 - 1.0)
        """
        self._min_confidence = min_confidence
        self._detector = None
        self._initialized = False
    
    def _ensure_initialized(self) -> None:
        """Lazy initialization of MediaPipe detector."""
        if self._initialized:
            return
            
        try:
            import mediapipe as mp
            
            # Initialize MediaPipe Face Detection
            self._mp_face = mp.solutions.face_detection
            self._detector = self._mp_face.FaceDetection(
                model_selection=1,  # Full range model (better for various distances)
                min_detection_confidence=self._min_confidence
            )
            self._initialized = True
            print("[FaceDetector] MediaPipe initialized successfully")
            
        except ImportError as e:
            print(f"[FaceDetector] MediaPipe not available: {e}")
            raise RuntimeError("MediaPipe is required for face detection")
    
    def detect(self, image: np.ndarray) -> List[FaceRegion]:
        """
        Detect faces in an image.
        
        Args:
            image: Input image as numpy array (BGR or RGB)
            
        Returns:
            List of FaceRegion objects for detected faces
        """
        self._ensure_initialized()
        
        if image is None or image.size == 0:
            return []
        
        # Convert BGR to RGB if needed (MediaPipe expects RGB)
        if len(image.shape) == 3 and image.shape[2] == 3:
            import cv2
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image
        
        # Process with MediaPipe
        results = self._detector.process(rgb_image)
        
        faces: List[FaceRegion] = []
        
        if results.detections:
            h, w = image.shape[:2]
            
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                
                # Convert relative coordinates to absolute pixels
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                # Clamp to image bounds
                x = max(0, x)
                y = max(0, y)
                width = min(width, w - x)
                height = min(height, h - y)
                
                if width > 0 and height > 0:
                    faces.append(FaceRegion(
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        confidence=detection.score[0]
                    ))
        
        return faces
    
    def detect_batch(self, images: List[np.ndarray]) -> List[List[FaceRegion]]:
        """
        Detect faces in multiple images.
        
        Args:
            images: List of input images
            
        Returns:
            List of face region lists (one per image)
        """
        return [self.detect(img) for img in images]
    
    def set_confidence(self, confidence: float) -> None:
        """
        Update minimum detection confidence.
        
        Note: Requires re-initialization of detector.
        """
        self._min_confidence = max(0.0, min(1.0, confidence))
        self._initialized = False
        self._detector = None
    
    def release(self) -> None:
        """Release MediaPipe resources."""
        if self._detector is not None:
            self._detector.close()
            self._detector = None
            self._initialized = False
    
    def __del__(self):
        """Cleanup on destruction."""
        self.release()
