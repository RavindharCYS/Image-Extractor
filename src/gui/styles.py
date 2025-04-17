"""
Styles Module for Image Metadata Extractor

This module handles UI styling and theme management for the application.
It provides functions to set up and apply different visual themes.
"""

import tkinter as tk
from tkinter import ttk
import logging
import os
import platform
import json

# Get the package logger
logger = logging.getLogger(__name__)

# Define color schemes for different themes
COLOR_SCHEMES = {
    "Default": {
        "primary": "#3498db",      # Blue
        "secondary": "#2ecc71",    # Green
        "accent": "#e74c3c",       # Red
        "background": "#f5f5f5",   # Light gray
        "text": "#2c3e50",         # Dark blue/gray
        "light_text": "#7f8c8d",   # Medium gray
        "border": "#bdc3c7",       # Light gray
        "highlight": "#f39c12",    # Orange
        "warning": "#e74c3c",      # Red
        "success": "#2ecc71",      # Green
    },
    "Light": {
        "primary": "#2980b9",      # Darker blue
        "secondary": "#27ae60",    # Darker green
        "accent": "#c0392b",       # Darker red
        "background": "#ffffff",   # White
        "text": "#333333",         # Dark gray
        "light_text": "#666666",   # Medium gray
        "border": "#dddddd",       # Light gray
        "highlight": "#e67e22",    # Darker orange
        "warning": "#c0392b",      # Darker red
        "success": "#27ae60",      # Darker green
    },
    "Dark": {
        "primary": "#3498db",      # Blue
        "secondary": "#2ecc71",    # Green
        "accent": "#e74c3c",       # Red
        "background": "#2c3e50",   # Dark blue/gray
        "text": "#ecf0f1",         # Light gray/white
        "light_text": "#bdc3c7",   # Light gray
        "border": "#34495e",       # Darker blue/gray
        "highlight": "#f39c12",    # Orange
        "warning": "#e74c3c",      # Red
        "success": "#2ecc71",      # Green
    },
    "System": {
        # This will be determined by the system theme
        # Default values as fallback
        "primary": "#3498db",      # Blue
        "secondary": "#2ecc71",    # Green
        "accent": "#e74c3c",       # Red
        "background": "#f5f5f5",   # Light gray
        "text": "#2c3e50",         # Dark blue/gray
        "light_text": "#7f8c8d",   # Medium gray
        "border": "#bdc3c7",       # Light gray
        "highlight": "#f39c12",    # Orange
        "warning": "#e74c3c",      # Red
        "success": "#2ecc71",      # Green
    }
}

# Define font configurations
FONT_CONFIGS = {
    "small": {
        "default": ("Helvetica", 9),
        "bold": ("Helvetica", 9, "bold"),
        "italic": ("Helvetica", 9, "italic"),
        "monospace": ("Courier", 9)
    },
    "medium": {
        "default": ("Helvetica", 10),
        "bold": ("Helvetica", 10, "bold"),
        "italic": ("Helvetica", 10, "italic"),
        "monospace": ("Courier", 10)
    },
    "large": {
        "default": ("Helvetica", 12),
        "bold": ("Helvetica", 12, "bold"),
        "italic": ("Helvetica", 12, "italic"),
        "monospace": ("Courier", 12)
    },
    "header": {
        "default": ("Helvetica", 14),
        "bold": ("Helvetica", 14, "bold"),
        "italic": ("Helvetica", 14, "italic"),
        "monospace": ("Courier", 14)
    }
}

# Current theme and font size
current_theme = "Default"
current_font_size = "medium"


def detect_system_theme():
    """
    Detect the system theme (light or dark) if possible.
    
    Returns:
        str: "Light" or "Dark" based on system settings, or None if detection fails
    """
    try:
        system = platform.system()
        
        if system == "Windows":
            # Windows theme detection
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "Light" if value == 1 else "Dark"
            
        elif system == "Darwin":  # macOS
            # macOS theme detection
            import subprocess
            result = subprocess.run(
                ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                capture_output=True, text=True
            )
            return "Dark" if result.stdout.strip() == "Dark" else "Light"
            
        elif system == "Linux":
            # Linux theme detection (GNOME)
            import subprocess
            try:
                result = subprocess.run(
                    ['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'],
                    capture_output=True, text=True
                )
                theme_name = result.stdout.strip().lower()
                return "Dark" if "dark" in theme_name else "Light"
            except:
                # Try another method for Linux
                try:
                    result = subprocess.run(
                        ['dconf', 'read', '/org/gnome/desktop/interface/color-scheme'],
                        capture_output=True, text=True
                    )
                    return "Dark" if "dark" in result.stdout.strip().lower() else "Light"
                except:
                    return None
        
        return None  # Could not detect
        
    except Exception as e:
        logger.warning(f"Failed to detect system theme: {e}")
        return None


