"""
Validators Module

This module provides validation functions for various inputs and data types
used in the Image Metadata Extractor application.
"""

import os
import re
import logging
import tempfile
from typing import Tuple, Optional, List, Dict, Any, Union
from pathlib import Path

# Get the package logger
logger = logging.getLogger(__name__)

# Try to import optional dependencies with fallbacks
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    logger.info("PIL/Pillow library not available. Image validation will be limited.")
    PIL_AVAILABLE = False

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    logger.info("python-magic library not available. MIME type detection will be limited.")
    MAGIC_AVAILABLE = False


def is_valid_image(file_path: str) -> bool:
    """
    Check if a file is a valid image.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file is a valid image, False otherwise
    """
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        logger.debug(f"File does not exist or is not a file: {file_path}")
        return False
    
    # Check file extension
    _, ext = os.path.splitext(file_path)
    valid_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp', '.heic', '.heif', '.cr2', '.nef']
    
    if ext.lower() not in valid_extensions:
        logger.debug(f"File has invalid extension: {ext}")
        return False
    
    # Check file size
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        logger.debug(f"File is empty: {file_path}")
        return False
    
    # Try to open with PIL if available
    if PIL_AVAILABLE:
        try:
            with Image.open(file_path) as img:
                # Verify the image can be loaded
                img.verify()
            return True
        except Exception as e:
            logger.debug(f"PIL could not verify image: {file_path}, error: {e}")
            # Fall through to other checks
    
    # Check MIME type if python-magic is available
    if MAGIC_AVAILABLE:
        try:
            mime = magic.Magic(mime=True)
            file_mime = mime.from_file(file_path)
            
            valid_mimes = [
                'image/jpeg', 'image/png', 'image/tiff', 'image/bmp', 
                'image/gif', 'image/webp', 'image/heic', 'image/heif'
            ]
            
            if file_mime in valid_mimes:
                return True
            
            logger.debug(f"File has invalid MIME type: {file_mime}")
            return False
        except Exception as e:
            logger.debug(f"Error checking MIME type: {e}")
    
    # If we can't verify with PIL or magic, just check the extension
    return ext.lower() in valid_extensions


def is_valid_path(path: str) -> bool:
    """
    Check if a path is valid and exists.
    
    Args:
        path: Path to check
        
    Returns:
        True if the path is valid and exists, False otherwise
    """
    if not path:
        return False
    
    try:
        # Check if path exists
        return os.path.exists(path)
    except Exception as e:
        logger.debug(f"Error checking path: {e}")
        return False


def is_valid_directory(directory: str) -> bool:
    """
    Check if a path is a valid directory.
    
    Args:
        directory: Directory path to check
        
    Returns:
        True if the path is a valid directory, False otherwise
    """
    if not directory:
        return False
    
    try:
        # Check if path exists and is a directory
        return os.path.exists(directory) and os.path.isdir(directory)
    except Exception as e:
        logger.debug(f"Error checking directory: {e}")
        return False


def is_writable_directory(directory: str) -> bool:
    """
    Check if a directory is writable.
    
    Args:
        directory: Directory path to check
        
    Returns:
        True if the directory is writable, False otherwise
    """
    if not is_valid_directory(directory):
        return False
    
    try:
        # Try to create a temporary file in the directory
        temp_file = os.path.join(directory, f".write_test_{os.getpid()}")
        with open(temp_file, 'w') as f:
            f.write('test')
        
        # Clean up
        os.remove(temp_file)
        
        return True
    except Exception as e:
        logger.debug(f"Directory is not writable: {directory}, error: {e}")
        return False


