import sys
import importlib.util

print(f"Python version: {sys.version}")
print(f"Executable: {sys.executable}")

try:
    import mediapipe as mp
    print(f"MediaPipe imported. File: {mp.__file__}")
    print(f"Dir(mp): {dir(mp)}")
    
    try:
        print(f"mp.solutions: {mp.solutions}")
        print("mp.solutions accessed successfully.")
    except AttributeError as e:
        print(f"Error accessing mp.solutions: {e}")

    try:
        from mediapipe.python import solutions
        print("Imported solutions directly from mediapipe.python")
    except ImportError as e:
        print(f"Error importing mediapipe.python.solutions: {e}")

except ImportError as e:
    print(f"Failed to import mediapipe: {e}")
