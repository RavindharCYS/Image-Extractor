"""
Metadata Extractor Module

This module provides the core functionality for extracting metadata from images.
It supports various image formats and extracts EXIF, IPTC, XMP, and other metadata.
"""

import os
import sys
import logging
import datetime
import json
import re
import traceback
from collections import OrderedDict
from typing import Dict, Any, List, Tuple, Optional, Union

# Get the package logger
logger = logging.getLogger(__name__)

# Import required libraries with error handling
try:
    from PIL import Image, ExifTags, TiffImagePlugin
    import exifread
    import piexif
    from fractions import Fraction
except ImportError as e:
    logger.error(f"Required library not available: {e}")
    raise ImportError(f"Required library not available: {e}. Please install all required dependencies.")

# Import optional libraries with fallbacks
try:
    import hachoir.parser
    import hachoir.metadata
    HACHOIR_AVAILABLE = True
except ImportError:
    logger.info("hachoir library not available. Some advanced metadata extraction will be limited.")
    HACHOIR_AVAILABLE = False

try:
    import pyheif
    HEIF_SUPPORT = True
except ImportError:
    logger.info("pyheif library not available. HEIC/HEIF image support will be limited.")
    HEIF_SUPPORT = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    logger.info("OpenCV library not available. Advanced image analysis will be limited.")
    OPENCV_AVAILABLE = False

# Import internal modules
try:
    from .gps_parser import GPSParser
    from .device_identifier import DeviceIdentifier
except ImportError as e:
    logger.warning(f"Internal module import error: {e}")
    # Create simple placeholder classes if imports fail
    class GPSParser:
        @staticmethod
        def parse_gps_info(exif_data):
            return {}
    
    class DeviceIdentifier:
        @staticmethod
        def identify_device(metadata):
            return {}