def validate_output_directory(directory: str) -> Tuple[bool, str]:
    """
    Validate that an output directory exists and is writable.
    
    Args:
        directory: Directory to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if directory exists
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
        except Exception as e:
            return False, f"Could not create directory: {str(e)}"
    
    # Check if it's a directory
    if not os.path.isdir(directory):
        return False, "Not a directory"
    
    # Check if it's writable
    if not is_writable_directory(directory):
        return False, "Directory is not writable"
    
    return True, ""


def is_valid_file(file_path: str) -> bool:
    """
    Check if a path is a valid file.
    
    Args:
        file_path: File path to check
        
    Returns:
        True if the path is a valid file, False otherwise
    """
    if not file_path:
        return False
    
    try:
        # Check if path exists and is a file
        return os.path.exists(file_path) and os.path.isfile(file_path)
    except Exception as e:
        logger.debug(f"Error checking file: {e}")
        return False


def is_valid_image_format(format_name: str) -> bool:
    """
    Check if a format name is a valid image format.
    
    Args:
        format_name: Format name to check
        
    Returns:
        True if the format is valid, False otherwise
    """
    valid_formats = [
        'jpeg', 'jpg', 'png', 'tiff', 'tif', 'bmp', 'gif', 'webp', 
        'heic', 'heif', 'cr2', 'nef'
    ]
    
    return format_name.lower() in valid_formats


def is_valid_export_format(format_name: str) -> bool:
    """
    Check if a format name is a valid export format.
    
    Args:
        format_name: Format name to check
        
    Returns:
        True if the format is valid, False otherwise
    """
    valid_formats = ['csv', 'json', 'txt', 'xlsx', 'pdf', 'html', 'yaml', 'yml']
    
    return format_name.lower() in valid_formats


def is_valid_url(url: str) -> bool:
    """
    Check if a string is a valid URL.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is valid, False otherwise
    """
    if not url:
        return False
    
    # Simple URL validation regex
    url_pattern = re.compile(
        r'^(?:http|https)://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


def is_valid_email(email: str) -> bool:
    """
    Check if a string is a valid email address.
    
    Args:
        email: Email address to check
        
    Returns:
        True if the email is valid, False otherwise
    """
    if not email:
        return False
    
    # Email validation regex
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    return bool(email_pattern.match(email))


def is_valid_ip_address(ip: str) -> bool:
    """
    Check if a string is a valid IP address.
    
    Args:
        ip: IP address to check
        
    Returns:
        True if the IP address is valid, False otherwise
    """
    if not ip:
        return False
    
    # IPv4 validation regex
    ipv4_pattern = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')
    
    match = ipv4_pattern.match(ip)
    if not match:
        return False
    
    # Check that each octet is between 0 and 255
    for octet in match.groups():
        if int(octet) > 255:
            return False
    
    return True


def is_valid_date_format(date_str: str, format_str: str) -> bool:
    """
    Check if a string matches a date format.
    
    Args:
        date_str: Date string to check
        format_str: Expected date format (e.g., '%Y-%m-%d')
        
    Returns:
        True if the date string matches the format, False otherwise
    """
    if not date_str:
        return False
    
    try:
        import datetime
        datetime.datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False


def is_valid_gps_coordinates(lat: float, lon: float) -> bool:
    """
    Check if latitude and longitude values are valid GPS coordinates.
    
    Args:
        lat: Latitude value
        lon: Longitude value
        
    Returns:
        True if the coordinates are valid, False otherwise
    """
    try:
        # Convert to float if they're strings
        if isinstance(lat, str):
            lat = float(lat)
        if isinstance(lon, str):
            lon = float(lon)
        
        # Check ranges
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (ValueError, TypeError):
        return False


def is_valid_metadata_key(key: str) -> bool:
    """
    Check if a string is a valid metadata key.
    
    Args:
        key: Metadata key to check
        
    Returns:
        True if the key is valid, False otherwise
    """
    if not key:
        return False
    
    # Metadata keys should not contain certain characters
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    
    return not any(char in key for char in invalid_chars)


def is_valid_json(json_str: str) -> bool:
    """
    Check if a string is valid JSON.
    
    Args:
        json_str: JSON string to check
        
    Returns:
        True if the string is valid JSON, False otherwise
    """
    if not json_str:
        return False
    
    try:
        import json
        json.loads(json_str)
        return True
    except ValueError:
        return False


def is_valid_yaml(yaml_str: str) -> bool:
    """
    Check if a string is valid YAML.
    
    Args:
        yaml_str: YAML string to check
        
    Returns:
        True if the string is valid YAML, False otherwise
    """
    if not yaml_str:
        return False
    
    try:
        import yaml
        yaml.safe_load(yaml_str)
        return True
    except (yaml.YAMLError, ImportError):
        return False


def is_valid_csv(csv_str: str) -> bool:
    """
    Check if a string is valid CSV.
    
    Args:
        csv_str: CSV string to check
        
    Returns:
        True if the string is valid CSV, False otherwise
    """
    if not csv_str:
        return False
    
    try:
        import csv
        from io import StringIO
        
        # Try to parse the CSV
        csv_file = StringIO(csv_str)
        csv_reader = csv.reader(csv_file)
        list(csv_reader)  # Consume the iterator
        
        return True
    except Exception:
        return False


def is_valid_hex_color(color: str) -> bool:
    """
    Check if a string is a valid hexadecimal color code.
    
    Args:
        color: Color code to check
        
    Returns:
        True if the color code is valid, False otherwise
    """
    if not color:
        return False
    
    # Hex color validation regex
    hex_pattern = re.compile(r'^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
    
    return bool(hex_pattern.match(color))


def is_valid_filename(filename: str) -> bool:
    """
    Check if a string is a valid filename.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if the filename is valid, False otherwise
    """
    if not filename:
        return False
    
    # Check for invalid characters
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    
    return not any(char in filename for char in invalid_chars)


def is_valid_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Check if a filename has an allowed extension.
    
    Args:
        filename: Filename to check
        allowed_extensions: List of allowed extensions (e.g., ['.jpg', '.png'])
        
    Returns:
        True if the filename has an allowed extension, False otherwise
    """
    if not filename:
        return False
    
    # Get the file extension
    _, ext = os.path.splitext(filename)
    
    # Convert to lowercase for case-insensitive comparison
    return ext.lower() in [e.lower() for e in allowed_extensions]


