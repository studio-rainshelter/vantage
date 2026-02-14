import sys
import os
import cv2
import numpy as np

# Add current directory to path
sys.path.append(os.getcwd())

from core.mosaic_engine import MosaicEngine

def test_high_intensity():
    print("Testing high intensity mosaic and blur limits...")
    
    # Create a dummy image (black background with a white square)
    width, height = 500, 500
    img = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.rectangle(img, (100, 100), (400, 400), (255, 255, 255), -1)
    
    engine = MosaicEngine()
    
    # --- Test Mosaic ---
    max_mosaic_size = 200
    print(f"Testing Mosaic with block_size={max_mosaic_size}...")
    engine.set_block_size(max_mosaic_size)
    
    mosaic_img = img.copy()
    # Region to apply: 300x300
    region = (100, 100, 300, 300)
    
    try:
        engine.apply_mosaic(mosaic_img, region)
        print("Mosaic applied successfully.")
    except Exception as e:
        print(f"FAILED: Mosaic application failed with error: {e}")
        exit(1)

    # --- Test Blur ---
    max_blur_size = 301
    print(f"Testing Blur with kernel_size={max_blur_size}...")
    engine.set_blur_kernel(max_blur_size)
    
    blur_img = img.copy()
    
    try:
        engine.apply_blur(blur_img, region)
        print("Blur applied successfully.")
    except Exception as e:
        print(f"FAILED: Blur application failed with error: {e}")
        exit(1)
        
    print("Verification Passed: Engine handles high intensity values.")

if __name__ == "__main__":
    test_high_intensity()