class MetadataExtractor:
    """
    A class for extracting metadata from image files.
    
    This class provides methods to extract various types of metadata from
    different image formats, including EXIF, IPTC, XMP, and file metadata.
    """
    
    def __init__(self):
        """Initialize the MetadataExtractor."""
        self.gps_parser = GPSParser()
        self.device_identifier = DeviceIdentifier()
        
        # Track supported formats
        self.supported_formats = {
            'JPEG': self._extract_jpeg_metadata,
            'TIFF': self._extract_tiff_metadata,
            'PNG': self._extract_png_metadata,
            'GIF': self._extract_gif_metadata,
            'BMP': self._extract_bmp_metadata,
            'WEBP': self._extract_webp_metadata,
        }
        
        # Add HEIC/HEIF support if available
        if HEIF_SUPPORT:
            self.supported_formats['HEIC'] = self._extract_heic_metadata
        
        logger.debug("MetadataExtractor initialized")
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from an image file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary containing extracted metadata
        
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is not a supported image format
            Exception: For other extraction errors
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not os.path.isfile(file_path):
            logger.error(f"Not a file: {file_path}")
            raise ValueError(f"Not a file: {file_path}")
        
        logger.info(f"Extracting metadata from: {file_path}")
        
        try:
            # Get basic file information
            file_info = self._get_file_info(file_path)
            
            # Determine file type and extract metadata
            metadata = self._extract_metadata_by_format(file_path)
            
            # Merge file info with extracted metadata
            metadata.update(file_info)
            
            # Extract device information
            device_info = self.device_identifier.identify_device(metadata)
            if device_info:
                metadata.update(device_info)
            
            # Process and clean metadata
            metadata = self._process_metadata(metadata)
            
            logger.info(f"Successfully extracted metadata from: {file_path}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            logger.debug(traceback.format_exc())
            raise
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            file_stat = os.stat(file_path)
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            
            file_info = {
                "FileName": file_name,
                "FilePath": file_path,
                "FileSize": file_stat.st_size,
                "FileSizeFormatted": self._format_file_size(file_stat.st_size),
                "FileExtension": file_ext,
                "FileModifyDate": datetime.datetime.fromtimestamp(file_stat.st_mtime),
                "FileAccessDate": datetime.datetime.fromtimestamp(file_stat.st_atime),
                "FileCreateDate": datetime.datetime.fromtimestamp(file_stat.st_ctime),
            }
            
            # Try to get MIME type if python-magic is available
            try:
                import magic
                mime = magic.Magic(mime=True)
                file_info["MIMEType"] = mime.from_file(file_path)
            except ImportError:
                # Fallback to basic MIME type detection
                mime_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.bmp': 'image/bmp',
                    '.tiff': 'image/tiff',
                    '.tif': 'image/tiff',
                    '.webp': 'image/webp',
                    '.heic': 'image/heic',
                    '.heif': 'image/heif',
                }
                file_info["MIMEType"] = mime_types.get(file_ext, 'application/octet-stream')
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {"FileName": os.path.basename(file_path), "FilePath": file_path}
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            Formatted file size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def _extract_metadata_by_format(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata based on the image format.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with extracted metadata
            
        Raises:
            ValueError: If the image format is not supported
        """
        try:
            # Try to open the image with PIL to determine format
            with Image.open(file_path) as img:
                format_name = img.format
                
                # Get basic image info
                basic_info = {
                    "ImageWidth": img.width,
                    "ImageHeight": img.height,
                    "ImageSize": f"{img.width} x {img.height}",
                    "ImageFormat": format_name,
                    "ImageMode": img.mode,
                    "ImageColorSpace": self._get_color_space(img),
                    "ImageBitsPerPixel": self._get_bits_per_pixel(img),
                }
                
                # Check if format is supported
                if format_name in self.supported_formats:
                    # Call the appropriate extraction method
                    metadata = self.supported_formats[format_name](file_path, img)
                    metadata.update(basic_info)
                    return metadata
                else:
                    logger.warning(f"Unsupported image format: {format_name}")
                    # Return basic info for unsupported formats
                    return basic_info
                
        except Exception as e:
            logger.error(f"Error determining image format: {e}")
            
            # Try using hachoir as a fallback
            if HACHOIR_AVAILABLE:
                try:
                    return self._extract_with_hachoir(file_path)
                except Exception as he:
                    logger.error(f"Hachoir extraction failed: {he}")
            
            # If all else fails, try to extract what we can
            return self._extract_fallback(file_path)
    
    def _get_color_space(self, img: Image.Image) -> str:
        """
        Determine the color space of an image.
        
        Args:
            img: PIL Image object
            
        Returns:
            Color space name
        """
        mode = img.mode
        if mode == "RGB":
            return "RGB"
        elif mode == "RGBA":
            return "RGB with Alpha"
        elif mode == "CMYK":
            return "CMYK"
        elif mode == "L":
            return "Grayscale"
        elif mode == "1":
            return "Bitmap"
        elif mode == "P":
            return "Palette"
        elif mode == "HSV":
            return "HSV"
        elif mode == "YCbCr":
            return "YCbCr"
        elif mode == "LAB":
            return "LAB"
        else:
            return mode
    
    def _get_bits_per_pixel(self, img: Image.Image) -> int:
        """
        Calculate bits per pixel for an image.
        
        Args:
            img: PIL Image object
            
        Returns:
            Bits per pixel
        """
        mode_to_bpp = {
            '1': 1,
            'L': 8,
            'P': 8,
            'RGB': 24,
            'RGBA': 32,
            'CMYK': 32,
            'YCbCr': 24,
            'LAB': 24,
            'HSV': 24,
            'I': 32,
            'F': 32,
        }
        return mode_to_bpp.get(img.mode, 0)
    
    def _extract_jpeg_metadata(self, file_path: str, img: Image.Image = None) -> Dict[str, Any]:
        """
        Extract metadata from JPEG images.
        
        Args:
            file_path: Path to the JPEG file
            img: Optional PIL Image object
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {}
        
        # Extract EXIF data using exifread
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=True)
                exif_data = self._process_exifread_tags(tags)
                metadata.update(exif_data)
        except Exception as e:
            logger.warning(f"Error extracting EXIF with exifread: {e}")
        
        # Extract EXIF data using PIL as backup
        try:
            if img is None:
                img = Image.open(file_path)
            
            if hasattr(img, '_getexif'):
                exif = img._getexif()
                if exif:
                    pil_exif = self._process_pil_exif(exif)
                    # Only add PIL EXIF data if we don't already have it from exifread
                    for key, value in pil_exif.items():
                        if key not in metadata:
                            metadata[key] = value
        except Exception as e:
            logger.warning(f"Error extracting EXIF with PIL: {e}")
        
        # Extract IPTC data
        try:
            iptc_data = self._extract_iptc(file_path)
            if iptc_data:
                metadata.update(iptc_data)
        except Exception as e:
            logger.warning(f"Error extracting IPTC data: {e}")
        
        # Extract XMP data
        try:
            xmp_data = self._extract_xmp(file_path)
            if xmp_data:
                metadata.update(xmp_data)
        except Exception as e:
            logger.warning(f"Error extracting XMP data: {e}")
        
        # Extract GPS information
        if any(key.startswith('GPS') for key in metadata.keys()):
            try:
                gps_info = self.gps_parser.parse_gps_info(metadata)
                if gps_info:
                    metadata.update(gps_info)
            except Exception as e:
                logger.warning(f"Error parsing GPS information: {e}")
        
        return metadata
    
    def _extract_tiff_metadata(self, file_path: str, img: Image.Image = None) -> Dict[str, Any]:
        """
        Extract metadata from TIFF images.
        
        Args:
            file_path: Path to the TIFF file
            img: Optional PIL Image object
            
        Returns:
            Dictionary with extracted metadata
        """
        # TIFF files use the same EXIF structure as JPEG
        metadata = self._extract_jpeg_metadata(file_path, img)
        
        # Add TIFF-specific metadata
        try:
            if img is None:
                img = Image.open(file_path)
            
            # Extract TIFF tags
            if isinstance(img, TiffImagePlugin.TiffImageFile):
                for tag, value in img.tag_v2.items():
                    tag_name = TiffImagePlugin.TAGS.get(tag, f"TIFF Tag {tag}")
                    metadata[tag_name] = value
        except Exception as e:
            logger.warning(f"Error extracting TIFF-specific metadata: {e}")
        
        return metadata
    
    def _extract_png_metadata(self, file_path: str, img: Image.Image = None) -> Dict[str, Any]:
        """
        Extract metadata from PNG images.
        
        Args:
            file_path: Path to the PNG file
            img: Optional PIL Image object
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {}
        
        try:
            if img is None:
                img = Image.open(file_path)
            
            # Extract PNG text chunks
            if hasattr(img, 'text') and img.text:
                for key, value in img.text.items():
                    metadata[f"PNG:{key}"] = value
            
            # Extract PNG info
            if hasattr(img, 'info') and img.info:
                for key, value in img.info.items():
                    if isinstance(value, (str, int, float, bool)):
                        metadata[f"PNG:{key}"] = value
        except Exception as e:
            logger.warning(f"Error extracting PNG metadata: {e}")
        
        # Try to extract XMP data
        try:
            xmp_data = self._extract_xmp(file_path)
            if xmp_data:
                metadata.update(xmp_data)
        except Exception as e:
            logger.warning(f"Error extracting XMP data from PNG: {e}")
        
        # Use hachoir as a fallback
        if HACHOIR_AVAILABLE and len(metadata) <= 1:
            try:
                hachoir_metadata = self._extract_with_hachoir(file_path)
                metadata.update(hachoir_metadata)
            except Exception as e:
                logger.warning(f"Error extracting PNG metadata with hachoir: {e}")
        
        return metadata
    
    def _extract_gif_metadata(self, file_path: str, img: Image.Image = None) -> Dict[str, Any]:
        """
        Extract metadata from GIF images.
        
        Args:
            file_path: Path to the GIF file
            img: Optional PIL Image object
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {}
        
        try:
            if img is None:
                img = Image.open(file_path)
            
            # Extract GIF info
            if hasattr(img, 'info') and img.info:
                for key, value in img.info.items():
                    if isinstance(value, (str, int, float, bool)):
                        metadata[f"GIF:{key}"] = value
            
            # Get animation info
            try:
                metadata["GIF:FrameCount"] = 0
                while True:
                    metadata["GIF:FrameCount"] += 1
                    img.seek(img.tell() + 1)
            except EOFError:
                pass  # End of frames
            
            # Reset position
            img.seek(0)
            
            # Get duration info
            if "duration" in img.info:
                metadata["GIF:Duration"] = img.info["duration"]
                if metadata.get("GIF:FrameCount", 0) > 1:
                    total_duration = metadata["GIF:Duration"] * metadata["GIF:FrameCount"]
                    metadata["GIF:TotalDuration"] = total_duration
                    metadata["GIF:TotalDurationFormatted"] = self._format_duration(total_duration)
            
            # Get loop info
            if "loop" in img.info:
                metadata["GIF:Loop"] = img.info["loop"]
            
            # Get background color
            if "background" in img.info:
                metadata["GIF:Background"] = img.info["background"]
            
            # Get transparency
            if "transparency" in img.info:
                metadata["GIF:Transparency"] = img.info["transparency"]
            
        except Exception as e:
            logger.warning(f"Error extracting GIF metadata: {e}")
        
        # Use hachoir as a fallback
        if HACHOIR_AVAILABLE and len(metadata) <= 1:
            try:
                hachoir_metadata = self._extract_with_hachoir(file_path)
                metadata.update(hachoir_metadata)
            except Exception as e:
                logger.warning(f"Error extracting GIF metadata with hachoir: {e}")
        
        return metadata
    
    def _extract_bmp_metadata(self, file_path: str, img: Image.Image = None) -> Dict[str, Any]:
        """
        Extract metadata from BMP images.
        
        Args:
            file_path: Path to the BMP file
            img: Optional PIL Image object
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {}
        
        try:
            if img is None:
                img = Image.open(file_path)
            
            # BMP files have limited metadata
            metadata["BMP:Format"] = "BMP"
            metadata["BMP:Compression"] = getattr(img, "compression", "Unknown")
            
            # Read BMP header manually to get more info
            with open(file_path, 'rb') as f:
                header = f.read(54)  # BMP header is 54 bytes
                
                if len(header) >= 54:
                    # Extract bits per pixel
                    bpp = int.from_bytes(header[28:30], byteorder='little')
                    metadata["BMP:BitsPerPixel"] = bpp
                    
                    # Extract compression type
                    compression = int.from_bytes(header[30:34], byteorder='little')
                    compression_types = {
                        0: "BI_RGB (None)",
                        1: "BI_RLE8",
                        2: "BI_RLE4",
                        3: "BI_BITFIELDS",
                        4: "BI_JPEG",
                        5: "BI_PNG"
                    }
                    metadata["BMP:CompressionType"] = compression_types.get(compression, f"Unknown ({compression})")
                    
                    # Extract image size in bytes
                    image_size = int.from_bytes(header[34:38], byteorder='little')
                    if image_size > 0:
                        metadata["BMP:ImageSizeBytes"] = image_size
                    
                    # Extract resolution
                    x_res = int.from_bytes(header[38:42], byteorder='little')
                    y_res = int.from_bytes(header[42:46], byteorder='little')
                    if x_res > 0 and y_res > 0:
                        metadata["BMP:HorizontalResolution"] = x_res
                        metadata["BMP:VerticalResolution"] = y_res
                        metadata["BMP:ResolutionUnit"] = "Pixels per meter"
        
        except Exception as e:
            logger.warning(f"Error extracting BMP metadata: {e}")
        
        # Use hachoir as a fallback
        if HACHOIR_AVAILABLE and len(metadata) <= 1:
            try:
                hachoir_metadata = self._extract_with_hachoir(file_path)
                metadata.update(hachoir_metadata)
            except Exception as e:
                logger.warning(f"Error extracting BMP metadata with hachoir: {e}")
        
        return metadata
    
    def _extract_webp_metadata(self, file_path: str, img: Image.Image = None) -> Dict[str, Any]:
        """
        Extract metadata from WebP images.
        
        Args:
            file_path: Path to the WebP file
            img: Optional PIL Image object
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {}
        
        try:
            if img is None:
                img = Image.open(file_path)
            
            # Extract WebP info
            if hasattr(img, 'info') and img.info:
                for key, value in img.info.items():
                    if isinstance(value, (str, int, float, bool)):
                        metadata[f"WebP:{key}"] = value
            
            # Check if animated
            is_animated = getattr(img, "is_animated", False)
            metadata["WebP:Animated"] = is_animated
            
            if is_animated:
                # Get animation info
                try:
                    metadata["WebP:FrameCount"] = getattr(img, "n_frames", 0)
                    
                    # Get duration info if available
                    if "duration" in img.info:
                        metadata["WebP:Duration"] = img.info["duration"]
                        if metadata.get("WebP:FrameCount", 0) > 1:
                            total_duration = metadata["WebP:Duration"] * metadata["WebP:FrameCount"]
                            metadata["WebP:TotalDuration"] = total_duration
                            metadata["WebP:TotalDurationFormatted"] = self._format_duration(total_duration)
                    
                    # Get loop info
                    if "loop" in img.info:
                        metadata["WebP:Loop"] = img.info["loop"]
                except Exception as e:
                    logger.warning(f"Error extracting WebP animation metadata: {e}")
            
            # Check for EXIF data
            if "exif" in img.info:
                try:
                    exif_data = img.info["exif"]
                    if exif_data:
                        exif = piexif.load(exif_data)
                        exif_metadata = self._process_piexif_data(exif)
                        metadata.update(exif_metadata)
                except Exception as e:
                    logger.warning(f"Error extracting WebP EXIF metadata: {e}")
            
            # Check for XMP data
            if "xmp" in img.info:
                try:
                    xmp_data = img.info["xmp"]
                    if xmp_data:
                        xmp_metadata = self._process_xmp_data(xmp_data)
                        metadata.update(xmp_metadata)
                except Exception as e:
                    logger.warning(f"Error extracting WebP XMP metadata: {e}")
            
        except Exception as e:
            logger.warning(f"Error extracting WebP metadata: {e}")
        
        # Use hachoir as a fallback
        if HACHOIR_AVAILABLE and len(metadata) <= 1:
            try:
                hachoir_metadata = self._extract_with_hachoir(file_path)
                metadata.update(hachoir_metadata)
            except Exception as e:
                logger.warning(f"Error extracting WebP metadata with hachoir: {e}")
        
        return metadata
    
    def _extract_heic_metadata(self, file_path: str, img: Image.Image = None) -> Dict[str, Any]:
        """
        Extract metadata from HEIC/HEIF images.
        
        Args:
            file_path: Path to the HEIC file
            img: Optional PIL Image object (not used for HEIC)
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {}
        
        if not HEIF_SUPPORT:
            logger.warning("pyheif library not available. Cannot extract HEIC metadata.")
            return metadata
        
        try:
            # Open HEIC file
            heif_file = pyheif.read(file_path)
            
            # Basic metadata
            metadata["HEIC:BitDepth"] = heif_file.bit_depth
            metadata["HEIC:Mode"] = heif_file.mode
            
            # Get image size
            if hasattr(heif_file, 'size'):
                metadata["ImageWidth"] = heif_file.size[0]
                metadata["ImageHeight"] = heif_file.size[1]
                metadata["ImageSize"] = f"{heif_file.size[0]} x {heif_file.size[1]}"
            
            # Extract EXIF data
            for metadata_type in heif_file.metadata or []:
                if metadata_type['type'] == 'Exif':
                    exif_data = metadata_type['data']
                    if exif_data:
                        # Skip first 4 bytes (TIFF header offset)
                        exif_data = exif_data[4:] if len(exif_data) > 4 else exif_data
                        try:
                            exif = piexif.load(exif_data)
                            exif_metadata = self._process_piexif_data(exif)
                            metadata.update(exif_metadata)
                        except Exception as e:
                            logger.warning(f"Error processing HEIC EXIF data: {e}")
                
                elif metadata_type['type'] == 'XMP':
                    xmp_data = metadata_type['data']
                    if xmp_data:
                        try:
                            xmp_metadata = self._process_xmp_data(xmp_data)
                            metadata.update(xmp_metadata)
                        except Exception as e:
                            logger.warning(f"Error processing HEIC XMP data: {e}")
            
        except Exception as e:
            logger.warning(f"Error extracting HEIC metadata: {e}")
        
        # Extract GPS information if available
        if any(key.startswith('GPS') for key in metadata.keys()):
            try:
                gps_info = self.gps_parser.parse_gps_info(metadata)
                if gps_info:
                    metadata.update(gps_info)
            except Exception as e:
                logger.warning(f"Error parsing GPS information from HEIC: {e}")
        
        return metadata
    
    def _extract_with_hachoir(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata using hachoir library.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with extracted metadata
        """
        if not HACHOIR_AVAILABLE:
            return {}
        
        metadata = {}
        
        try:
            parser = hachoir.parser.createParser(file_path)
            if not parser:
                return {}
            
            extractor = hachoir.metadata.extractMetadata(parser)
            if not extractor:
                return {}
            
            # Convert hachoir metadata to dictionary
            for key, values in extractor.items():
                for value in values:
                    # Clean up key name
                    clean_key = key.replace('/', ':').replace(' ', '')
                    
                    # Handle different value types
                    if value.unit:
                        metadata[clean_key] = f"{value.value} {value.unit}"
                    else:
                        metadata[clean_key] = value.value
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Hachoir extraction error: {e}")
            return {}
    
    def _extract_fallback(self, file_path: str) -> Dict[str, Any]:
        """
        Fallback method to extract basic metadata when other methods fail.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with basic metadata
        """
        metadata = {}
        
        try:
            # Try to open with PIL
            try:
                with Image.open(file_path) as img:
                    metadata["ImageWidth"] = img.width
                    metadata["ImageHeight"] = img.height
                    metadata["ImageSize"] = f"{img.width} x {img.height}"
                    metadata["ImageFormat"] = img.format or "Unknown"
                    metadata["ImageMode"] = img.mode
            except Exception as e:
                logger.warning(f"PIL fallback failed: {e}")
            
            # Try to get file info
            file_info = self._get_file_info(file_path)
            metadata.update(file_info)
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Fallback extraction failed: {e}")
            return {"Error": "Metadata extraction failed"}
    
    def _process_exifread_tags(self, tags: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process EXIF tags from exifread.
        
        Args:
            tags: Dictionary of EXIF tags from exifread
            
        Returns:
            Processed metadata dictionary
        """
        metadata = {}
        
        for tag, value in tags.items():
            # Skip thumbnail data
            if "thumbnail" in tag.lower():
                continue
            
            # Clean up tag name
            tag_parts = tag.split(" ")
            if len(tag_parts) > 1 and tag_parts[0] in ("EXIF", "Image", "GPS", "Interoperability"):
                tag_name = tag
            else:
                tag_name = tag.replace(" ", ":")
            
            # Process value based on type
            if isinstance(value, exifread.classes.IfdTag):
                # Handle different value types
                if value.field_type == 1:  # Byte
                    metadata[tag_name] = value.values
                elif value.field_type == 2:  # ASCII
                    text_value = str(value.values)
                    # Clean up text values
                    text_value = text_value.strip('\x00').strip()
                    if text_value:
                        metadata[tag_name] = text_value
                elif value.field_type == 3:  # Short
                    metadata[tag_name] = value.values
                elif value.field_type == 4:  # Long
                    metadata[tag_name] = value.values
                elif value.field_type == 5:  # Rational
                    # Handle rational values
                    if len(value.values) == 1:
                        rational = value.values[0]
                        if rational.denominator == 1:
                            metadata[tag_name] = rational.numerator
                        else:
                            metadata[tag_name] = float(rational.numerator) / rational.denominator
                    else:
                        metadata[tag_name] = [float(v.numerator) / v.denominator if v.denominator != 0 else 0 
                                             for v in value.values]
                elif value.field_type == 7:  # Undefined
                    # Skip binary data
                    if len(value.values) < 100:  # Only include small binary data
                        metadata[tag_name] = value.values
                elif value.field_type == 9:  # SLong
                    metadata[tag_name] = value.values
                elif value.field_type == 10:  # SRational
                    # Handle signed rational values
                    if len(value.values) == 1:
                        rational = value.values[0]
                        if rational.denominator == 1:
                            metadata[tag_name] = rational.numerator
                        else:
                            metadata[tag_name] = float(rational.numerator) / rational.denominator
                    else:
                        metadata[tag_name] = [float(v.numerator) / v.denominator if v.denominator != 0 else 0 
                                             for v in value.values]
                else:
                    # Default handling
                    metadata[tag_name] = value.values
            else:
                # Handle non-IfdTag values
                metadata[tag_name] = str(value)
        
        return metadata
    
    def _process_pil_exif(self, exif: Dict[int, Any]) -> Dict[str, Any]:
        """
        Process EXIF data from PIL.
        
        Args:
            exif: EXIF data from PIL
            
        Returns:
            Processed metadata dictionary
        """
        metadata = {}
        
        for tag_id, value in exif.items():
            # Get tag name
            tag_name = ExifTags.TAGS.get(tag_id, f"Unknown Tag {tag_id}")
            
            # Skip thumbnail data
            if "thumbnail" in tag_name.lower():
                continue
            
            # Process value based on type
            if isinstance(value, bytes):
                # Try to decode as string
                try:
                    text_value = value.decode('utf-8').strip('\x00').strip()
                    if text_value:
                        metadata[tag_name] = text_value
                except UnicodeDecodeError:
                    # Skip binary data
                    pass
            elif isinstance(value, tuple) and len(value) == 1:
                # Single value tuple
                metadata[tag_name] = value[0]
            elif isinstance(value, tuple) and all(isinstance(x, int) for x in value):
                # Tuple of integers (like version numbers)
                metadata[tag_name] = '.'.join(str(x) for x in value)
            elif isinstance(value, tuple) and len(value) == 2 and all(isinstance(x, int) for x in value):
                # Rational number
                if value[1] == 0:
                    metadata[tag_name] = 0  # Avoid division by zero
                elif value[1] == 1:
                    metadata[tag_name] = value[0]  # Integer value
                else:
                    metadata[tag_name] = float(value[0]) / value[1]  # Floating point
            else:
                # Default handling
                metadata[tag_name] = value
        
        return metadata
    
    def _process_piexif_data(self, exif_dict: Dict[str, Dict[int, Any]]) -> Dict[str, Any]:
        """
        Process EXIF data from piexif.
        
        Args:
            exif_dict: EXIF dictionary from piexif
            
        Returns:
            Processed metadata dictionary
        """
        metadata = {}
        
        # Process each IFD (Image File Directory)
        for ifd_name, ifd in exif_dict.items():
            if ifd_name == 'thumbnail':
                continue  # Skip thumbnail data
            
            # Get prefix based on IFD
            if ifd_name == '0th':
                prefix = "Image"
            elif ifd_name == '1st':
                prefix = "Thumbnail"
            elif ifd_name == 'Exif':
                prefix = "EXIF"
            elif ifd_name == 'GPS':
                prefix = "GPS"
            elif ifd_name == 'Interop':
                prefix = "Interoperability"
            else:
                prefix = ifd_name
            
            # Process tags in this IFD
            for tag_id, value in ifd.items():
                # Get tag name based on IFD
                if ifd_name == '0th':
                    tag_name = piexif.ImageIFD.get(tag_id, tag_id)
                elif ifd_name == '1st':
                    tag_name = piexif.ImageIFD.get(tag_id, tag_id)  # Same as 0th
                elif ifd_name == 'Exif':
                    tag_name = piexif.ExifIFD.get(tag_id, tag_id)
                elif ifd_name == 'GPS':
                    tag_name = piexif.GPSIFD.get(tag_id, tag_id)
                elif ifd_name == 'Interop':
                    tag_name = piexif.InteropIFD.get(tag_id, tag_id)
                else:
                    tag_name = str(tag_id)
                
                # Format tag name
                if isinstance(tag_name, int):
                    tag_name = f"Unknown Tag {tag_name}"
                
                full_tag_name = f"{prefix}:{tag_name}"
                
                # Process value based on type
                if isinstance(value, bytes):
                    # Try to decode as string
                    try:
                        text_value = value.decode('utf-8').strip('\x00').strip()
                        if text_value:
                            metadata[full_tag_name] = text_value
                    except UnicodeDecodeError:
                        try:
                            # Try other encodings
                            text_value = value.decode('latin-1').strip('\x00').strip()
                            if text_value:
                                metadata[full_tag_name] = text_value
                        except:
                            # Skip binary data
                            pass
                elif isinstance(value, tuple) and len(value) == 2 and all(isinstance(x, int) for x in value):
                    # Rational number
                    if value[1] == 0:
                        metadata[full_tag_name] = 0  # Avoid division by zero
                    elif value[1] == 1:
                        metadata[full_tag_name] = value[0]  # Integer value
                    else:
                        metadata[full_tag_name] = float(value[0]) / value[1]  # Floating point
                elif isinstance(value, list) and all(isinstance(x, tuple) and len(x) == 2 for x in value):
                    # List of rational numbers
                    metadata[full_tag_name] = [
                        (0 if x[1] == 0 else 
                         x[0] if x[1] == 1 else 
                         float(x[0]) / x[1])
                        for x in value
                    ]
                else:
                    # Default handling
                    metadata[full_tag_name] = value
        
        return metadata
    
    def _extract_iptc(self, file_path: str) -> Dict[str, Any]:
        """
        Extract IPTC metadata from an image.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with IPTC metadata
        """
        metadata = {}
        
        try:
            # Try to extract IPTC data using PIL
            with Image.open(file_path) as img:
                if hasattr(img, 'info') and 'iptc' in img.info:
                    iptc_data = img.info['iptc']
                    # Process IPTC data
                    # This is a simplified implementation
                    # A full implementation would parse the IPTC binary data
                    metadata["IPTC:Data"] = "IPTC data present (not parsed)"
            
            # If we have iptcinfo3 library, use it for better IPTC extraction
            try:
                import iptcinfo3
                info = iptcinfo3.IPTCInfo(file_path)
                
                # Map common IPTC tags
                iptc_mapping = {
                    'object_name': 'Title',
                    'edit_status': 'EditStatus',
                    'urgency': 'Urgency',
                    'category': 'Category',
                    'supplemental_category': 'SupplementalCategory',
                    'fixture_identifier': 'FixtureIdentifier',
                    'keywords': 'Keywords',
                    'content_location_code': 'LocationCode',
                    'content_location_name': 'LocationName',
                    'release_date': 'ReleaseDate',
                    'release_time': 'ReleaseTime',
                    'expiration_date': 'ExpirationDate',
                    'expiration_time': 'ExpirationTime',
                    'special_instructions': 'Instructions',
                    'action_advised': 'ActionAdvised',
                    'reference_service': 'ReferenceService',
                    'reference_date': 'ReferenceDate',
                    'reference_number': 'ReferenceNumber',
                    'date_created': 'DateCreated',
                    'time_created': 'TimeCreated',
                    'digital_creation_date': 'DigitalCreationDate',
                    'digital_creation_time': 'DigitalCreationTime',
                    'originating_program': 'OriginatingProgram',
                    'program_version': 'ProgramVersion',
                    'object_cycle': 'ObjectCycle',
                    'byline': 'Creator',
                    'byline_title': 'CreatorJobTitle',
                    'city': 'City',
                    'sub_location': 'Sublocation',
                    'province_state': 'ProvinceState',
                    'country_code': 'CountryCode',
                    'country_name': 'Country',
                    'original_transmission_reference': 'TransmissionReference',
                    'headline': 'Headline',
                    'credit': 'Credit',
                    'source': 'Source',
                    'copyright_notice': 'Copyright',
                    'contact': 'Contact',
                    'caption_abstract': 'Description',
                    'writer_editor': 'CaptionWriter',
                    'image_type': 'ImageType',
                    'image_orientation': 'ImageOrientation',
                    'language_identifier': 'LanguageIdentifier'
                }
                
                # Extract mapped IPTC data
                for iptc_key, metadata_key in iptc_mapping.items():
                    if hasattr(info, iptc_key) and getattr(info, iptc_key):
                        value = getattr(info, iptc_key)
                        if value:
                            metadata[f"IPTC:{metadata_key}"] = value
                
                # Get any other available data
                for key in info.data:
                    if isinstance(key, int) and key not in [k for k in info._data_types]:
                        continue  # Skip unknown tags
                    
                    value = info[key]
                    if value and key not in iptc_mapping:
                        # Format key name
                        if isinstance(key, str):
                            metadata[f"IPTC:{key.capitalize()}"] = value
                        else:
                            metadata[f"IPTC:Tag{key}"] = value
            
            except ImportError:
                logger.debug("iptcinfo3 library not available for detailed IPTC extraction")
            except Exception as e:
                logger.warning(f"Error extracting IPTC data with iptcinfo3: {e}")
        
        except Exception as e:
            logger.warning(f"Error extracting IPTC data: {e}")
        
        return metadata
    
    def _extract_xmp(self, file_path: str) -> Dict[str, Any]:
        """
        Extract XMP metadata from an image.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with XMP metadata
        """
        metadata = {}
        
        try:
            # Try to extract XMP data using PIL
            with Image.open(file_path) as img:
                if hasattr(img, 'info') and 'xmp' in img.info:
                    xmp_data = img.info['xmp']
                    if xmp_data:
                        xmp_metadata = self._process_xmp_data(xmp_data)
                        metadata.update(xmp_metadata)
            
            # If no XMP data found with PIL, try reading the file directly
            if not metadata:
                with open(file_path, 'rb') as f:
                    data = f.read()
                    
                    # Look for XMP packet
                    xmp_start = b'<x:xmpmeta'
                    xmp_end = b'</x:xmpmeta>'
                    
                    start_idx = data.find(xmp_start)
                    if start_idx != -1:
                        end_idx = data.find(xmp_end, start_idx)
                        if end_idx != -1:
                            # Extract XMP packet
                            xmp_packet = data[start_idx:end_idx + len(xmp_end)]
                            xmp_metadata = self._process_xmp_data(xmp_packet)
                            metadata.update(xmp_metadata)
        
        except Exception as e:
            logger.warning(f"Error extracting XMP data: {e}")
        
        return metadata
    
    def _process_xmp_data(self, xmp_data: Union[bytes, str]) -> Dict[str, Any]:
        """
        Process XMP data.
        
        Args:
            xmp_data: XMP data as bytes or string
            
        Returns:
            Dictionary with XMP metadata
        """
        metadata = {}
        
        try:
            # Convert bytes to string if needed
            if isinstance(xmp_data, bytes):
                try:
                    xmp_str = xmp_data.decode('utf-8')
                except UnicodeDecodeError:
                    xmp_str = xmp_data.decode('latin-1')
            else:
                xmp_str = xmp_data
            
            # Simple regex-based extraction
            # This is a simplified implementation
            # A full implementation would use an XML parser
            
            # Extract Dublin Core elements
            dc_elements = {
                'dc:title': 'XMP:Title',
                'dc:creator': 'XMP:Creator',
                'dc:description': 'XMP:Description',
                'dc:subject': 'XMP:Subject',
                'dc:publisher': 'XMP:Publisher',
                'dc:contributor': 'XMP:Contributor',
                'dc:date': 'XMP:Date',
                'dc:type': 'XMP:Type',
                'dc:format': 'XMP:Format',
                'dc:identifier': 'XMP:Identifier',
                'dc:source': 'XMP:Source',
                'dc:language': 'XMP:Language',
                'dc:relation': 'XMP:Relation',
                'dc:coverage': 'XMP:Coverage',
                'dc:rights': 'XMP:Rights'
            }
            
            for element, key in dc_elements.items():
                pattern = f'<{element}>(.*?)</{element}>'
                matches = re.findall(pattern, xmp_str, re.DOTALL)
                if matches:
                    metadata[key] = matches[0].strip()
            
            # Extract XMP basic elements
            xmp_elements = {
                'xmp:CreateDate': 'XMP:CreateDate',
                'xmp:ModifyDate': 'XMP:ModifyDate',
                'xmp:CreatorTool': 'XMP:CreatorTool',
                'xmp:Label': 'XMP:Label',
                'xmp:Rating': 'XMP:Rating'
            }
            
            for element, key in xmp_elements.items():
                pattern = f'<{element}>(.*?)</{element}>'
                matches = re.findall(pattern, xmp_str, re.DOTALL)
                if matches:
                    metadata[key] = matches[0].strip()
            
            # Extract photoshop elements
            photoshop_elements = {
                'photoshop:AuthorsPosition': 'XMP:AuthorsPosition',
                'photoshop:CaptionWriter': 'XMP:CaptionWriter',
                'photoshop:Category': 'XMP:Category',
                'photoshop:City': 'XMP:City',
                'photoshop:Country': 'XMP:Country',
                'photoshop:Credit': 'XMP:Credit',
                'photoshop:DateCreated': 'XMP:DateCreated',
                'photoshop:Headline': 'XMP:Headline',
                'photoshop:Instructions': 'XMP:Instructions',
                'photoshop:Source': 'XMP:Source',
                'photoshop:State': 'XMP:State',
                'photoshop:TransmissionReference': 'XMP:TransmissionReference'
            }
            
            for element, key in photoshop_elements.items():
                pattern = f'<{element}>(.*?)</{element}>'
                matches = re.findall(pattern, xmp_str, re.DOTALL)
                if matches:
                    metadata[key] = matches[0].strip()
            
            # Extract GPS coordinates if available
            gps_elements = {
                'exif:GPSLatitude': 'XMP:GPSLatitude',
                'exif:GPSLongitude': 'XMP:GPSLongitude',
                'exif:GPSAltitude': 'XMP:GPSAltitude'
            }
            
            for element, key in gps_elements.items():
                pattern = f'<{element}>(.*?)</{element}>'
                matches = re.findall(pattern, xmp_str, re.DOTALL)
                if matches:
                    metadata[key] = matches[0].strip()
        
        except Exception as e:
            logger.warning(f"Error processing XMP data: {e}")
        
        return metadata
    
    def _format_duration(self, milliseconds: int) -> str:
        """
        Format duration in milliseconds to a human-readable string.
        
        Args:
            milliseconds: Duration in milliseconds
            
        Returns:
            Formatted duration string
        """
        seconds = milliseconds / 1000
        
        if seconds < 1:
            return f"{milliseconds} ms"
        elif seconds < 60:
            return f"{seconds:.1f} seconds"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes} min {int(remaining_seconds)} sec"
    
    def _process_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and clean the extracted metadata.
        
        Args:
            metadata: Raw metadata dictionary
            
        Returns:
            Processed metadata dictionary
        """
        processed = {}
        
        # Convert all keys to strings and clean values
        for key, value in metadata.items():
            # Skip None values and empty strings
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            
            # Convert key to string
            str_key = str(key)
            
            # Clean up value based on type
            if isinstance(value, bytes):
                try:
                    # Try to decode as UTF-8
                    str_value = value.decode('utf-8').strip('\x00').strip()
                    if str_value:
                        processed[str_key] = str_value
                except UnicodeDecodeError:
                    # Skip binary data
                    pass
            elif isinstance(value, datetime.datetime):
                # Format datetime objects
                processed[str_key] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, (list, tuple)):
                # Handle lists and tuples
                if len(value) == 0:
                    continue  # Skip empty lists
                elif len(value) == 1:
                    # Single item lists
                    processed[str_key] = self._clean_value(value[0])
                else:
                    # Convert all items in the list
                    cleaned_list = [self._clean_value(item) for item in value]
                    # Filter out None values
                    cleaned_list = [item for item in cleaned_list if item is not None]
                    if cleaned_list:
                        processed[str_key] = cleaned_list
            else:
                # Handle other types
                cleaned = self._clean_value(value)
                if cleaned is not None:
                    processed[str_key] = cleaned
        
        # Add derived metadata
        processed = self._add_derived_metadata(processed)
        
        # Sort metadata by keys
        return OrderedDict(sorted(processed.items()))
    
    def _clean_value(self, value: Any) -> Any:
        """
        Clean a metadata value.
        
        Args:
            value: Value to clean
            
        Returns:
            Cleaned value or None if the value should be skipped
        """
        if value is None:
            return None
        
        if isinstance(value, (int, float, bool)):
            return value
        
        if isinstance(value, (bytes, bytearray)):
            try:
                # Try to decode as UTF-8
                str_value = value.decode('utf-8').strip('\x00').strip()
                if str_value:
                    return str_value
                return None
            except UnicodeDecodeError:
                # Skip binary data
                return None
        
        if isinstance(value, str):
            # Clean up string
            cleaned = value.strip('\x00').strip()
            if not cleaned:
                return None
            return cleaned
        
        if isinstance(value, (list, tuple)):
            # Clean each item in the list
            cleaned_list = [self._clean_value(item) for item in value]
            # Filter out None values
            cleaned_list = [item for item in cleaned_list if item is not None]
            if not cleaned_list:
                return None
            if len(cleaned_list) == 1:
                return cleaned_list[0]
            return cleaned_list
        
        if isinstance(value, dict):
            # Clean each item in the dictionary
            cleaned_dict = {}
            for k, v in value.items():
                cleaned_v = self._clean_value(v)
                if cleaned_v is not None:
                    cleaned_dict[k] = cleaned_v
            if not cleaned_dict:
                return None
            return cleaned_dict
        
        if isinstance(value, datetime.datetime):
            # Format datetime objects
            return value.strftime('%Y-%m-%d %H:%M:%S')
        
        if isinstance(value, Fraction):
            # Convert fractions to float
            if value.denominator == 0:
                return 0
            if value.denominator == 1:
                return value.numerator
            return float(value.numerator) / value.denominator
        
        # For other types, convert to string
        try:
            return str(value)
        except:
            return None
    
    def _add_derived_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add derived metadata fields.
        
        Args:
            metadata: Processed metadata dictionary
            
        Returns:
            Metadata dictionary with derived fields
        """
        # Make a copy to avoid modifying the original
        result = metadata.copy()
        
        # Add aspect ratio if width and height are available
        if "ImageWidth" in result and "ImageHeight" in result:
            try:
                width = float(result["ImageWidth"])
                height = float(result["ImageHeight"])
                if width > 0 and height > 0:
                    aspect_ratio = width / height
                    result["AspectRatio"] = round(aspect_ratio, 3)
                    
                    # Add common aspect ratio name
                    common_ratios = {
                        1.0: "1:1 (Square)",
                        1.33: "4:3",
                        1.5: "3:2",
                        1.78: "16:9",
                        1.85: "1.85:1 (Cinema)",
                        2.35: "2.35:1 (Cinemascope)",
                        0.75: "3:4 (Portrait)",
                        0.67: "2:3 (Portrait)",
                        0.56: "9:16 (Portrait)"
                    }
                    
                    # Find the closest common ratio
                    closest_ratio = min(common_ratios.keys(), key=lambda x: abs(x - aspect_ratio))
                    if abs(closest_ratio - aspect_ratio) < 0.05:  # Within 5% tolerance
                        result["AspectRatioName"] = common_ratios[closest_ratio]
            except (ValueError, TypeError):
                pass
        
        # Add megapixels if width and height are available
        if "ImageWidth" in result and "ImageHeight" in result:
            try:
                width = float(result["ImageWidth"])
                height = float(result["ImageHeight"])
                if width > 0 and height > 0:
                    megapixels = (width * height) / 1000000
                    result["Megapixels"] = round(megapixels, 2)
            except (ValueError, TypeError):
                pass
        
        # Add formatted date fields
        date_fields = [
            ("DateTimeOriginal", "DateTaken"),
            ("CreateDate", "DateCreated"),
            ("ModifyDate", "DateModified")
        ]
        
        for source_field, target_field in date_fields:
            if source_field in result and target_field not in result:
                try:
                    # Try to parse the date string
                    date_str = result[source_field]
                    for date_format in [
                        '%Y:%m:%d %H:%M:%S',
                        '%Y-%m-%d %H:%M:%S',
                        '%Y/%m/%d %H:%M:%S',
                        '%Y:%m:%d',
                        '%Y-%m-%d',
                        '%Y/%m/%d'
                    ]:
                        try:
                            date_obj = datetime.datetime.strptime(date_str, date_format)
                            result[target_field] = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                            break
                        except ValueError:
                            continue
                except:
                    pass
        
        # Add camera model info
        camera_fields = ["Make", "Model", "Software"]
        camera_info = []
        
        for field in camera_fields:
            if field in result:
                camera_info.append(result[field])
        
        if camera_info:
            result["CameraInfo"] = " - ".join(camera_info)
        
        # Add exposure info
        exposure_fields = {
            "FNumber": "F-Stop",
            "ExposureTime": "Exposure Time",
            "ISOSpeedRatings": "ISO",
            "FocalLength": "Focal Length"
        }
        
        exposure_info = []
        
        for source_field, label in exposure_fields.items():
            if source_field in result:
                value = result[source_field]
                
                # Format specific fields
                if source_field == "FNumber":
                    if isinstance(value, (int, float)):
                        value = f"f/{value}"
                elif source_field == "ExposureTime":
                    if isinstance(value, (int, float)):
                        if value < 1:
                            # Convert to fraction (e.g., 0.5 -> 1/2)
                            denominator = round(1 / value)
                            value = f"1/{denominator}s"
                        else:
                            value = f"{value}s"
                elif source_field == "FocalLength":
                    if isinstance(value, (int, float)):
                        value = f"{value}mm"
                
                exposure_info.append(f"{label}: {value}")
        
        if exposure_info:
            result["ExposureInfo"] = ", ".join(exposure_info)
        
        return result
    
    def clean_metadata(self, input_file: str, output_file: str, **options) -> bool:
        """
        Clean metadata from an image file.
        
        Args:
            input_file: Path to the input image file
            output_file: Path to save the cleaned image
            **options: Cleaning options
                - remove_exif: Remove EXIF data
                - remove_gps: Remove GPS data
                - remove_iptc: Remove IPTC data
                - remove_xmp: Remove XMP data
                - remove_comments: Remove comments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Set default options
            remove_exif = options.get('remove_exif', True)
            remove_gps = options.get('remove_gps', True)
            remove_iptc = options.get('remove_iptc', False)
            remove_xmp = options.get('remove_xmp', False)
            remove_comments = options.get('remove_comments', False)
            
            # Open the image
            img = Image.open(input_file)
            
            # Create a new image with the same content but without metadata
            if remove_exif and remove_gps and remove_iptc and remove_xmp and remove_comments:
                # Remove all metadata
                data = list(img.getdata())
                img_without_metadata = Image.new(img.mode, img.size)
                img_without_metadata.putdata(data)
                img_without_metadata.save(output_file)
                logger.info(f"Removed all metadata from {input_file} and saved to {output_file}")
                return True
            
            # Selectively remove metadata
            if img.format == 'JPEG':
                # For JPEG, use piexif to selectively remove metadata
                try:
                    # Extract existing EXIF data
                    exif_dict = piexif.load(img.info.get('exif', b''))
                    
                    # Remove GPS data if requested
                    if remove_gps and 'GPS' in exif_dict:
                        del exif_dict['GPS']
                    
                    # Remove EXIF data if requested
                    if remove_exif and 'Exif' in exif_dict:
                        del exif_dict['Exif']
                    
                    # Remove other IFDs if requested
                    if remove_exif:
                        if '0th' in exif_dict:
                            del exif_dict['0th']
                        if '1st' in exif_dict:
                            del exif_dict['1st']
                        if 'Interop' in exif_dict:
                            del exif_dict['Interop']
                    
                    # Prepare new EXIF data
                    if any(exif_dict.values()):
                        exif_bytes = piexif.dump(exif_dict)
                    else:
                        exif_bytes = None
                    
                    # Prepare save parameters
                    params = {}
                    if exif_bytes:
                        params['exif'] = exif_bytes
                    
                    # Keep IPTC data if not removing it
                    if not remove_iptc and 'iptc' in img.info:
                        params['iptc'] = img.info['iptc']
                    
                    # Keep XMP data if not removing it
                    if not remove_xmp and 'xmp' in img.info:
                        params['xmp'] = img.info['xmp']
                    
                    # Keep comments if not removing them
                    if not remove_comments and 'comment' in img.info:
                        params['comment'] = img.info['comment']
                    
                    # Save the image with selected metadata
                    img.save(output_file, **params)
                    logger.info(f"Selectively removed metadata from {input_file} and saved to {output_file}")
                    return True
                    
                except Exception as e:
                    logger.error(f"Error selectively removing metadata: {e}")
                    # Fall back to removing all metadata
                    data = list(img.getdata())
                    img_without_metadata = Image.new(img.mode, img.size)
                    img_without_metadata.putdata(data)
                    img_without_metadata.save(output_file)
                    logger.info(f"Removed all metadata from {input_file} and saved to {output_file}")
                    return True
            else:
                # For other formats, create a new image without metadata
                data = list(img.getdata())
                img_without_metadata = Image.new(img.mode, img.size)
                img_without_metadata.putdata(data)
                img_without_metadata.save(output_file)
                logger.info(f"Removed all metadata from {input_file} and saved to {output_file}")
                return True
                
        except Exception as e:
            logger.error(f"Error cleaning metadata: {e}")
            return False
    
    def analyze_image(self, file_path: str) -> Dict[str, Any]:
        """
        Perform advanced analysis on an image.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with analysis results
        """
        if not OPENCV_AVAILABLE:
            logger.warning("OpenCV not available. Advanced image analysis is limited.")
            return {"Error": "OpenCV not available for advanced analysis"}
        
        try:
            # Extract basic metadata first
            metadata = self.extract(file_path)
            
            # Load image with OpenCV
            img = cv2.imread(file_path)
            if img is None:
                return {"Error": "Failed to load image with OpenCV"}
            
            # Get image dimensions
            height, width, channels = img.shape
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Calculate histogram
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = [float(h[0]) for h in hist]
            
            # Calculate basic statistics
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(gray)
            mean, stddev = cv2.meanStdDev(gray)
            
            # Detect edges
            edges = cv2.Canny(gray, 100, 200)
            edge_count = cv2.countNonZero(edges)
            edge_percentage = (edge_count / (width * height)) * 100
            
            # Detect faces if possible
            face_count = 0
            try:
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                face_count = len(faces)
            except Exception as e:
                logger.warning(f"Face detection failed: {e}")
            
            # Add analysis results to metadata
            analysis = {
                "Analysis:MinimumPixelValue": int(min_val),
                "Analysis:MaximumPixelValue": int(max_val),
                "Analysis:MeanPixelValue": float(mean[0][0]),
                "Analysis:StdDevPixelValue": float(stddev[0][0]),
                "Analysis:EdgePercentage": round(edge_percentage, 2),
                "Analysis:DetectedFaces": face_count,
                "Analysis:Histogram": hist,  # This might be too large for display
                "Analysis:HistogramPeaks": self._find_histogram_peaks(hist),
                "Analysis:ImageComplexity": self._calculate_image_complexity(gray),
                "Analysis:IsDark": float(mean[0][0]) < 85,
                "Analysis:IsLight": float(mean[0][0]) > 170,
                "Analysis:IsLowContrast": float(stddev[0][0]) < 40,
                "Analysis:IsHighContrast": float(stddev[0][0]) > 100,
                "Analysis:DominantColors": self._extract_dominant_colors(img),
                "Analysis:BlurScore": self._calculate_blur_score(gray),
                "Analysis:IsBlurry": self._is_image_blurry(gray),
                "Analysis:NoiseLevel": self._estimate_noise_level(gray)
            }
            
            # Add analysis to metadata
            metadata.update(analysis)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            logger.debug(traceback.format_exc())
            return {"Error": f"Image analysis failed: {str(e)}"}
    
    def _find_histogram_peaks(self, histogram: List[float]) -> List[int]:
        """
        Find peaks in the histogram.
        
        Args:
            histogram: Image histogram
            
        Returns:
            List of peak positions
        """
        peaks = []
        for i in range(1, len(histogram) - 1):
            if histogram[i] > histogram[i-1] and histogram[i] > histogram[i+1]:
                # Only consider significant peaks
                if histogram[i] > sum(histogram) / (len(histogram) * 2):
                    peaks.append(i)
        
        # Limit to top 5 peaks
        if len(peaks) > 5:
            peaks.sort(key=lambda p: histogram[p], reverse=True)
            peaks = peaks[:5]
        
        return sorted(peaks)
    
    def _calculate_image_complexity(self, gray_img) -> float:
        """
        Calculate image complexity based on edge density.
        
        Args:
            gray_img: Grayscale image
            
        Returns:
            Complexity score (0-100)
        """
        # Use Sobel operator to detect edges
        sobelx = cv2.Sobel(gray_img, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray_img, cv2.CV_64F, 0, 1, ksize=3)
        
        # Combine horizontal and vertical edges
        sobel = cv2.magnitude(sobelx, sobely)
        
        # Calculate mean edge strength
        mean_edge = cv2.mean(sobel)[0]
        
        # Normalize to 0-100 scale
        complexity = min(100, mean_edge * 5)
        
        return round(complexity, 2)
    
    def _extract_dominant_colors(self, img, num_colors=5) -> List[str]:
        """
        Extract dominant colors from an image.
        
        Args:
            img: OpenCV image
            num_colors: Number of dominant colors to extract
            
        Returns:
            List of dominant colors as hex strings
        """
        # Reshape the image to be a list of pixels
        pixels = img.reshape(-1, 3).astype(np.float32)
        
        # Reduce number of pixels to speed up processing
        sample_size = min(50000, pixels.shape[0])
        indices = np.random.choice(pixels.shape[0], sample_size, replace=False)
        pixels_sample = pixels[indices]
        
        # Convert from BGR to RGB
        pixels_sample = pixels_sample[:, ::-1]
        
        # Apply K-means clustering
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
        _, labels, centers = cv2.kmeans(pixels_sample, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Count occurrences of each label
        counts = np.bincount(labels.flatten())
        
        # Sort colors by frequency
        colors = []
        for i in np.argsort(counts)[::-1]:
            if i < len(centers):
                # Convert to integer RGB values
                color = centers[i].astype(int)
                # Convert to hex
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                colors.append(hex_color)
        
        return colors
    
    def _calculate_blur_score(self, gray_img) -> float:
        """
        Calculate a blur score using the variance of Laplacian method.
        
        Args:
            gray_img: Grayscale image
            
        Returns:
            Blur score (lower means more blurry)
        """
        # Calculate Laplacian
        laplacian = cv2.Laplacian(gray_img, cv2.CV_64F)
        
        # Calculate variance
        score = laplacian.var()
        
        # Normalize to 0-100 scale (higher is sharper)
        normalized_score = min(100, score / 10)
        
        return round(normalized_score, 2)
    
    def _is_image_blurry(self, gray_img) -> bool:
        """
        Determine if an image is blurry.
        
        Args:
            gray_img: Grayscale image
            
        Returns:
            True if the image is blurry, False otherwise
        """
        blur_score = self._calculate_blur_score(gray_img)
        return blur_score < 30
    
    def _estimate_noise_level(self, gray_img) -> float:
        """
        Estimate the noise level in an image.
        
        Args:
            gray_img: Grayscale image
            
        Returns:
            Noise level (0-100)
        """
        # Apply median filter to remove noise
        denoised = cv2.medianBlur(gray_img, 5)
        
        # Calculate difference between original and denoised
        diff = cv2.absdiff(gray_img, denoised)
        
        # Calculate mean difference
        noise_level = cv2.mean(diff)[0]
        
        # Normalize to 0-100 scale
        normalized_noise = min(100, noise_level * 5)
        
        return round(normalized_noise, 2)