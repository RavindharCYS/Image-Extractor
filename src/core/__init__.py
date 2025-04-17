"""
Image Metadata Extractor - Core Package

This package contains the core functionality for extracting and processing
image metadata. It provides the backend logic for the application.

Modules:
    - metadata_extractor: Main class for extracting metadata from images
    - file_handler: Handles file operations and format conversions
    - gps_parser: Parses and converts GPS coordinates
    - device_identifier: Identifies camera and device information
"""

import logging
import os
import sys
import importlib
import platform

# Setup package-level logger
logger = logging.getLogger(__name__)

# Core package version
__version__ = '1.0.0'

# Define what gets imported with "from src.core import *"
__all__ = [
    'MetadataExtractor',
    'FileHandler',
    'GPSParser',
    'DeviceIdentifier',
]

# Core constants
SUPPORTED_IMAGE_FORMATS = [
    '.jpg', '.jpeg', '.tiff', '.tif', '.png', '.bmp', 
    '.gif', '.webp', '.heic', '.heif', '.cr2', '.nef'
]

EXIF_DATE_FORMATS = [
    '%Y:%m:%d %H:%M:%S',
    '%Y-%m-%d %H:%M:%S',
    '%Y/%m/%d %H:%M:%S',
    '%Y:%m:%d',
    '%Y-%m-%d',
    '%Y/%m/%d'
]

# Check for required dependencies
REQUIRED_PACKAGES = {
    'PIL': 'Pillow',
    'exifread': 'exifread',
    'piexif': 'piexif',
    'hachoir': 'hachoir'
}

OPTIONAL_PACKAGES = {
    'geopy': 'geopy',
    'folium': 'folium',
    'pyheif': 'pyheif',
    'opencv': 'opencv-python'
}

# Track available packages
available_packages = {pkg: False for pkg in list(REQUIRED_PACKAGES.keys()) + list(OPTIONAL_PACKAGES.keys())}

def check_dependencies():
    """
    Check if required and optional dependencies are installed.
    
    Returns:
        tuple: (all_required_available, available_packages)
    """
    all_required_available = True
    
    # Check required packages
    for package, pip_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(package)
            available_packages[package] = True
            logger.debug(f"Required package available: {package}")
        except ImportError:
            all_required_available = False
            available_packages[package] = False
            logger.warning(f"Required package not available: {package} (pip install {pip_name})")
    
    # Check optional packages
    for package, pip_name in OPTIONAL_PACKAGES.items():
        try:
            importlib.import_module(package)
            available_packages[package] = True
            logger.debug(f"Optional package available: {package}")
        except ImportError:
            available_packages[package] = False
            logger.info(f"Optional package not available: {package} (pip install {pip_name})")
    
    return all_required_available, available_packages

# Check dependencies
all_required_available, available_packages = check_dependencies()

if not all_required_available:
    missing_packages = [f"{pip_name}" for pkg, pip_name in REQUIRED_PACKAGES.items() 
                       if not available_packages[pkg]]
    logger.warning(f"Missing required packages: {', '.join(missing_packages)}")
    logger.warning("Install missing packages with: pip install " + " ".join(missing_packages))

# Import core components
try:
    from .metadata_extractor import MetadataExtractor
    from .file_handler import FileHandler
    from .gps_parser import GPSParser
    from .device_identifier import DeviceIdentifier
except ImportError as e:
    logger.error(f"Error importing core components: {e}")
    # Define placeholder classes if imports fail
    
    class MetadataExtractor:
        """Placeholder for MetadataExtractor class."""
        def __init__(self):
            logger.error("MetadataExtractor module not available")
            raise ImportError("MetadataExtractor module not available")
    
    class FileHandler:
        """Placeholder for FileHandler class."""
        def __init__(self):
            logger.error("FileHandler module not available")
            raise ImportError("FileHandler module not available")
    
    class GPSParser:
        """Placeholder for GPSParser class."""
        def __init__(self):
            logger.error("GPSParser module not available")
            raise ImportError("GPSParser module not available")
    
    class DeviceIdentifier:
        """Placeholder for DeviceIdentifier class."""
        def __init__(self):
            logger.error("DeviceIdentifier module not available")
            raise ImportError("DeviceIdentifier module not available")

# System information
def get_system_info():
    """
    Get system information for debugging.
    
    Returns:
        dict: System information
    """
    info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'python_implementation': platform.python_implementation(),
        'system': platform.system(),
        'processor': platform.processor(),
        'available_packages': {k: v for k, v in available_packages.items()},
    }
    
    # Add PIL version if available
    if available_packages.get('PIL'):
        try:
            import PIL
            info['pil_version'] = PIL.__version__
        except:
            pass
    
    return info

# Log system information
system_info = get_system_info()
logger.debug(f"System information: {system_info}")

# Feature detection based on available packages
FEATURES = {
    'heic_support': available_packages.get('pyheif', False),
    'advanced_image_analysis': available_packages.get('opencv', False),
    'geolocation': available_packages.get('geopy', False),
    'mapping': available_packages.get('folium', False),
}

logger.debug(f"Available features: {FEATURES}")

# Metadata categories
METADATA_CATEGORIES = {
    'basic': 'Basic Information',
    'exif': 'EXIF Data',
    'gps': 'GPS Location',
    'device': 'Device Information',
    'file': 'File Information',
    'iptc': 'IPTC Data',
    'xmp': 'XMP Data',
    'icc': 'ICC Profile',
    'makernotes': 'Maker Notes',
}

# Sensitive metadata fields that might contain personal information
SENSITIVE_METADATA_FIELDS = [
    'GPS', 'Location', 'Latitude', 'Longitude',
    'SerialNumber', 'CameraSerialNumber', 'BodySerialNumber',
    'LensSerialNumber', 'InternalSerialNumber',
    'Owner', 'OwnerName', 'CameraOwner',
    'Artist', 'Author', 'Copyright',
    'Email', 'Address', 'Phone',
    'UserComment', 'Comment',
    'Software', 'HostComputer',
]

# Initialize core components
def initialize_core():
    """Initialize core components and return status."""
    status = {
        'all_dependencies_available': all_required_available,
        'available_packages': available_packages,
        'features': FEATURES,
    }
    
    logger.info("Core package initialized")
    return status

# Initialize when imported
core_status = initialize_core()