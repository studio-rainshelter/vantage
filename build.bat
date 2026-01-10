@echo off
setlocal

echo [VANTAGE] Build Process Started...

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [VANTAGE] PyInstaller not found. Installing...
    pip install pyinstaller
) else (
    echo [VANTAGE] PyInstaller is already installed.
)

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /f /q "*.spec"

echo [VANTAGE] Creating executable...

REM Run PyInstaller
REM --noconfirm: Replace output directory without asking
REM --onefile: Create a single executable file
REM --windowed: Do not provide a console window for standard i/o
REM --icon: Icon file to use
REM --add-data: Additional data files or directories containing data
REM --name: Name to assign to the bundled app and spec file
REM --hidden-import: Explicitly list imports that PyInstaller might miss (often needed for PySide6/OpenCV plugins)

pyinstaller --noconfirm --onefile --windowed ^
    --name "VANTAGE" ^
    --icon "resources/icons/app.ico" ^
    --add-data "i18n;i18n" ^
    --add-data "resources;resources" ^
    --collect-all "mediapipe" ^
    --hidden-import "cv2" ^
    --hidden-import "PIL" ^
    --hidden-import "PySide6" ^
    main.py

if %errorlevel% equ 0 (
    echo [VANTAGE] Build successful!
    echo [VANTAGE] Executable located at: dist\VANTAGE.exe
) else (
    echo [VANTAGE] Build failed.
)

pause
