"""
VANTAGE Face Detector

MediaPipe-based face detection (Tasks API) for automatic anonymization.
"""

from typing import List, Tuple, Optional, Union
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
    
    Supports:
    - BlazeFace Short Range (default) and Full Range models.
    - CLAHE Preprocessing for difficult lighting.
    - Tiled detection for high-resolution images.
    """
    
    def __init__(self, min_confidence: float = FACE_DETECTION_CONFIDENCE, model_type: str = 'short'):
        """
        Initialize the face detector.
        
        Args:
            min_confidence: Minimum confidence threshold (0.0 - 1.0)
            model_type: 'short' for selfie/close-up (<2m), 'full' for longer range (<5m)
        """
        self._min_confidence = min_confidence
        self._model_type = model_type
        self._detector = None
        
        # Determine model filename
        if model_type == 'full':
            model_filename = "blaze_face_full_range.tflite"
        else:
            model_filename = "blaze_face_short_range.tflite"
            
        # Model path resolution
        # Try relative to CWD first, then relative to this file
        cwd_path = os.path.join("resources", model_filename)
        if os.path.exists(cwd_path):
            self._model_path = os.path.abspath(cwd_path)
        else:
            # Fallback for when running from elsewhere (e.g. tests in different dir)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(os.path.dirname(current_dir))
            self._model_path = os.path.join(root_dir, "resources", model_filename)
    
    def _ensure_initialized(self) -> None:
        """Lazy initialization of MediaPipe Detector."""
        if getattr(self, '_detector', None) is not None:
            return
            
        try:
            if not os.path.exists(self._model_path):
                # Fallback to short range if full range is missing but requested
                if self._model_type == 'full' and not os.path.exists(self._model_path):
                    print(f"[FaceDetector] Warning: {self._model_path} not found. Falling back to short range.")
                    self._model_type = 'short'
                    self.__init__(self._min_confidence, 'short') # Re-init with short
                    # Check again
                    if not os.path.exists(self._model_path):
                        raise FileNotFoundError(f"Model not found at: {self._model_path}")
                else:
                    raise FileNotFoundError(f"Model not found at: {self._model_path}")

            base_options = python.BaseOptions(model_asset_path=self._model_path)
            options = vision.FaceDetectorOptions(
                base_options=base_options,
                min_detection_confidence=self._min_confidence
            )
            self._detector = vision.FaceDetector.create_from_options(options)
            print(f"[FaceDetector] Initialized MediaPipe Tasks API ({self._model_type} range) successfully")
        except Exception as e:
            print(f"[FaceDetector] Init failed: {e}")
            raise
    
    def detect(self, image: np.ndarray, preprocess: bool = True, tile: bool = True) -> List[FaceRegion]:
        """
        Detect faces in an image with optional preprocessing and tiling.
        
        Args:
            image: Input image as numpy array (BGR or RGB)
            preprocess: Apply CLAHE preprocessing if True
            tile: Use tiling for large images if True
            
        Returns:
            List of FaceRegion objects for detected faces
        """
        self._ensure_initialized()
        
        if image is None or image.size == 0:
            return []
            
        # 1. Preprocessing (CLAHE)
        # We work on a copy to not modify original
        img_to_process = image.copy()
        if preprocess:
            img_to_process = self._apply_clahe(img_to_process)
            
        # 2. Gamma Correction (for dark images)
        if preprocess:
            img_to_process = self._apply_gamma(img_to_process, gamma=1.5)

        # 3. Tiled Detection for large images
        # Heuristic: if either dim > 1280, use tiles
        h, w = img_to_process.shape[:2]
        if tile and (w > 1280 or h > 1280):
            return self._detect_tiled(img_to_process)
            
        # 3. Standard Detection (with rotation support)
        return self._detect_rotated_scan(img_to_process)

    def _apply_clahe(self, image: np.ndarray) -> np.ndarray:
        """Apply CLAHE to improve contrast."""
        try:
            if len(image.shape) == 3:
                # Convert to LAB
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                
                # Apply CLAHE to L-channel
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                cl = clahe.apply(l)
                
                # Merge and convert back
                limg = cv2.merge((cl, a, b))
                return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
            else:
                # Grayscale
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                return clahe.apply(image)
        except Exception as e:
            print(f"[FaceDetector] CLAHE failed: {e}")
            return image

    def _apply_gamma(self, image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
        """Apply Gamma Correction."""
        if gamma == 1.0:
            return image
        try:
            invGamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** invGamma) * 255 for i in range(256)]).astype("uint8")
            return cv2.LUT(image, table)
        except Exception as e:
            print(f"[FaceDetector] Gamma correction failed: {e}")
            return image

    def _detect_tiled(self, image: np.ndarray, tile_size: int = 1024, overlap: float = 0.5) -> List[FaceRegion]:
        """Split image into overlapping tiles and detect faces."""
        h, w = image.shape[:2]
        stride = int(tile_size * (1 - overlap))
        
        all_faces = []
        
        # Grid generation
        for y in range(0, h, stride):
            for x in range(0, w, stride):
                # Calculate tile bounds
                y_end = min(y + tile_size, h)
                x_end = min(x + tile_size, w)
                
                # If tile is too small (e.g. edge), extending backwards
                if y_end - y < tile_size and y > 0:
                    y = max(0, y_end - tile_size)
                if x_end - x < tile_size and x > 0:
                    x = max(0, x_end - tile_size)
                
                tile = image[y:y_end, x:x_end]
                
                # Detect on tile (no recursive tiling, but allow rotation scan)
                tile_faces = self._detect_rotated_scan(tile)
                
                # Map back to global coordinates
                for f in tile_faces:
                    f.x += x
                    f.y += y
                    all_faces.append(f)
                    
        # Merge overlapping detections via NMS
        return self._nms(all_faces, iou_threshold=0.3)

    def _nms(self, faces: List[FaceRegion], iou_threshold: float) -> List[FaceRegion]:
        """Non-Maximum Suppression to remove duplicate detections."""
        if not faces:
            return []
            
        # Sort by confidence
        faces = sorted(faces, key=lambda f: f.confidence, reverse=True)
        keep = []
        
        while faces:
            current = faces.pop(0)
            keep.append(current)
            
            # Filter remaining
            faces = [f for f in faces if self._iou(current, f) < iou_threshold]
            
        return keep

    def _iou(self, a: FaceRegion, b: FaceRegion) -> float:
        """Calculate Intersection over Union."""
        # Intersection
        x1 = max(a.x, b.x)
        y1 = max(a.y, b.y)
        x2 = min(a.x + a.width, b.x + b.width)
        y2 = min(a.y + a.height, b.y + b.height)
        
        if x2 < x1 or y2 < y1:
            return 0.0
            
        intersection = (x2 - x1) * (y2 - y1)
        area_a = a.width * a.height
        area_b = b.width * b.height
        
        return intersection / float(area_a + area_b - intersection)

    def _detect_rotated_scan(self, image: np.ndarray) -> List[FaceRegion]:
        """
        Run detection with multi-orientation scan.
        """
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