def setup_styles(has_ttkthemes=False):
    """
    Set up the application styles and themes.
    
    Args:
        has_ttkthemes (bool): Whether the ttkthemes package is available
    """
    try:
        # Detect system theme for "System" theme option
        system_theme = detect_system_theme()
        if system_theme:
            # Update the System theme colors based on detected theme
            COLOR_SCHEMES["System"] = COLOR_SCHEMES[system_theme].copy()
            logger.info(f"Detected system theme: {system_theme}")
        
        # Create style object
        style = ttk.Style()
        
        # Set initial theme
        if has_ttkthemes:
            try:
                from ttkthemes import ThemedStyle
                style = ThemedStyle()
                style.set_theme("arc")  # A modern, clean theme
                logger.info("Using ttkthemes with 'arc' theme")
            except Exception as e:
                logger.warning(f"Failed to apply ttkthemes: {e}")
                # Fall back to default ttk theme
                style.theme_use('clam' if 'clam' in style.theme_names() else 'default')
        else:
            # Use the best available built-in theme
            available_themes = style.theme_names()
            preferred_themes = ['clam', 'vista', 'xpnative', 'winnative', 'default']
            
            for theme in preferred_themes:
                if theme in available_themes:
                    style.theme_use(theme)
                    logger.info(f"Using built-in theme: {theme}")
                    break
        
        # Apply the default theme colors
        apply_theme_colors(style, "Default")
        
        logger.info("Styles initialized successfully")
        return style
        
    except Exception as e:
        logger.error(f"Error setting up styles: {e}")
        # Return a basic style to avoid errors
        return ttk.Style()


def apply_theme(theme_name, font_size=None):
    """
    Apply a theme to the application.
    
    Args:
        theme_name (str): Name of the theme to apply
        font_size (str, optional): Font size to use (small, medium, large)
    
    Returns:
        bool: True if theme was applied successfully, False otherwise
    """
    try:
        global current_theme, current_font_size
        
        # Validate theme name
        if theme_name not in COLOR_SCHEMES:
            logger.warning(f"Unknown theme: {theme_name}, falling back to Default")
            theme_name = "Default"
        
        # Validate font size
        if font_size and font_size not in FONT_CONFIGS:
            logger.warning(f"Unknown font size: {font_size}, falling back to medium")
            font_size = "medium"
        
        # Update current settings
        current_theme = theme_name
        if font_size:
            current_font_size = font_size
        
        # Get style object
        style = ttk.Style()
        
        # Apply theme colors
        apply_theme_colors(style, theme_name)
        
        # Apply font configuration
        apply_font_config(style, current_font_size)
        
        logger.info(f"Applied theme: {theme_name}, font size: {current_font_size}")
        return True
        
    except Exception as e:
        logger.error(f"Error applying theme: {e}")
        return False


