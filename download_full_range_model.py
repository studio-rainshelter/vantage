
import os
import urllib.request
import sys

CANDIDATE_URLS = [
    # UNPKG (Reliable mirror)
    "https://unpkg.com/@mediapipe/face_detection@0.4.1646425229/face_detection_full_range.tflite",
    "https://storage.googleapis.com/mediapipe-models/face_detector/face_detection_full_range/float16/1/face_detection_full_range.tflite",
]

DEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
DEST_PATH = os.path.join(DEST_DIR, "blaze_face_full_range.tflite")

def download_model():
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        
    if os.path.exists(DEST_PATH):
        print(f"Model already exists at: {DEST_PATH}")
        return

    print("Attempting to download full range model...")
    
    for url in CANDIDATE_URLS:
        print(f"Trying: {url}")
        try:
            urllib.request.urlretrieve(url, DEST_PATH)
            if os.path.getsize(DEST_PATH) > 1000: # Check if it's not a tiny error page
                print(f"Success! Model saved to: {DEST_PATH}")
                return
            else:
                print("Downloaded file was too small, probably an error page.")
        except Exception as e:
            print(f"Failed: {e}")
            
    print("Error: Could not download model from any candidate URL.")
    if os.path.exists(DEST_PATH):
        os.remove(DEST_PATH) # Cleanup partial/bad file
    sys.exit(1)

if __name__ == "__main__":
    download_model()
