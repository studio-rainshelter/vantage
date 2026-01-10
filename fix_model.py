import urllib.request
import os
import shutil

# Official OpenCV Geo YuNet model
# https://github.com/opencv/opencv_zoo/tree/master/models/face_detection_yunet
URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"

DEST_DIR = os.path.join(os.getcwd(), "resources")
DEST_FILE = os.path.join(DEST_DIR, "face_detection_yunet_2023mar.onnx")

def download_yunet():
    print(f"Downloading YuNet from {URL}...")
    try:
        temp_file = "temp_yunet.onnx"
        # Accessing raw content from GitHub
        urllib.request.urlretrieve(URL, temp_file)
        
        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 1000:
            print(f"Download successful. Size: {os.path.getsize(temp_file)} bytes")
            shutil.move(temp_file, DEST_FILE)
            print(f"Saved to {DEST_FILE}")
        else:
            print("Download failed or file too small.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    download_yunet()
