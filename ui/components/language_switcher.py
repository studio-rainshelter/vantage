"""
VANTAGE Language Switcher

文/A toggle button for switching between Korean and English.
Industrial toggle switch design.
"""

from typing import Optional
from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import Signal

from i18n import Translator
from ui.styles import Styles


class LanguageSwitcher(QPushButton):
    """
    Language toggle button (文/A design).
    
    Displays current language symbol and switches on click.
    Korean: 文 (Hanja for "language/writing")
    English: A
    """
    
    language_changed = Signal(str)  # Emits new language code
    
    # Display symbols
    SYMBOLS = {
        'ko': '文',  # Hanja
        'en': 'A'
    }
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._translator = Translator()
        
        self._setup_ui()
        self._update_display()
        
        # Connect click
        self.clicked.connect(self._toggle_language)
        
        # Listen for external language changes
        self._translator.add_observer(self._on_language_changed)
    
    def _setup_ui(self):
        """Initialize the button styling."""
        self.setStyleSheet(Styles.get_language_switcher_style())
        self.setCursor(self.cursor())  # Inherit cursor
        self.setToolTip("Toggle Language / 언어 전환")
    
    def _update_display(self):
        """Update button text based on current language."""
        current = self._translator.current_language
        self.setText(self.SYMBOLS.get(current, 'A'))
    
    def _toggle_language(self):
        """Toggle between languages."""
        new_lang = self._translator.toggle_language()
        self.language_changed.emit(new_lang)
    
    def _on_language_changed(self, lang: str):
        """Handle external language change."""
        self._update_display()
    
    def set_language(self, lang: str):
        """Programmatically set language."""
        if self._translator.set_language(lang):
            self.language_changed.emit(lang)