def is_valid_image_dimensions(width: int, height: int, min_width: int = 1, min_height: int = 1, max_width: Optional[int] = None, max_height: Optional[int] = None) -> bool:
    """
    Check if image dimensions are valid.
    
    Args:
        width: Image width
        height: Image height
        min_width: Minimum allowed width
        min_height: Minimum allowed height
        max_width: Maximum allowed width (None for no limit)
        max_height: Maximum allowed height (None for no limit)
        
    Returns:
        True if the dimensions are valid, False otherwise
    """
    try:
        # Convert to integers if they're strings
        if isinstance(width, str):
            width = int(width)
        if isinstance(height, str):
            height = int(height)
        
        # Check minimum dimensions
        if width < min_width or height < min_height:
            return False
        
        # Check maximum dimensions if specified
        if max_width is not None and width > max_width:
            return False
        if max_height is not None and height > max_height:
            return False
        
        return True
    except (ValueError, TypeError):
        return False


def is_valid_aspect_ratio(width: int, height: int, target_ratio: float, tolerance: float = 0.01) -> bool:
    """
    Check if image dimensions match a target aspect ratio within a tolerance.
    
    Args:
        width: Image width
        height: Image height
        target_ratio: Target aspect ratio (width/height)
        tolerance: Allowed deviation from target ratio
        
    Returns:
        True if the aspect ratio is valid, False otherwise
    """
    try:
        # Convert to integers if they're strings
        if isinstance(width, str):
            width = int(width)
        if isinstance(height, str):
            height = int(height)
        
        # Calculate actual ratio
        actual_ratio = width / height
        
        # Check if within tolerance
        return abs(actual_ratio - target_ratio) <= tolerance
    except (ValueError, TypeError, ZeroDivisionError):
        return False


def is_valid_file_size(file_path: str, max_size: int) -> bool:
    """
    Check if a file is within a maximum size limit.
    
    Args:
        file_path: Path to the file
        max_size: Maximum allowed size in bytes
        
    Returns:
        True if the file size is valid, False otherwise
    """
    if not is_valid_file(file_path):
        return False
    
    try:
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Check if within limit
        return file_size <= max_size
    except Exception as e:
        logger.debug(f"Error checking file size: {e}")
        return False


def is_valid_metadata_value(value: Any) -> bool:
    """
    Check if a value is valid for metadata storage.
    
    Args:
        value: Value to check
        
    Returns:
        True if the value is valid, False otherwise
    """
    # None is not a valid metadata value
    if value is None:
        return False
    
    # Check for basic types that are always valid
    if isinstance(value, (str, int, float, bool)):
        return True
    
    # Check for lists and dictionaries
    if isinstance(value, (list, tuple)):
        # Empty lists are not valid
        if not value:
            return False
        # Check each item in the list
        return all(is_valid_metadata_value(item) for item in value)
    
    if isinstance(value, dict):
        # Empty dictionaries are not valid
        if not value:
            return False
        # Check each key and value in the dictionary
        return all(is_valid_metadata_key(str(k)) and is_valid_metadata_value(v) for k, v in value.items())
    
    # Other types are converted to strings
    return True


