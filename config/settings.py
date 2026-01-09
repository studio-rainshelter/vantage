"""
VANTAGE Settings Manager

Handles application settings persistence and runtime configuration.
"""

import json
from pathlib import Path
from typing import Any, Optional

from .constants import DEFAULT_LANGUAGE, MosaicMode


class Settings:
    """
    Application settings manager with JSON persistence.
    
    Settings are stored in user's app data directory and persist
    across application restarts.
    """
    
    _instance: Optional['Settings'] = None
    
    # Default settings
    DEFAULTS = {
        'language': DEFAULT_LANGUAGE,
        'mosaic_mode': MosaicMode.AUTO,
        'mosaic_block_size': 10,
        'blur_kernel_size': 51,
        'face_detection_confidence': 0.3, # MediaPipe Confidence
        'face_detection_model_type': 'full', # 'short' or 'full'
        'last_open_directory': '',
        'last_save_directory': '',
        'window_geometry': None,
        'show_ruler': True,
        'auto_save_edits': False,
        'theme': 'dark',
    }
    
    def __new__(cls) -> 'Settings':
        """Singleton pattern for global settings access."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._settings: dict[str, Any] = self.DEFAULTS.copy()
        self._settings_file = self._get_settings_path()
        self._load()
    
    def _get_settings_path(self) -> Path:
        """Get platform-appropriate settings file path."""
        import os
        app_data = Path(os.environ.get('APPDATA', Path.home()))
        settings_dir = app_data / 'VANTAGE'
        settings_dir.mkdir(parents=True, exist_ok=True)
        return settings_dir / 'settings.json'
    
    def _load(self) -> None:
        """Load settings from disk."""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults to handle new settings
                    self._settings = {**self.DEFAULTS, **loaded}
        except (json.JSONDecodeError, IOError) as e:
            print(f"[Settings] Failed to load settings: {e}")
            self._settings = self.DEFAULTS.copy()
    
    def save(self) -> None:
        """Persist settings to disk."""
        try:
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[Settings] Failed to save settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        """Set a setting value."""
        self._settings[key] = value
        if auto_save:
            self.save()
    
    def reset(self) -> None:
        """Reset all settings to defaults."""
        self._settings = self.DEFAULTS.copy()
        self.save()
    
    # Convenience properties
    @property
    def language(self) -> str:
        return self.get('language', DEFAULT_LANGUAGE)
    
    @language.setter
    def language(self, value: str) -> None:
        self.set('language', value)
    
    @property
    def mosaic_mode(self) -> str:
        return self.get('mosaic_mode', MosaicMode.AUTO)
    
    @mosaic_mode.setter
    def mosaic_mode(self, value: str) -> None:
        self.set('mosaic_mode', value)

    @property
    def theme(self) -> str:
        return self.get('theme', 'dark')

    @theme.setter
    def theme(self, value: str) -> None:
        self.set('theme', value)