def apply_theme_colors(style, theme_name):
    """
    Apply color scheme for the specified theme.
    
    Args:
        style (ttk.Style): The style object to configure
        theme_name (str): Name of the theme to apply
    """
    # Get color scheme
    colors = COLOR_SCHEMES.get(theme_name, COLOR_SCHEMES["Default"])
    
    # Configure common elements
    style.configure("TFrame", background=colors["background"])
    style.configure("TLabel", background=colors["background"], foreground=colors["text"])
    style.configure("TButton", 
                   background=colors["primary"], 
                   foreground="white",
                   bordercolor=colors["border"])
    
    # Button states
    style.map("TButton",
             background=[("active", colors["highlight"]), 
                        ("disabled", colors["border"])],
             foreground=[("disabled", colors["light_text"])])
    
    # Entry fields
    style.configure("TEntry", 
                   fieldbackground="white", 
                   foreground=colors["text"],
                   bordercolor=colors["border"])
    
    # Notebook (tabs)
    style.configure("TNotebook", 
                   background=colors["background"], 
                   bordercolor=colors["border"])
    style.configure("TNotebook.Tab", 
                   background=colors["background"], 
                   foreground=colors["text"],
                   bordercolor=colors["border"])
    
    # Active tab
    style.map("TNotebook.Tab",
             background=[("selected", colors["primary"])],
             foreground=[("selected", "white")])
    
    # Treeview (for metadata display)
    style.configure("Treeview", 
                   background="white", 
                   foreground=colors["text"],
                   fieldbackground="white")
    style.configure("Treeview.Heading", 
                   background=colors["primary"], 
                   foreground="white",
                   font=FONT_CONFIGS[current_font_size]["bold"])
    
    # Selected items in treeview
    style.map("Treeview",
             background=[("selected", colors["primary"])],
             foreground=[("selected", "white")])
    
    # Scrollbars
    style.configure("Vertical.TScrollbar", 
                   background=colors["background"], 
                   troughcolor=colors["background"],
                   bordercolor=colors["border"])
    style.configure("Horizontal.TScrollbar", 
                   background=colors["background"], 
                   troughcolor=colors["background"],
                   bordercolor=colors["border"])
    
    # Progress bar
    style.configure("TProgressbar", 
                   background=colors["primary"], 
                   troughcolor=colors["background"],
                   bordercolor=colors["border"])
    
    # Separator
    style.configure("TSeparator", background=colors["border"])
    
    # Label frames
    style.configure("TLabelframe", 
                   background=colors["background"], 
                   foreground=colors["text"],
                   bordercolor=colors["border"])
    style.configure("TLabelframe.Label", 
                   background=colors["background"], 
                   foreground=colors["text"],
                   font=FONT_CONFIGS[current_font_size]["bold"])
    
    # Checkbutton
    style.configure("TCheckbutton", 
                   background=colors["background"], 
                   foreground=colors["text"])
    
    # Radiobutton
    style.configure("TRadiobutton", 
                   background=colors["background"], 
                   foreground=colors["text"])
    
    # Combobox
    style.configure("TCombobox", 
                   background="white", 
                   foreground=colors["text"],
                   fieldbackground="white")
    
    # Custom styles for specific elements
    
    # Header label
    style.configure("Header.TLabel", 
                   font=FONT_CONFIGS[current_font_size]["header"],
                   foreground=colors["primary"])
    
    # Success button
    style.configure("Success.TButton", 
                   background=colors["success"], 
                   foreground="white")
    style.map("Success.TButton",
             background=[("active", colors["secondary"])])
    
    # Warning button
    style.configure("Warning.TButton", 
                   background=colors["warning"], 
                   foreground="white")
    style.map("Warning.TButton",
             background=[("active", colors["accent"])])
    
    # Info text
    style.configure("Info.TLabel", 
                   foreground=colors["light_text"],
                   font=FONT_CONFIGS[current_font_size]["italic"])
    
    # Status bar
    style.configure("StatusBar.TFrame", 
                   background=colors["border"])
    style.configure("StatusBar.TLabel", 
                   background=colors["border"],
                   foreground=colors["text"])
    
    # Highlight frame (for drag and drop)
    style.configure("Highlight.TFrame", 
                   background=colors["background"],
                   bordercolor=colors["primary"],
                   relief="solid")
    
    # Apply platform-specific adjustments
    _apply_platform_specific_styles(style, colors)


def apply_font_config(style, font_size):
    """
    Apply font configuration for the specified size.
    
    Args:
        style (ttk.Style): The style object to configure
        font_size (str): Size category (small, medium, large)
    """
    # Get font configuration
    fonts = FONT_CONFIGS.get(font_size, FONT_CONFIGS["medium"])
    
    # Apply fonts to common elements
    style.configure("TLabel", font=fonts["default"])
    style.configure("TButton", font=fonts["default"])
    style.configure("TCheckbutton", font=fonts["default"])
    style.configure("TRadiobutton", font=fonts["default"])
    style.configure("TEntry", font=fonts["default"])
    style.configure("TCombobox", font=fonts["default"])
    style.configure("Treeview", font=fonts["default"])
    
    # Special font styles
    style.configure("Header.TLabel", font=fonts["header"])
    style.configure("Bold.TLabel", font=fonts["bold"])
    style.configure("Italic.TLabel", font=fonts["italic"])
    style.configure("Monospace.TLabel", font=fonts["monospace"])


