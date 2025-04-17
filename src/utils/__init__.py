"""
Image Metadata Extractor - Utils Package

This package contains utility functions and helper modules for the application.

Modules:
    - logger: Logging configuration and utilities
    - validators: Input validation functions
    - exporters: Export utilities for different formats
    - converters: Data conversion utilities
    - formatters: Text and data formatting utilities
"""

import logging
import os
import sys
import platform
from typing import Dict, Any, List, Optional, Union

# Setup package-level logger
logger = logging.getLogger(__name__)

# Utils package version
__version__ = '1.0.0'

# Define what gets imported with "from src.utils import *"
__all__ = [
    'setup_logging',
    'setup_exception_logging',
    'is_valid_image',
    'is_valid_path',
    'format_metadata_value',
    'get_system_info',
]

# Import utility functions
try:
    from .logger import setup_logging, setup_exception_logging
    from .validators import is_valid_image, is_valid_path, validate_output_directory
    from .formatters import format_metadata_value, format_file_size, format_timestamp
    from .converters import convert_coordinates, convert_timestamp
except ImportError as e:
    logger.error(f"Error importing utility modules: {e}")
    
    # Define placeholder functions if imports fail
    def setup_logging(*args, **kwargs):
        """Placeholder for setup_logging function."""
        print("Warning: logger module not available")
        return None
    
    def setup_exception_logging(*args, **kwargs):
        """Placeholder for setup_exception_logging function."""
        print("Warning: logger module not available")
        return None
    
    def is_valid_image(file_path):
        """Placeholder for is_valid_image function."""
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return False
        _, ext = os.path.splitext(file_path)
        return ext.lower() in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp']
    
    def is_valid_path(path):
        """Placeholder for is_valid_path function."""
        return os.path.exists(path)
    
    def format_metadata_value(value):
        """Placeholder for format_metadata_value function."""
        return str(value)


def get_system_info() -> Dict[str, Any]:
    """
    Get system information for debugging and reporting.
    
    Returns:
        Dictionary with system information
    """
    info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'python_implementation': platform.python_implementation(),
        'system': platform.system(),
        'processor': platform.processor(),
        'architecture': platform.architecture()[0],
    }
    
    # Add more detailed information
    if hasattr(os, 'cpu_count'):
        info['cpu_count'] = os.cpu_count()
    
    if hasattr(sys, 'getwindowsversion') and platform.system() == 'Windows':
        windows_version = sys.getwindowsversion()
        info['windows_version'] = {
            'major': windows_version.major,
            'minor': windows_version.minor,
            'build': windows_version.build,
            'platform': windows_version.platform,
            'service_pack': windows_version.service_pack
        }
    
    # Add memory information if psutil is available
    try:
        import psutil
        memory = psutil.virtual_memory()
        info['memory'] = {
            'total': format_size(memory.total),
            'available': format_size(memory.available),
            'percent_used': memory.percent
        }
        
        disk = psutil.disk_usage('/')
        info['disk'] = {
            'total': format_size(disk.total),
            'free': format_size(disk.free),
            'percent_used': disk.percent
        }
    except ImportError:
        pass
    
    # Add display information if available
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        info['display'] = {
            'width': root.winfo_screenwidth(),
            'height': root.winfo_screenheight(),
            'dpi': root.winfo_fpixels('1i')
        }
        root.destroy()
    except:
        pass
    
    return info


def format_size(size_bytes: int) -> str:
    """
    Format size in bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024 or unit == 'TB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024


def check_dependencies() -> Dict[str, bool]:
    """
    Check if optional dependencies are available.
    
    Returns:
        Dictionary with dependency availability
    """
    dependencies = {
        'PIL': False,
        'pandas': False,
        'reportlab': False,
        'yaml': False,
        'psutil': False,
        'geopy': False,
        'folium': False,
        'exifread': False,
        'piexif': False,
        'hachoir': False,
        'pyheif': False,
        'opencv': False,
    }
    
    # Check each dependency
    try:
        import PIL
        dependencies['PIL'] = True
    except ImportError:
        pass
    
    try:
        import pandas
        dependencies['pandas'] = True
    except ImportError:
        pass
    
    try:
        import reportlab
        dependencies['reportlab'] = True
    except ImportError:
        pass
    
    try:
        import yaml
        dependencies['yaml'] = True
    except ImportError:
        pass
    
    try:
        import psutil
        dependencies['psutil'] = True
    except ImportError:
        pass
    
    try:
        import geopy
        dependencies['geopy'] = True
    except ImportError:
        pass
    
    try:
        import folium
        dependencies['folium'] = True
    except ImportError:
        pass
    
    try:
        import exifread
        dependencies['exifread'] = True
    except ImportError:
        pass
    
    try:
        import piexif
        dependencies['piexif'] = True
    except ImportError:
        pass
    
    try:
        import hachoir
        dependencies['hachoir'] = True
    except ImportError:
        pass
    
    try:
        import pyheif
        dependencies['pyheif'] = True
    except ImportError:
        pass
    
    try:
        import cv2
        dependencies['opencv'] = True
    except ImportError:
        pass
    
    return dependencies


# Initialize the utils package
def initialize_utils():
    """Initialize the utils package."""
    # Check dependencies
    deps = check_dependencies()
    missing = [name for name, available in deps.items() if not available]
    
    if missing:
        logger.info(f"Optional dependencies not available: {', '.join(missing)}")
    
    # Log system information
    sys_info = get_system_info()
    logger.debug(f"System information: {sys_info}")
    
    # Setup default logging if not already configured
    if not logging.getLogger().handlers:
        setup_logging()
    
    logger.info("Utils package initialized")


# Initialize when imported
initialize_utils()