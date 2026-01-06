import sys
import os

print("--- DEBUG START ---")
try:
    import mediapipe
    print(f"MediaPipe path: {mediapipe.__file__}")
    print(f"MediaPipe attributes: {dir(mediapipe)}")
    
    try:
        from mediapipe import solutions
        print("Successfully imported solutions from mediapipe")
    except ImportError as e:
        print(f"Failed to import solutions from mediapipe: {e}")

    if hasattr(mediapipe, 'solutions'):
        print("mediapipe.solutions exists")
    else:
        print("mediapipe.solutions DOES NOT exist")

except ImportError as e:
    print(f"Failed to import mediapipe: {e}")
print("--- DEBUG END ---")