def _apply_platform_specific_styles(style, colors):
    """
    Apply platform-specific style adjustments.
    
    Args:
        style (ttk.Style): The style object to configure
        colors (dict): Color scheme dictionary
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        # macOS specific adjustments
        style.configure("TButton", relief="flat", borderwidth=0)
        style.configure("TEntry", relief="solid", borderwidth=1)
        style.configure("TNotebook", relief="flat", borderwidth=0)
        
    elif system == "Windows":
        # Windows specific adjustments
        pass  # Default styles work well on Windows
        
    elif system == "Linux":
        # Linux specific adjustments
        pass  # Default styles work well on most Linux distributions


def get_current_theme():
    """
    Get the current theme name.
    
    Returns:
        str: Name of the current theme
    """
    return current_theme


def get_current_font_size():
    """
    Get the current font size.
    
    Returns:
        str: Current font size category (small, medium, large)
    """
    return current_font_size


def get_color_scheme(theme_name=None):
    """
    Get the color scheme for a theme.
    
    Args:
        theme_name (str, optional): Name of the theme. If None, uses current theme.
    
    Returns:
        dict: Color scheme dictionary
    """
    if theme_name is None:
        theme_name = current_theme
    
    return COLOR_SCHEMES.get(theme_name, COLOR_SCHEMES["Default"])


def save_theme_preferences(theme_name, font_size):
    """
    Save theme preferences to a configuration file.
    
    Args:
        theme_name (str): Name of the theme
        font_size (str): Font size category
    
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Create config directory if it doesn't exist
        config_dir = os.path.join(os.path.expanduser("~"), ".image_metadata_extractor")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        # Create preferences file path
        prefs_file = os.path.join(config_dir, "theme_preferences.json")
        
        # Save preferences
        preferences = {
            "theme": theme_name,
            "font_size": font_size,
            "last_updated": str(datetime.datetime.now())
        }
        
        with open(prefs_file, 'w') as f:
            json.dump(preferences, f, indent=4)
        
        logger.info(f"Saved theme preferences: {theme_name}, {font_size}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving theme preferences: {e}")
        return False


def load_theme_preferences():
    """
    Load theme preferences from configuration file.
    
    Returns:
        tuple: (theme_name, font_size) or (None, None) if loading fails
    """
    try:
        # Check if preferences file exists
        prefs_file = os.path.join(os.path.expanduser("~"), ".image_metadata_extractor", "theme_preferences.json")
        
        if not os.path.exists(prefs_file):
            logger.info("No theme preferences file found, using defaults")
            return None, None
        
        # Load preferences
        with open(prefs_file, 'r') as f:
            preferences = json.load(f)
        
        theme_name = preferences.get("theme")
        font_size = preferences.get("font_size")
        
        # Validate
        if theme_name not in COLOR_SCHEMES:
            logger.warning(f"Unknown theme in preferences: {theme_name}, using default")
            theme_name = "Default"
        
        if font_size not in FONT_CONFIGS:
            logger.warning(f"Unknown font size in preferences: {font_size}, using medium")
            font_size = "medium"
        
        logger.info(f"Loaded theme preferences: {theme_name}, {font_size}")
        return theme_name, font_size
        
    except Exception as e:
        logger.error(f"Error loading theme preferences: {e}")
        return None, None


def create_custom_style(style_name, base_theme=None, **kwargs):
    """
    Create a custom style based on a theme.
    
    Args:
        style_name (str): Name for the custom style
        base_theme (str, optional): Base theme to use. If None, uses current theme.
        **kwargs: Style properties to override
    
    Returns:
        str: The created style name
    """
    try:
        # Get base theme colors
        if base_theme is None:
            base_theme = current_theme
        
        colors = COLOR_SCHEMES.get(base_theme, COLOR_SCHEMES["Default"]).copy()
        
        # Override with provided properties
        for key, value in kwargs.items():
            if key in colors:
                colors[key] = value
        
        # Get style object
        style = ttk.Style()
        
        # Create the custom style
        if "." in style_name:
            # Style for a specific widget type (e.g., "Custom.TButton")
            widget_type = style_name.split(".")[-1]
            style.configure(style_name, **{k: v for k, v in kwargs.items()})
            
            # Apply appropriate base styling based on widget type
            if widget_type == "TButton":
                style.configure(style_name, 
                               background=kwargs.get("background", colors["primary"]),
                               foreground=kwargs.get("foreground", "white"))
                
                style.map(style_name,
                         background=[("active", kwargs.get("active_bg", colors["highlight"])), 
                                    ("disabled", kwargs.get("disabled_bg", colors["border"]))],
                         foreground=[("disabled", kwargs.get("disabled_fg", colors["light_text"]))])
                
            elif widget_type == "TLabel":
                style.configure(style_name, 
                               background=kwargs.get("background", colors["background"]),
                               foreground=kwargs.get("foreground", colors["text"]))
                
            elif widget_type == "TFrame":
                style.configure(style_name, 
                               background=kwargs.get("background", colors["background"]))
                
            # Add more widget types as needed
        
        else:
            # Generic style
            style.configure(style_name, **kwargs)
        
        logger.debug(f"Created custom style: {style_name}")
        return style_name
        
    except Exception as e:
        logger.error(f"Error creating custom style: {e}")
        return None