def validate_input_files(file_paths: List[str], allowed_extensions: Optional[List[str]] = None) -> Tuple[List[str], List[str]]:
    """
    Validate a list of input files.
    
    Args:
        file_paths: List of file paths to validate
        allowed_extensions: List of allowed extensions (None for any)
        
    Returns:
        Tuple of (valid_files, invalid_files)
    """
    valid_files = []
    invalid_files = []
    
    for file_path in file_paths:
        # Check if file exists and is a file
        if not is_valid_file(file_path):
            invalid_files.append(file_path)
            continue
        
        # Check extension if specified
        if allowed_extensions is not None:
            if not is_valid_file_extension(file_path, allowed_extensions):
                invalid_files.append(file_path)
                continue
        
        valid_files.append(file_path)
    
    return valid_files, invalid_files


def validate_output_file(file_path: str, overwrite: bool = False) -> Tuple[bool, str]:
    """
    Validate an output file path.
    
    Args:
        file_path: File path to validate
        overwrite: Whether to allow overwriting existing files
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path:
        return False, "File path is empty"
    
    # Check if the directory exists
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            return False, f"Could not create directory: {str(e)}"
    
    # Check if the file already exists
    if os.path.exists(file_path) and not overwrite:
        return False, "File already exists and overwrite is not allowed"
    
    # Check if the directory is writable
    if not is_writable_directory(directory or os.getcwd()):
        return False, "Directory is not writable"
    
    # Check if the filename is valid
    filename = os.path.basename(file_path)
    if not is_valid_filename(filename):
        return False, "Invalid filename"
    
    return True, ""


def validate_image_file(file_path: str, min_width: int = 1, min_height: int = 1, max_width: Optional[int] = None, max_height: Optional[int] = None, max_size: Optional[int] = None) -> Tuple[bool, str]:
    """
    Validate an image file with various criteria.
    
    Args:
        file_path: Path to the image file
        min_width: Minimum allowed width
        min_height: Minimum allowed height
        max_width: Maximum allowed width (None for no limit)
        max_height: Maximum allowed height (None for no limit)
        max_size: Maximum allowed file size in bytes (None for no limit)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if the file exists and is a file
    if not is_valid_file(file_path):
        return False, "File does not exist or is not a file"
    
    # Check if it's a valid image
    if not is_valid_image(file_path):
        return False, "Not a valid image file"
    
    # Check file size if specified
    if max_size is not None and not is_valid_file_size(file_path, max_size):
        return False, f"File size exceeds maximum allowed size of {max_size} bytes"
    
    # Check dimensions if PIL is available
    if PIL_AVAILABLE:
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                
                if not is_valid_image_dimensions(width, height, min_width, min_height, max_width, max_height):
                    return False, f"Image dimensions ({width}x{height}) are outside allowed range"
        except Exception as e:
            return False, f"Error checking image dimensions: {str(e)}"
    
    return True, ""


