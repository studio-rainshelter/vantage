import sys
import os
from PySide6.QtWidgets import QApplication
from ui.dialogs.settings_dialog import SettingsDialog

# Add current directory to path
sys.path.append(os.getcwd())

def test_dialog():
    app = QApplication(sys.argv)
    
    # Initialize settings if needed (mock or real)
    # Assuming Settings() handles its own initialization
    
    dialog = SettingsDialog()
    dialog.show()
    
    print("Settings dialog launched. Check if controls are visible.")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_dialog()
