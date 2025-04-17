"""
Image Metadata Extractor - GUI Package

This package contains all the graphical user interface components for the application.

Modules:
    - main_window: Main application window and controller
    - result_view: Components for displaying extraction results
    - menu_bar: Application menu and toolbar
    - styles: UI styling and theme management
    - dialogs: Custom dialog boxes for the application
    - widgets: Custom widgets and UI components
"""

import logging
import tkinter as tk
from tkinter import ttk
import os
import sys

# Setup package-level logger
logger = logging.getLogger(__name__)

# GUI Constants
DEFAULT_PADDING = 10
DEFAULT_FONT = ("Helvetica", 10)
HEADER_FONT = ("Helvetica", 12, "bold")
MONOSPACE_FONT = ("Courier", 10)

# Color scheme
COLORS = {
    'primary': '#3498db',      # Blue
    'secondary': '#2ecc71',    # Green
    'accent': '#e74c3c',       # Red
    'background': '#f5f5f5',   # Light gray
    'text': '#2c3e50',         # Dark blue/gray
    'light_text': '#7f8c8d',   # Medium gray
    'border': '#bdc3c7',       # Light gray
    'highlight': '#f39c12',    # Orange
    'warning': '#e74c3c',      # Red
    'success': '#2ecc71',      # Green
}

# Check if running in a GUI environment
def is_gui_available():
    """Check if the GUI environment is available."""
    try:
        root = tk.Tk()
        root.destroy()
        return True
    except Exception as e:
        logger.warning(f"GUI environment not available: {e}")
        return False

# Initialize GUI environment
GUI_AVAILABLE = is_gui_available()

if not GUI_AVAILABLE:
    logger.warning("No display available. GUI components may not function properly.")

# Import GUI components
try:
    from .styles import setup_styles, apply_theme
    from .main_window import MainWindow
    from .result_view import ResultView
    from .menu_bar import MenuBar
    
    # Define what gets imported with "from src.gui import *"
    __all__ = [
        'MainWindow',
        'ResultView',
        'MenuBar',
        'setup_styles',
        'apply_theme',
        'COLORS',
        'DEFAULT_PADDING',
        'DEFAULT_FONT',
        'HEADER_FONT',
        'MONOSPACE_FONT',
    ]
    
except ImportError as e:
    logger.error(f"Error importing GUI components: {e}")
    # Define a minimal __all__ in case of import errors
    __all__ = ['COLORS', 'DEFAULT_PADDING', 'DEFAULT_FONT']

# Setup theme if GUI is available
def initialize_gui():
    """Initialize GUI settings and themes."""
    if not GUI_AVAILABLE:
        return False
    
    try:
        # Try to import and use ttkthemes for better looking UI
        try:
            from ttkthemes import ThemedStyle
            logger.info("ttkthemes available, using enhanced themes")
            HAS_TTKTHEMES = True
        except ImportError:
            logger.info("ttkthemes not available, using default themes")
            HAS_TTKTHEMES = False
        
        # Setup custom styles and themes
        if 'setup_styles' in globals():
            setup_styles(HAS_TTKTHEMES)
        
        logger.info("GUI initialization complete")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing GUI: {e}")
        return False

# Custom exception for GUI errors
class GUIError(Exception):
    """Exception raised for errors in the GUI components."""
    pass

# Helper functions for GUI components
def center_window(window):
    """Center a tkinter window on the screen."""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

def create_tooltip(widget, text):
    """Create a tooltip for a widget."""
    def enter(event):
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        
        # Create a toplevel window
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(tooltip, text=text, justify=tk.LEFT,
                         background=COLORS['background'], relief=tk.SOLID, borderwidth=1,
                         font=DEFAULT_FONT, padding=DEFAULT_PADDING//2)
        label.pack(ipadx=1)
        
        widget.tooltip = tooltip
        
    def leave(event):
        if hasattr(widget, "tooltip"):
            widget.tooltip.destroy()
            
    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)

# Initialize GUI on import if available
if GUI_AVAILABLE:
    initialize_gui()
else:
    logger.warning("GUI initialization skipped - no display available")

logger.debug("GUI package loaded")