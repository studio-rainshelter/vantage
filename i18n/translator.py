"""
VANTAGE Translator

Manages multi-language translation with EN/KR support.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any

from config.constants import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE


class Translator:
    """
    Translation manager for multi-language support.
    
    Loads translation files and provides text lookup by key.
    Supports runtime language switching.
    """
    
    _instance: Optional['Translator'] = None
    
    def __new__(cls) -> 'Translator':
        """Singleton pattern for global translation access."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._current_language = DEFAULT_LANGUAGE
        self._translations: Dict[str, Dict[str, str]] = {}
        self._i18n_dir = Path(__file__).parent
        self._load_all_languages()
        
        # Callbacks for language change notification
        self._observers: list = []
    
    def _load_all_languages(self) -> None:
        """Load all available translation files."""
        for lang in SUPPORTED_LANGUAGES:
            self._load_language(lang)
    
    def _load_language(self, lang: str) -> None:
        """Load a single language file."""
        try:
            lang_file = self._i18n_dir / f"{lang}.json"
            if lang_file.exists():
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self._translations[lang] = json.load(f)
                print(f"[Translator] Loaded language: {lang}")
            else:
                print(f"[Translator] Language file not found: {lang_file}")
                self._translations[lang] = {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"[Translator] Error loading {lang}: {e}")
            self._translations[lang] = {}
    
    def get(self, key: str, **kwargs) -> str:
        """
        Get translated text for a key.
        
        Args:
            key: Translation key (dot-notation supported)
            **kwargs: Format arguments for string interpolation
            
        Returns:
            Translated text, or key itself if not found
        """
        translations = self._translations.get(self._current_language, {})
        
        # Support dot notation (e.g., "menu.file.open")
        value = translations
        for part in key.split('.'):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
                break
        
        if value is None:
            # Fallback to default language
            translations = self._translations.get(DEFAULT_LANGUAGE, {})
            value = translations
            for part in key.split('.'):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
        
        if value is None:
            # Return key as fallback
            return key
        
        # Apply format arguments
        if kwargs:
            try:
                return str(value).format(**kwargs)
            except KeyError:
                return str(value)
        
        return str(value)
    
    def set_language(self, lang: str) -> bool:
        """
        Switch to a different language.
        
        Args:
            lang: Language code ('en' or 'ko')
            
        Returns:
            True if successful, False if language not supported
        """
        if lang not in SUPPORTED_LANGUAGES:
            print(f"[Translator] Unsupported language: {lang}")
            return False
        
        if lang != self._current_language:
            self._current_language = lang
            self._notify_observers()
            print(f"[Translator] Switched to: {lang}")
        
        return True
    
    @property
    def current_language(self) -> str:
        """Get current language code."""
        return self._current_language
    
    @property
    def is_korean(self) -> bool:
        """Check if current language is Korean."""
        return self._current_language == 'ko'
    
    @property
    def is_english(self) -> bool:
        """Check if current language is English."""
        return self._current_language == 'en'
    
    def toggle_language(self) -> str:
        """Toggle between EN and KR."""
        new_lang = 'ko' if self._current_language == 'en' else 'en'
        self.set_language(new_lang)
        return new_lang
    
    def add_observer(self, callback) -> None:
        """Register a callback for language change events."""
        if callback not in self._observers:
            self._observers.append(callback)
    
    def remove_observer(self, callback) -> None:
        """Unregister a language change callback."""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self) -> None:
        """Notify all observers of language change."""
        for callback in self._observers:
            try:
                callback(self._current_language)
            except Exception as e:
                print(f"[Translator] Observer error: {e}")


# Global translator instance
_translator = Translator()


def tr(key: str, **kwargs) -> str:
    """
    Shorthand function for translation.
    
    Usage:
        from i18n import tr
        label.setText(tr('menu.file.open'))
    """
    return _translator.get(key, **kwargs)
