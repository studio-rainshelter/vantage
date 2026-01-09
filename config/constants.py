"""
VANTAGE Constants

Industrial Brutalism Design System - Visual Specification
"""

# =============================================================================
# APPLICATION INFO
# =============================================================================
APP_NAME = "VANTAGE"
APP_VERSION = "0.1.0"
APP_FULL_NAME = "Visual Anonymization & Tactical Graphics Editor"

# =============================================================================
# COLOR PALETTE - Industrial Brutalism
# =============================================================================
COLOR_BASE = "#0F0F0F"          # Deep Black - Primary background
COLOR_BASE_LIGHT = "#1A1A1A"    # Slightly lighter for panels
COLOR_ACCENT = "#FF3E00"        # Safety Orange - Warnings, selections
COLOR_ACCENT_HOVER = "#FF5722"  # Lighter orange for hover states
COLOR_BORDER = "#2A2A2A"        # Hard Grey - 1px sharp borders
COLOR_BORDER_FOCUS = "#3A3A3A"  # Focused border
COLOR_TEXT = "#E0E0E0"          # Primary text
COLOR_TEXT_DIM = "#808080"      # Secondary/disabled text
COLOR_TEXT_ACCENT = "#FFFFFF"   # High contrast text
COLOR_SUCCESS = "#00C853"       # Success states
COLOR_WARNING = "#FFB300"       # Warning states
COLOR_ERROR = "#FF1744"         # Error states

# Light Theme Palette
LIGHT_THEME = {
    "COLOR_BASE": "#F0F0F0",
    "COLOR_BASE_LIGHT": "#FFFFFF",
    "COLOR_ACCENT": "#FF3E00",
    "COLOR_ACCENT_HOVER": "#FF5722",
    "COLOR_BORDER": "#D0D0D0",
    "COLOR_BORDER_FOCUS": "#A0A0A0",
    "COLOR_TEXT": "#202020",
    "COLOR_TEXT_DIM": "#606060",
    "COLOR_TEXT_ACCENT": "#000000",
    "COLOR_SUCCESS": "#00C853",
    "COLOR_WARNING": "#EDA200",
    "COLOR_ERROR": "#D50000",
}

DARK_THEME = {
    "COLOR_BASE": COLOR_BASE,
    "COLOR_BASE_LIGHT": COLOR_BASE_LIGHT,
    "COLOR_ACCENT": COLOR_ACCENT,
    "COLOR_ACCENT_HOVER": COLOR_ACCENT_HOVER,
    "COLOR_BORDER": COLOR_BORDER,
    "COLOR_BORDER_FOCUS": COLOR_BORDER_FOCUS,
    "COLOR_TEXT": COLOR_TEXT,
    "COLOR_TEXT_DIM": COLOR_TEXT_DIM,
    "COLOR_TEXT_ACCENT": COLOR_TEXT_ACCENT,
    "COLOR_SUCCESS": COLOR_SUCCESS,
    "COLOR_WARNING": COLOR_WARNING,
    "COLOR_ERROR": COLOR_ERROR,
}

THEMES = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
}

# =============================================================================
# TYPOGRAPHY
# =============================================================================
FONT_MONO = "JetBrains Mono"    # Numeric data, code
FONT_UI = "IBM Plex Sans"       # UI text
FONT_FALLBACK = "Segoe UI"      # Windows fallback

FONT_SIZE_XS = 10
FONT_SIZE_SM = 11
FONT_SIZE_MD = 13
FONT_SIZE_LG = 16
FONT_SIZE_XL = 20
FONT_SIZE_XXL = 28

# =============================================================================
# UI DIMENSIONS
# =============================================================================
BORDER_WIDTH = 1                # Sharp 1px borders
BORDER_RADIUS = 0               # No rounded corners (Brutalist)

SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 16
SPACING_LG = 24
SPACING_XL = 32

# Window
WINDOW_MIN_WIDTH = 1280
WINDOW_MIN_HEIGHT = 720
WINDOW_DEFAULT_WIDTH = 1280
WINDOW_DEFAULT_HEIGHT = 720

# Sidebar / Panels
SIDEBAR_WIDTH = 280
INSPECTOR_WIDTH = 400

# Thumbnail Grid
THUMBNAIL_SIZE = 160
THUMBNAIL_GAP = 8

# Toolbar
TOOLBAR_HEIGHT = 48
UTILITY_BAR_HEIGHT = 32

# =============================================================================
# CACHE SETTINGS
# =============================================================================
THUMBNAIL_CACHE_SIZE = 500      # Max thumbnails in LRU cache
THUMBNAIL_CACHE_MB = 256        # Max cache size in MB
IMAGE_LOAD_BATCH = 50           # Images to load per batch

# =============================================================================
# PROCESSING SETTINGS
# =============================================================================
# PROCESSING SETTINGS
# =============================================================================
FACE_DETECTION_CONFIDENCE = 0.5
MOSAIC_BLOCK_SIZE = 10          # Default mosaic pixel size
BLUR_KERNEL_SIZE = 51           # Default blur kernel

# =============================================================================
# I18N
# =============================================================================
SUPPORTED_LANGUAGES = ['en', 'ko']
DEFAULT_LANGUAGE = 'en'

# =============================================================================
# MOSAIC MODE
# =============================================================================
class MosaicMode:
    AUTO = "auto"               # Automatic face detection only
    MANUAL = "manual"           # Manual ROI only
    OVERRIDE = "override"       # Manual overrides auto
    APPEND = "append"           # Manual + Auto combined