def validate_metadata_dict(metadata: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a metadata dictionary.
    
    Args:
        metadata: Metadata dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(metadata, dict):
        return False, "Metadata must be a dictionary"
    
    if not metadata:
        return False, "Metadata dictionary is empty"
    
    # Check each key and value
    for key, value in metadata.items():
        if not is_valid_metadata_key(str(key)):
            return False, f"Invalid metadata key: {key}"
        
        if not is_valid_metadata_value(value):
            return False, f"Invalid metadata value for key: {key}"
    
    return True, ""


def validate_gps_data(gps_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate GPS data.
    
    Args:
        gps_data: GPS data dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(gps_data, dict):
        return False, "GPS data must be a dictionary"
    
    # Check for required fields
    required_fields = ['Latitude', 'Longitude']
    for field in required_fields:
        if field not in gps_data:
            return False, f"Missing required GPS field: {field}"
    
    # Validate coordinates
    try:
        lat = float(gps_data['Latitude'])
        lon = float(gps_data['Longitude'])
        
        if not is_valid_gps_coordinates(lat, lon):
            return False, f"Invalid GPS coordinates: {lat}, {lon}"
    except (ValueError, TypeError):
        return False, "GPS coordinates must be numeric"
    
    # Validate altitude if present
    if 'Altitude' in gps_data:
        try:
            float(gps_data['Altitude'])
        except (ValueError, TypeError):
            return False, "Altitude must be numeric"
    
    return True, ""


def validate_exif_data(exif_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate EXIF data.
    
    Args:
        exif_data: EXIF data dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(exif_data, dict):
        return False, "EXIF data must be a dictionary"
    
    if not exif_data:
        return False, "EXIF data dictionary is empty"
    
    # No specific validation rules for EXIF data, just check it's a non-empty dictionary
    return True, ""


def validate_batch_process_params(file_paths: List[str], output_dir: str, output_format: str) -> Tuple[bool, str]:
    """
    Validate parameters for batch processing.
    
    Args:
        file_paths: List of file paths to process
        output_dir: Directory to save output files
        output_format: Format to save in (csv, json, etc.)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if file paths list is empty
    if not file_paths:
        return False, "No files specified for processing"
    
    # Validate output directory
    valid_dir, dir_error = validate_output_directory(output_dir)
    if not valid_dir:
        return False, f"Invalid output directory: {dir_error}"
    
    # Validate output format
    if not is_valid_export_format(output_format):
        return False, f"Invalid export format: {output_format}"
    
    # Validate input files
    valid_files, invalid_files = validate_input_files(file_paths, ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp', '.heic', '.heif'])
    
    if not valid_files:
        return False, "No valid image files to process"
    
    if invalid_files:
        logger.warning(f"Some files are invalid and will be skipped: {invalid_files}")
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"
    
    # Replace invalid characters with underscores
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Trim leading/trailing whitespace and dots
    filename = filename.strip().strip('.')
    
    # If filename is empty after sanitization, use a default name
    if not filename:
        return "unnamed"
    
    return filename


def sanitize_path(path: str) -> str:
    """
    Sanitize a file path by removing invalid characters.
    
    Args:
        path: File path to sanitize
        
    Returns:
        Sanitized file path
    """
    if not path:
        return ""
    
    # Split path into directory and filename
    directory, filename = os.path.split(path)
    
    # Sanitize filename
    sanitized_filename = sanitize_filename(filename)
    
    # Recombine
    return os.path.join(directory, sanitized_filename)


def get_unique_filename(directory: str, base_name: str, extension: str) -> str:
    """
    Get a unique filename in a directory.
    
    Args:
        directory: Directory for the file
        base_name: Base filename
        extension: File extension
        
    Returns:
        Unique filename
    """
    # Sanitize base name
    base_name = sanitize_filename(base_name)
    
    # Clean up extension
    if not extension.startswith('.'):
        extension = f".{extension}"
    
    # Try the original filename first
    filename = os.path.join(directory, f"{base_name}{extension}")
    if not os.path.exists(filename):
        return filename
    
    # If it exists, add a number
    counter = 1
    while True:
        filename = os.path.join(directory, f"{base_name}_{counter}{extension}")
        if not os.path.exists(filename):
            return filename
        counter += 1


def is_path_inside_directory(path: str, directory: str) -> bool:
    """
    Check if a path is inside a directory.
    
    Args:
        path: Path to check
        directory: Directory to check against
        
    Returns:
        True if the path is inside the directory, False otherwise
    """
    # Normalize paths
    path = os.path.abspath(path)
    directory = os.path.abspath(directory)
    
    # Check if path starts with directory
    return path.startswith(directory)


def is_safe_path(base_dir: str, path: str) -> bool:
    """
    Check if a path is safe (doesn't escape from base directory).
    
    Args:
        base_dir: Base directory
        path: Path to check
        
    Returns:
        True if the path is safe, False otherwise
    """
    # Normalize paths
    base_dir = os.path.abspath(base_dir)
    path = os.path.abspath(os.path.join(base_dir, path))
    
    # Check if path is inside base directory
    return path.startswith(base_dir)


def validate_config_file(config_file: str) -> Tuple[bool, str]:
    """
    Validate a configuration file.
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not is_valid_file(config_file):
        return False, "Configuration file does not exist or is not a file"
    
    # Check file extension
    _, ext = os.path.splitext(config_file)
    
    if ext.lower() == '.json':
        # Validate JSON
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                import json
                json.load(f)
            return True, ""
        except Exception as e:
            return False, f"Invalid JSON configuration file: {str(e)}"
    
    elif ext.lower() in ['.yaml', '.yml']:
        # Validate YAML
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                import yaml
                yaml.safe_load(f)
            return True, ""
        except Exception as e:
            return False, f"Invalid YAML configuration file: {str(e)}"
    
    else:
        return False, f"Unsupported configuration file format: {ext}"


def validate_session_file(session_file: str) -> Tuple[bool, str]:
    """
    Validate a session file.
    
    Args:
        session_file: Path to the session file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not is_valid_file(session_file):
        return False, "Session file does not exist or is not a file"
    
    # Check file extension
    _, ext = os.path.splitext(session_file)
    
    if ext.lower() != '.json':
        return False, "Session file must be a JSON file"
    
    # Validate JSON
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            import json
            session_data = json.load(f)
        
        # Check for required fields
        required_fields = ['version', 'timestamp', 'files']
        for field in required_fields:
            if field not in session_data:
                return False, f"Missing required field in session file: {field}"
        
        return True, ""
    except Exception as e:
        return False, f"Invalid session file: {str(e)}"


def is_valid_color_space(color_space: str) -> bool:
    """
    Check if a string is a valid color space.
    
    Args:
        color_space: Color space to check
        
    Returns:
        True if the color space is valid, False otherwise
    """
    valid_color_spaces = [
        'RGB', 'RGBA', 'CMYK', 'LAB', 'HSV', 'YCbCr', 'GRAY', 'sRGB', 'Adobe RGB'
    ]
    
    return color_space.upper() in [cs.upper() for cs in valid_color_spaces]


def is_valid_compression_type(compression: str) -> bool:
    """
    Check if a string is a valid compression type.
    
    Args:
        compression: Compression type to check
        
    Returns:
        True if the compression type is valid, False otherwise
    """
    valid_compressions = [
        'JPEG', 'LZW', 'ZIP', 'PACKBITS', 'DEFLATE', 'NONE', 'RLE'
    ]
    
    return compression.upper() in [c.upper() for c in valid_compressions]


def is_valid_image_mode(mode: str) -> bool:
    """
    Check if a string is a valid PIL image mode.
    
    Args:
        mode: Image mode to check
        
    Returns:
        True if the mode is valid, False otherwise
    """
    valid_modes = [
        '1', 'L', 'P', 'RGB', 'RGBA', 'CMYK', 'YCbCr', 'LAB', 'HSV', 'I', 'F'
    ]
    
    return mode.upper() in [m.upper() for m in valid_modes]


def is_valid_dpi(dpi: Union[int, float, Tuple[int, int], Tuple[float, float]]) -> bool:
    """
    Check if a value is a valid DPI (dots per inch) setting.
    
    Args:
        dpi: DPI value to check
        
    Returns:
        True if the DPI is valid, False otherwise
    """
    try:
        # Handle tuple (x_dpi, y_dpi)
        if isinstance(dpi, tuple):
            x_dpi, y_dpi = dpi
            return x_dpi > 0 and y_dpi > 0
        
        # Handle single value
        return float(dpi) > 0
    except (ValueError, TypeError):
        return False


def is_valid_quality(quality: int) -> bool:
    """
    Check if a value is a valid image quality setting.
    
    Args:
        quality: Quality value to check
        
    Returns:
        True if the quality is valid, False otherwise
    """
    try:
        quality = int(quality)
        return 1 <= quality <= 100
    except (ValueError, TypeError):
        return False


def is_valid_rotation_angle(angle: float) -> bool:
    """
    Check if a value is a valid rotation angle.
    
    Args:
        angle: Angle value to check
        
    Returns:
        True if the angle is valid, False otherwise
    """
    try:
        angle = float(angle)
        # Any angle is technically valid, but we might want to normalize
        return True
    except (ValueError, TypeError):
        return False


def is_valid_exif_orientation(orientation: int) -> bool:
    """
    Check if a value is a valid EXIF orientation.
    
    Args:
        orientation: Orientation value to check
        
    Returns:
        True if the orientation is valid, False otherwise
    """
    try:
        orientation = int(orientation)
        # EXIF orientation values are 1-8
        return 1 <= orientation <= 8
    except (ValueError, TypeError):
        return False


def is_valid_exposure_time(exposure_time: Union[float, str]) -> bool:
    """
    Check if a value is a valid exposure time.
    
    Args:
        exposure_time: Exposure time to check
        
    Returns:
        True if the exposure time is valid, False otherwise
    """
    try:
        # Handle fraction string like "1/250"
        if isinstance(exposure_time, str) and '/' in exposure_time:
            numerator, denominator = exposure_time.split('/')
            return float(numerator) > 0 and float(denominator) > 0
        
        # Handle float
        return float(exposure_time) > 0
    except (ValueError, TypeError, ZeroDivisionError):
        return False


def is_valid_f_number(f_number: Union[float, str]) -> bool:
    """
    Check if a value is a valid f-number (aperture).
    
    Args:
        f_number: F-number to check
        
    Returns:
        True if the f-number is valid, False otherwise
    """
    try:
        # Handle string with "f/" prefix
        if isinstance(f_number, str) and f_number.lower().startswith('f/'):
            f_number = f_number[2:]
        
        # Convert to float and check
        f_number = float(f_number)
        
        # F-numbers are typically between 1.0 and 64.0
        return 0.7 <= f_number <= 64.0
    except (ValueError, TypeError):
        return False


def is_valid_iso(iso: int) -> bool:
    """
    Check if a value is a valid ISO sensitivity.
    
    Args:
        iso: ISO value to check
        
    Returns:
        True if the ISO is valid, False otherwise
    """
    try:
        iso = int(iso)
        # ISO values are typically between 50 and 409600
        return 25 <= iso <= 409600
    except (ValueError, TypeError):
        return False


def is_valid_focal_length(focal_length: Union[float, str]) -> bool:
    """
    Check if a value is a valid focal length.
    
    Args:
        focal_length: Focal length to check
        
    Returns:
        True if the focal length is valid, False otherwise
    """
    try:
        # Handle string with "mm" suffix
        if isinstance(focal_length, str):
            focal_length = focal_length.lower().replace('mm', '').strip()
        
        # Convert to float and check
        focal_length = float(focal_length)
        
        # Focal lengths are typically between 1mm and 2000mm
        return 1.0 <= focal_length <= 2000.0
    except (ValueError, TypeError):
        return False


def is_valid_flash_value(flash: int) -> bool:
    """
    Check if a value is a valid EXIF flash value.
    
    Args:
        flash: Flash value to check
        
    Returns:
        True if the flash value is valid, False otherwise
    """
    try:
        flash = int(flash)
        # EXIF flash values are typically between 0 and 95
        return 0 <= flash <= 95
    except (ValueError, TypeError):
        return False


def is_valid_metering_mode(metering_mode: int) -> bool:
    """
    Check if a value is a valid EXIF metering mode.
    
    Args:
        metering_mode: Metering mode to check
        
    Returns:
        True if the metering mode is valid, False otherwise
    """
    try:
        metering_mode = int(metering_mode)
        # EXIF metering mode values are 0-255
        valid_modes = [0, 1, 2, 3, 4, 5, 6, 255]
        return metering_mode in valid_modes
    except (ValueError, TypeError):
        return False


def is_valid_exposure_program(exposure_program: int) -> bool:
    """
    Check if a value is a valid EXIF exposure program.
    
    Args:
        exposure_program: Exposure program to check
        
    Returns:
        True if the exposure program is valid, False otherwise
    """
    try:
        exposure_program = int(exposure_program)
        # EXIF exposure program values are 0-9
        return 0 <= exposure_program <= 9
    except (ValueError, TypeError):
        return False


def is_valid_white_balance(white_balance: int) -> bool:
    """
    Check if a value is a valid EXIF white balance mode.
    
    Args:
        white_balance: White balance mode to check
        
    Returns:
        True if the white balance mode is valid, False otherwise
    """
    try:
        white_balance = int(white_balance)
        # EXIF white balance values are typically 0 (auto) or 1 (manual)
        return white_balance in [0, 1]
    except (ValueError, TypeError):
        return False


def is_valid_scene_capture_type(scene_type: int) -> bool:
    """
    Check if a value is a valid EXIF scene capture type.
    
    Args:
        scene_type: Scene capture type to check
        
    Returns:
        True if the scene capture type is valid, False otherwise
    """
    try:
        scene_type = int(scene_type)
        # EXIF scene capture type values are 0-4
        return 0 <= scene_type <= 4
    except (ValueError, TypeError):
        return False


def is_valid_contrast(contrast: int) -> bool:
    """
    Check if a value is a valid EXIF contrast setting.
    
    Args:
        contrast: Contrast setting to check
        
    Returns:
        True if the contrast setting is valid, False otherwise
    """
    try:
        contrast = int(contrast)
        # EXIF contrast values are 0-2
        return 0 <= contrast <= 2
    except (ValueError, TypeError):
        return False


def is_valid_saturation(saturation: int) -> bool:
    """
    Check if a value is a valid EXIF saturation setting.
    
    Args:
        saturation: Saturation setting to check
        
    Returns:
        True if the saturation setting is valid, False otherwise
    """
    try:
        saturation = int(saturation)
        # EXIF saturation values are 0-2
        return 0 <= saturation <= 2
    except (ValueError, TypeError):
        return False


def is_valid_sharpness(sharpness: int) -> bool:
    """
    Check if a value is a valid EXIF sharpness setting.
    
    Args:
        sharpness: Sharpness setting to check
        
    Returns:
        True if the sharpness setting is valid, False otherwise
    """
    try:
        sharpness = int(sharpness)
        # EXIF sharpness values are 0-2
        return 0 <= sharpness <= 2
    except (ValueError, TypeError):
        return False


def is_valid_subject_distance(distance: Union[float, str]) -> bool:
    """
    Check if a value is a valid subject distance.
    
    Args:
        distance: Subject distance to check
        
    Returns:
        True if the subject distance is valid, False otherwise
    """
    try:
        # Handle string with unit
        if isinstance(distance, str):
            distance = distance.lower()
            if 'm' in distance:
                distance = distance.replace('m', '').strip()
            elif 'ft' in distance or 'feet' in distance:
                # Convert feet to meters (approximate)
                distance = float(distance.replace('ft', '').replace('feet', '').strip()) * 0.3048
        
        # Convert to float and check
        distance = float(distance)
        
        # Subject distances are typically between 0 and 1000 meters
        # 0 can mean infinity in some cameras
        return distance >= 0
    except (ValueError, TypeError):
        return False


def is_valid_digital_zoom_ratio(zoom_ratio: float) -> bool:
    """
    Check if a value is a valid digital zoom ratio.
    
    Args:
        zoom_ratio: Digital zoom ratio to check
        
    Returns:
        True if the digital zoom ratio is valid, False otherwise
    """
    try:
        zoom_ratio = float(zoom_ratio)
        # Digital zoom ratios are typically between 0 and 100
        # 0 means no digital zoom
        return zoom_ratio >= 0
    except (ValueError, TypeError):
        return False


def is_valid_exif_version(version: str) -> bool:
    """
    Check if a string is a valid EXIF version.
    
    Args:
        version: EXIF version to check
        
    Returns:
        True if the EXIF version is valid, False otherwise
    """
    if not version:
        return False
    
    # EXIF versions are typically in the format "0220" or "2.2"
    if re.match(r'^\d{4}$', version):
        # Format like "0220"
        return True
    elif re.match(r'^\d+\.\d+$', version):
        # Format like "2.2"
        return True
    
    return False


def is_valid_software_name(software: str) -> bool:
    """
    Check if a string is a valid software name.
    
    Args:
        software: Software name to check
        
    Returns:
        True if the software name is valid, False otherwise
    """
    if not software:
        return False
    
    # Software names should not contain certain characters
    invalid_chars = ['<', '>', '|', '*']
    
    return not any(char in software for char in invalid_chars)


def is_valid_make_model(make_model: str) -> bool:
    """
    Check if a string is a valid camera make or model.
    
    Args:
        make_model: Camera make or model to check
        
    Returns:
        True if the make or model is valid, False otherwise
    """
    if not make_model:
        return False
    
    # Make/model should not contain certain characters
    invalid_chars = ['<', '>', '|', '*']
    
    return not any(char in make_model for char in invalid_chars)


def is_valid_copyright(copyright: str) -> bool:
    """
    Check if a string is a valid copyright notice.
    
    Args:
        copyright: Copyright notice to check
        
    Returns:
        True if the copyright notice is valid, False otherwise
    """
    if not copyright:
        return False
    
    # Copyright notices should not contain certain characters
    invalid_chars = ['<', '>', '|', '*']
    
    return not any(char in copyright for char in invalid_chars)


def is_valid_artist(artist: str) -> bool:
    """
    Check if a string is a valid artist name.
    
    Args:
        artist: Artist name to check
        
    Returns:
        True if the artist name is valid, False otherwise
    """
    if not artist:
        return False
    
    # Artist names should not contain certain characters
    invalid_chars = ['<', '>', '|', '*']
    
    return not any(char in artist for char in invalid_chars)


def is_valid_datetime_format(datetime_str: str) -> bool:
    """
    Check if a string is in a valid EXIF datetime format.
    
    Args:
        datetime_str: Datetime string to check
        
    Returns:
        True if the datetime string is valid, False otherwise
    """
    if not datetime_str:
        return False
    
    # EXIF datetime format is "YYYY:MM:DD HH:MM:SS"
    pattern = r'^\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}$'
    
    return bool(re.match(pattern, datetime_str))