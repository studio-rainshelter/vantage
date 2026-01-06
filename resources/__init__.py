"""
VANTAGE Resources Module

Static resources management (icons, fonts).
"""

from pathlib import Path


# Resource directories
RESOURCES_DIR = Path(__file__).parent
ICONS_DIR = RESOURCES_DIR / "icons"
FONTS_DIR = RESOURCES_DIR / "fonts"


def get_icon_path(name: str) -> Path:
    """Get path to an icon file."""
    return ICONS_DIR / name


def get_font_path(name: str) -> Path:
    """Get path to a font file."""
    return FONTS_DIR / name
