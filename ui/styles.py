"""
VANTAGE Style System

Industrial Brutalism Qt StyleSheets.
Sharp grids, high contrast, exposed structure.
"""

from config.constants import (
    COLOR_BASE, COLOR_BASE_LIGHT, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_BORDER, COLOR_BORDER_FOCUS, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_TEXT_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR,
    FONT_MONO, FONT_UI, FONT_FALLBACK,
    FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG, FONT_SIZE_XL,
    BORDER_WIDTH, BORDER_RADIUS, SPACING_SM, SPACING_MD,
    TOOLBAR_HEIGHT, UTILITY_BAR_HEIGHT
)


class Styles:
    """
    Industrial Brutalism style sheets for Qt widgets.
    
    Design principles:
    - No rounded corners (BORDER_RADIUS = 0)
    - Sharp 1px borders
    - High contrast colors
    - Monospace fonts for data
    - Exposed structural elements
    """
    
    @staticmethod
    def get_main_stylesheet() -> str:
        """Complete application stylesheet."""
        return f"""
        /* ========================================
           GLOBAL RESET & BASE
           ======================================== */
        
        * {{
            margin: 0;
            padding: 0;
            outline: none;
        }}
        
        QMainWindow, QDialog {{
            background-color: {COLOR_BASE};
            color: {COLOR_TEXT};
            font-family: "{FONT_UI}", "{FONT_FALLBACK}", sans-serif;
            font-size: {FONT_SIZE_MD}px;
        }}
        
        /* ========================================
           MENU BAR
           ======================================== */
        
        QMenuBar {{
            background-color: {COLOR_BASE};
            color: {COLOR_TEXT};
            border-bottom: {BORDER_WIDTH}px solid {COLOR_BORDER};
            padding: {SPACING_SM}px;
            font-size: {FONT_SIZE_SM}px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: {SPACING_SM}px {SPACING_MD}px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {COLOR_BORDER};
        }}
        
        QMenuBar::item:pressed {{
            background-color: {COLOR_ACCENT};
            color: {COLOR_TEXT_ACCENT};
        }}
        
        QMenu {{
            background-color: {COLOR_BASE_LIGHT};
            border: {BORDER_WIDTH}px solid {COLOR_BORDER};
            padding: {SPACING_SM}px 0;
        }}
        
        QMenu::item {{
            padding: {SPACING_SM}px {SPACING_MD}px;
            padding-right: 32px;
        }}
        
        QMenu::item:selected {{
            background-color: {COLOR_ACCENT};
            color: {COLOR_TEXT_ACCENT};
        }}
        
        QMenu::separator {{
            height: {BORDER_WIDTH}px;
            background-color: {COLOR_BORDER};
            margin: {SPACING_SM}px 0;
        }}
        
        /* ========================================
           TOOLBAR
           ======================================== */
        
        QToolBar {{
            background-color: {COLOR_BASE};
            border-bottom: {BORDER_WIDTH}px solid {COLOR_BORDER};
            spacing: {SPACING_SM}px;
            padding: {SPACING_SM}px;
            min-height: {TOOLBAR_HEIGHT}px;
        }}
        
        QToolButton {{
            background-color: transparent;
            border: {BORDER_WIDTH}px solid transparent;
            padding: {SPACING_SM}px;
            color: {COLOR_TEXT};
            font-size: {FONT_SIZE_SM}px;
        }}
        
        QToolButton:hover {{
            background-color: {COLOR_BORDER};
            border-color: {COLOR_BORDER};
        }}
        
        QToolButton:pressed {{
            background-color: {COLOR_ACCENT};
            color: {COLOR_TEXT_ACCENT};
        }}
        
        QToolButton:checked {{
            background-color: {COLOR_ACCENT};
            color: {COLOR_TEXT_ACCENT};
            border-color: {COLOR_ACCENT};
        }}
        
        /* ========================================
           SCROLL BARS - Brutalist
           ======================================== */
        
        QScrollBar:vertical {{
            background-color: {COLOR_BASE};
            width: 12px;
            border-left: {BORDER_WIDTH}px solid {COLOR_BORDER};
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {COLOR_BORDER};
            min-height: 40px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {COLOR_ACCENT};
        }}
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        
        QScrollBar:horizontal {{
            background-color: {COLOR_BASE};
            height: 12px;
            border-top: {BORDER_WIDTH}px solid {COLOR_BORDER};
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {COLOR_BORDER};
            min-width: 40px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {COLOR_ACCENT};
        }}
        
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        
        /* ========================================
           PANELS & FRAMES
           ======================================== */
        
        QFrame {{
            border: none;
        }}
        
        QFrame[frameShape="StyledPanel"] {{
            background-color: {COLOR_BASE_LIGHT};
            border: {BORDER_WIDTH}px solid {COLOR_BORDER};
        }}
        
        QSplitter::handle {{
            background-color: {COLOR_BORDER};
        }}
        
        QSplitter::handle:horizontal {{
            width: {BORDER_WIDTH}px;
        }}
        
        QSplitter::handle:vertical {{
            height: {BORDER_WIDTH}px;
        }}
        
        /* ========================================
           LABELS
           ======================================== */
        
        QLabel {{
            color: {COLOR_TEXT};
            background-color: transparent;
        }}
        
        QLabel[class="header"] {{
            font-size: {FONT_SIZE_LG}px;
            font-weight: bold;
            color: {COLOR_TEXT_ACCENT};
        }}
        
        QLabel[class="mono"] {{
            font-family: "{FONT_MONO}", monospace;
        }}
        
        QLabel[class="dim"] {{
            color: {COLOR_TEXT_DIM};
        }}
        
        /* ========================================
           BUTTONS
           ======================================== */
        
        QPushButton {{
            background-color: {COLOR_BORDER};
            color: {COLOR_TEXT};
            border: {BORDER_WIDTH}px solid {COLOR_BORDER};
            padding: {SPACING_SM}px {SPACING_MD}px;
            font-size: {FONT_SIZE_SM}px;
            min-height: 28px;
        }}
        
        QPushButton:hover {{
            background-color: {COLOR_BORDER_FOCUS};
            border-color: {COLOR_BORDER_FOCUS};
        }}
        
        QPushButton:pressed {{
            background-color: {COLOR_ACCENT};
            border-color: {COLOR_ACCENT};
            color: {COLOR_TEXT_ACCENT};
        }}
        
        QPushButton:disabled {{
            background-color: {COLOR_BASE_LIGHT};
            color: {COLOR_TEXT_DIM};
            border-color: {COLOR_BASE_LIGHT};
        }}
        
        QPushButton[class="primary"] {{
            background-color: {COLOR_ACCENT};
            border-color: {COLOR_ACCENT};
            color: {COLOR_TEXT_ACCENT};
        }}
        
        QPushButton[class="primary"]:hover {{
            background-color: {COLOR_ACCENT_HOVER};
            border-color: {COLOR_ACCENT_HOVER};
        }}
        
        /* ========================================
           LINE EDITS & INPUTS
           ======================================== */
        
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {COLOR_BASE};
            color: {COLOR_TEXT};
            border: {BORDER_WIDTH}px solid {COLOR_BORDER};
            padding: {SPACING_SM}px;
            font-family: "{FONT_MONO}", monospace;
            selection-background-color: {COLOR_ACCENT};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {COLOR_ACCENT};
        }}
        
        /* ========================================
           COMBO BOX
           ======================================== */
        
        QComboBox {{
            background-color: {COLOR_BORDER};
            color: {COLOR_TEXT};
            border: {BORDER_WIDTH}px solid {COLOR_BORDER};
            padding: {SPACING_SM}px;
            min-height: 28px;
        }}
        
        QComboBox:hover {{
            border-color: {COLOR_BORDER_FOCUS};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {COLOR_BASE_LIGHT};
            border: {BORDER_WIDTH}px solid {COLOR_BORDER};
            selection-background-color: {COLOR_ACCENT};
        }}
        
        /* ========================================
           SLIDERS
           ======================================== */
        
        QSlider::groove:horizontal {{
            background-color: {COLOR_BORDER};
            height: 4px;
        }}
        
        QSlider::handle:horizontal {{
            background-color: {COLOR_ACCENT};
            width: 16px;
            margin: -6px 0;
        }}
        
        QSlider::handle:horizontal:hover {{
            background-color: {COLOR_ACCENT_HOVER};
        }}
        
        /* ========================================
           SPIN BOX
           ======================================== */
        
        QSpinBox, QDoubleSpinBox {{
            background-color: {COLOR_BASE};
            color: {COLOR_TEXT};
            border: {BORDER_WIDTH}px solid {COLOR_BORDER};
            padding: {SPACING_SM}px;
            font-family: "{FONT_MONO}", monospace;
        }}
        
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {COLOR_ACCENT};
        }}
        
        /* ========================================
           STATUS BAR
           ======================================== */
        
        QStatusBar {{
            background-color: {COLOR_BASE};
            border-top: {BORDER_WIDTH}px solid {COLOR_BORDER};
            color: {COLOR_TEXT_DIM};
            font-size: {FONT_SIZE_XS}px;
        }}
        
        QStatusBar::item {{
            border: none;
        }}
        
        /* ========================================
           PROGRESS BAR
           ======================================== */
        
        QProgressBar {{
            background-color: {COLOR_BASE};
            border: {BORDER_WIDTH}px solid {COLOR_BORDER};
            height: 20px;
            text-align: center;
            font-family: "{FONT_MONO}", monospace;
            font-size: {FONT_SIZE_XS}px;
        }}
        
        QProgressBar::chunk {{
            background-color: {COLOR_ACCENT};
        }}
        
        /* ========================================
           TOOLTIPS
           ======================================== */
        
        QToolTip {{
            background-color: {COLOR_BASE_LIGHT};
            color: {COLOR_TEXT};
            border: {BORDER_WIDTH}px solid {COLOR_BORDER};
            padding: {SPACING_SM}px;
            font-size: {FONT_SIZE_XS}px;
        }}
        """
    
    @staticmethod
    def get_language_switcher_style() -> str:
        """Style for the language toggle button."""
        return f"""
        QPushButton {{
            background-color: transparent;
            border: {BORDER_WIDTH}px solid {COLOR_BORDER};
            color: {COLOR_TEXT};
            font-family: "{FONT_MONO}", monospace;
            font-size: {FONT_SIZE_MD}px;
            font-weight: bold;
            min-width: 48px;
            min-height: 28px;
            padding: 4px 8px;
        }}
        
        QPushButton:hover {{
            background-color: {COLOR_BORDER};
            color: {COLOR_TEXT_ACCENT};
        }}
        
        QPushButton:pressed {{
            background-color: {COLOR_ACCENT};
            border-color: {COLOR_ACCENT};
            color: {COLOR_TEXT_ACCENT};
        }}
        """
    
    @staticmethod
    def get_manual_marker_style() -> str:
        """Style for the 'M' manual edit marker overlay."""
        return f"""
        QLabel {{
            background-color: {COLOR_ACCENT};
            color: {COLOR_TEXT_ACCENT};
            font-family: "{FONT_MONO}", monospace;
            font-size: {FONT_SIZE_LG}px;
            font-weight: bold;
            padding: 2px 6px;
            min-width: 20px;
            qproperty-alignment: AlignCenter;
        }}
        """
    
    @staticmethod
    def get_thumbnail_style(selected: bool = False) -> str:
        """Style for thumbnail items."""
        border_color = COLOR_ACCENT if selected else COLOR_BORDER
        return f"""
        QFrame {{
            background-color: {COLOR_BASE_LIGHT};
            border: {BORDER_WIDTH}px solid {border_color};
        }}
        
        QFrame:hover {{
            border-color: {COLOR_ACCENT if selected else COLOR_BORDER_FOCUS};
        }}
        """
    
    @staticmethod
    def get_empty_state_style() -> str:
        """Style for empty state / drop zone."""
        return f"""
        QFrame {{
            background-color: {COLOR_BASE};
            border: 2px dashed {COLOR_BORDER};
        }}
        
        QFrame:hover {{
            border-color: {COLOR_ACCENT};
        }}
        
        QLabel {{
            color: {COLOR_TEXT_DIM};
        }}
        
        QLabel[class="title"] {{
            font-size: {FONT_SIZE_XL}px;
            color: {COLOR_TEXT};
        }}
        """
