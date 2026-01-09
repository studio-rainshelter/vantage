
import sys
import os
import cv2
import numpy as np
from core.face_detector import FaceDetector, FaceRegion

def test_initialization():
    print("Testing FaceDetector initialization...")
    try:
        detector = FaceDetector(min_confidence=0.5)
        detector._ensure_initialized()
        print("PASS: FaceDetector initialized successfully.")
    except Exception as e:
        print(f"FAIL: FaceDetector initialization failed: {e}")
        return False
    return True

def test_detection_empty_image():
    print("Testing detection on empty image...")
    detector = FaceDetector()
    try:
        faces = detector.detect(np.zeros((100, 100, 3), dtype=np.uint8))
        if faces == []:
            print("PASS: Correctly returned empty list for empty image.")
        else:
            print(f"FAIL: Returned {faces} for empty image.")
            return False
    except Exception as e:
        print(f"FAIL: Detection raised exception: {e}")
        return False
    return True

def test_detection_dummy_image():
    print("Testing detection on valid image structure...")
    detector = FaceDetector()
    # Create a blank image 512x512
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    
    # We don't expect to find a face in a black square, but we check if it runs
    try:
        faces = detector.detect(img)
        print(f"PASS: Detection ran successfully (Faces found: {len(faces)}).")
    except Exception as e:
        print(f"FAIL: Detection raised exception: {e}")
        return False
    return True

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    
    steps = [
        test_initialization,
        test_detection_empty_image,
        test_detection_dummy_image
    ]
    
    failed = False
    for step in steps:
        if not step():
            failed = True
            break
    
    if failed:
        print("\nTESTS FAILED")
        sys.exit(1)
    else:
        print("\nALL TESTS PASSED")
        sys.exit(0)
