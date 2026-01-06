import sys
print("--- DEBUG IMPORT ---")
try:
    import mediapipe as mp
    try:
        print("Attempting: import mediapipe.solutions")
        import mediapipe.solutions
        print(f"Success. mp.solutions is now: {getattr(mp, 'solutions', 'Still Missing')}")
    except ImportError as e:
        print(f"Import failed: {e}")

    try:
        from mediapipe.python import solutions
        print(f"Direct import from python.solutions success: {solutions}")
    except ImportError as e:
        print(f"Direct import failed: {e}")

except Exception as e:
    print(f"Outer error: {e}")
print("--- DEBUG END ---")