def apply_theme_to_widget(widget, theme_name=None):
    """
    Apply theme colors directly to a widget (useful for non-ttk widgets).
    
    Args:
        widget: The widget to style
        theme_name (str, optional): Theme to apply. If None, uses current theme.
    """
    try:
        # Get theme colors
        if theme_name is None:
            theme_name = current_theme
        
        colors = COLOR_SCHEMES.get(theme_name, COLOR_SCHEMES["Default"])
        
        # Apply appropriate styling based on widget type
        widget_type = widget.winfo_class()
        
        if widget_type in ("Frame", "Toplevel", "Tk"):
            widget.configure(background=colors["background"])
            
        elif widget_type == "Label":
            widget.configure(
                background=colors["background"],
                foreground=colors["text"]
            )
            
        elif widget_type == "Button":
            widget.configure(
                background=colors["primary"],
                foreground="white",
                activebackground=colors["highlight"],
                activeforeground="white"
            )
            
        elif widget_type == "Entry":
            widget.configure(
                background="white",
                foreground=colors["text"],
                insertbackground=colors["text"]  # Cursor color
            )
            
        elif widget_type == "Text":
            widget.configure(
                background="white",
                foreground=colors["text"],
                insertbackground=colors["text"],  # Cursor color
                selectbackground=colors["primary"],
                selectforeground="white"
            )
            
        elif widget_type == "Canvas":
            widget.configure(background=colors["background"])
            
        elif widget_type == "Listbox":
            widget.configure(
                background="white",
                foreground=colors["text"],
                selectbackground=colors["primary"],
                selectforeground="white"
            )
            
        elif widget_type == "Menu":
            widget.configure(
                background=colors["background"],
                foreground=colors["text"],
                activebackground=colors["primary"],
                activeforeground="white"
            )
            
        # Add more widget types as needed
        
        logger.debug(f"Applied theme to {widget_type} widget")
        
    except Exception as e:
        logger.error(f"Error applying theme to widget: {e}")


def get_themed_icon_path(icon_name, theme_name=None):
    """
    Get the path to a themed icon.
    
    Args:
        icon_name (str): Name of the icon
        theme_name (str, optional): Theme to use. If None, uses current theme.
    
    Returns:
        str: Path to the icon file
    """
    try:
        # Determine theme
        if theme_name is None:
            theme_name = current_theme
        
        # Check if theme is dark
        is_dark = theme_name == "Dark" or (
            theme_name == "System" and detect_system_theme() == "Dark"
        )
        
        # Determine icon variant
        variant = "dark" if is_dark else "light"
        
        # Construct path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "resources", "icons", variant, f"{icon_name}.png")
        
        # Check if icon exists
        if not os.path.exists(icon_path):
            # Fall back to default icon
            icon_path = os.path.join(base_dir, "resources", "icons", f"{icon_name}.png")
            
            # If still doesn't exist, return None
            if not os.path.exists(icon_path):
                logger.warning(f"Icon not found: {icon_name}")
                return None
        
        return icon_path
        
    except Exception as e:
        logger.error(f"Error getting themed icon: {e}")
        return None


# Initialize module with default theme
def initialize():
    """Initialize the styles module with default settings."""
    global current_theme, current_font_size
    
    # Try to load saved preferences
    theme_name, font_size = load_theme_preferences()
    
    if theme_name:
        current_theme = theme_name
    
    if font_size:
        current_font_size = font_size
    
    # If using System theme, detect system theme
    if current_theme == "System":
        system_theme = detect_system_theme()
        if system_theme:
            # Update the System theme colors based on detected theme
            COLOR_SCHEMES["System"] = COLOR_SCHEMES[system_theme].copy()
    
    logger.info(f"Styles module initialized with theme: {current_theme}, font size: {current_font_size}")


# Initialize the module when imported
initialize()