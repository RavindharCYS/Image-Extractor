"""
Image Metadata Extractor

A cybersecurity tool for extracting and analyzing metadata from images.
This package contains all the source code for the application.

Modules:
    - core: Core functionality for metadata extraction and analysis
    - gui: Graphical user interface components
    - utils: Utility functions and helpers
"""

__version__ = '1.0.0'
__author__ = 'Your Name'
__email__ = 'your.email@example.com'
__license__ = 'MIT'
__copyright__ = 'Copyright 2023'

# Package metadata
package_info = {
    'name': 'ImageMetadataExtractor',
    'version': __version__,
    'description': 'A tool for extracting and analyzing metadata from images',
    'author': __author__,
    'author_email': __email__,
    'license': __license__,
    'copyright': __copyright__,
    'url': 'https://github.com/yourusername/ImageMetadataExtractor',
}

# Import key components for easier access
from src.core.metadata_extractor import MetadataExtractor
from src.core.file_handler import FileHandler

# Define what gets imported with "from src import *"
__all__ = [
    'MetadataExtractor',
    'FileHandler',
    'package_info',
]

# Setup logging for the package
import logging
import os

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Configure package-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Prevent duplicate handlers
if not logger.handlers:
    # File handler
    file_handler = logging.FileHandler(os.path.join(logs_dir, 'image_metadata_extractor.log'))
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings and above to console
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

logger.info(f"Image Metadata Extractor v{__version__} initialized")

# Version check
import sys
if sys.version_info < (3, 6):
    logger.warning("This application requires Python 3.6 or higher")

# Check for required dependencies
try:
    import PIL
    import exifread
    import tkinter
except ImportError as e:
    logger.error(f"Required dependency not found: {e}")
    logger.error("Please install all required dependencies using: pip install -r requirements.txt")

# Application constants
APP_NAME = "Image Metadata Extractor"
DEFAULT_EXPORT_FORMATS = ['csv', 'json', 'txt', 'pdf']
SUPPORTED_IMAGE_FORMATS = [
    '.jpg', '.jpeg', '.tiff', '.tif', '.png', '.bmp', 
    '.gif', '.webp', '.heic', '.heif', '.cr2', '.nef'
]

# Initialize subpackages
from . import core
from . import gui
from . import utils