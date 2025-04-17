"""
Utility module for formatting various types of metadata values.
Provides consistent formatting for display and export purposes.
"""

import datetime
import re
from typing import Any, Union, Dict


def format_metadata_value(value: Any) -> str:
    """
    Format any metadata value to a human-readable string.
    Handles different data types appropriately.
    
    Args:
        value: The metadata value to format
        
    Returns:
        A formatted string representation of the value
    """
    if value is None:
        return "N/A"
    
    if isinstance(value, (list, tuple)):
        if len(value) == 0:
            return "N/A"
        if len(value) == 1:
            return format_metadata_value(value[0])
        return ", ".join(format_metadata_value(item) for item in value)
    
    if isinstance(value, dict):
        if not value:
            return "N/A"
        return "; ".join(f"{k}: {format_metadata_value(v)}" for k, v in value.items())
    
    if isinstance(value, bool):
        return "Yes" if value else "No"
    
    if isinstance(value, (int, float)):
        # Check if it might be a timestamp
        if 1000000000 < value < 9999999999:  # Reasonable Unix timestamp range
            try:
                return format_timestamp(value)
            except:
                pass
        return str(value)
    
    # Default string conversion
    return str(value)


def format_file_size(size_in_bytes: Union[int, float]) -> str:
    """
    Convert file size in bytes to a human-readable format.
    
    Args:
        size_in_bytes: File size in bytes
        
    Returns:
        Formatted file size string (e.g., "2.5 MB")
    """
    if size_in_bytes is None or size_in_bytes < 0:
        return "Unknown"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_in_bytes)
    unit_index = 0
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    # Format with appropriate precision
    if unit_index == 0:  # Bytes
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def format_timestamp(timestamp: Union[int, float, str]) -> str:
    """
    Format a timestamp to a human-readable date and time.
    
    Args:
        timestamp: Unix timestamp (seconds since epoch)
        
    Returns:
        Formatted date/time string
    """
    try:
        # Convert string to float if needed
        if isinstance(timestamp, str):
            timestamp = float(timestamp)
            
        # Convert timestamp to datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OverflowError):
        # If conversion fails, return the original
        return str(timestamp)


def format_gps_coordinates(gps_data: Dict[str, Any]) -> str:
    """
    Format GPS coordinates to a readable string with degrees, minutes, seconds.
    
    Args:
        gps_data: Dictionary containing GPS information
        
    Returns:
        Formatted GPS coordinates string
    """
    if not gps_data or not isinstance(gps_data, dict):
        return "No GPS data"
    
    try:
        lat = gps_data.get('GPSLatitude')
        lat_ref = gps_data.get('GPSLatitudeRef', 'N')
        lon = gps_data.get('GPSLongitude')
        lon_ref = gps_data.get('GPSLongitudeRef', 'E')
        
        if not lat or not lon:
            return "Incomplete GPS data"
        
        # Format latitude
        lat_deg, lat_min, lat_sec = lat
        lat_str = f"{lat_deg}° {lat_min}' {lat_sec:.2f}\" {lat_ref}"
        
        # Format longitude
        lon_deg, lon_min, lon_sec = lon
        lon_str = f"{lon_deg}° {lon_min}' {lon_sec:.2f}\" {lon_ref}"
        
        return f"{lat_str}, {lon_str}"
    except (KeyError, ValueError, TypeError):
        # Fall back to decimal format if DMS format fails
        try:
            lat = gps_data.get('Latitude')
            lat_ref = gps_data.get('LatitudeRef', 'N')
            lon = gps_data.get('Longitude')
            lon_ref = gps_data.get('LongitudeRef', 'E')
            
            if lat is not None and lon is not None:
                lat_sign = -1 if lat_ref in ('S', 's') else 1
                lon_sign = -1 if lon_ref in ('W', 'w') else 1
                return f"{lat_sign * lat:.6f}, {lon_sign * lon:.6f}"
        except:
            pass
            
        return "Invalid GPS data format"


def format_exposure_time(exposure: Union[float, str, tuple]) -> str:
    """
    Format exposure time as a fraction (e.g., 1/125).
    
    Args:
        exposure: Exposure time value
        
    Returns:
        Formatted exposure time string
    """
    try:
        # Handle tuple format (numerator, denominator)
        if isinstance(exposure, tuple) and len(exposure) == 2:
            num, denom = exposure
            if num == 1:
                return f"1/{denom}"
            else:
                return f"{num}/{denom}"
        
        # Handle float
        if isinstance(exposure, (float, int)):
            if exposure >= 1:
                return str(exposure)
            else:
                # Convert to fraction
                denominator = round(1 / exposure)
                return f"1/{denominator}"
        
        # Handle string that might contain a fraction
        if isinstance(exposure, str):
            if '/' in exposure:
                return exposure
            try:
                return format_exposure_time(float(exposure))
            except:
                pass
                
        return str(exposure)
    except:
        return str(exposure)


def format_focal_length(focal_length: Any) -> str:
    """
    Format focal length with mm unit.
    
    Args:
        focal_length: The focal length value
        
    Returns:
        Formatted focal length string
    """
    try:
        # Handle tuple format (value, denominator)
        if isinstance(focal_length, tuple) and len(focal_length) == 2:
            value = focal_length[0] / focal_length[1]
            return f"{value:.1f} mm"
        
        # Handle numeric types
        if isinstance(focal_length, (int, float)):
            return f"{focal_length:.1f} mm"
        
        # Handle string
        if isinstance(focal_length, str):
            # If already has units, return as is
            if "mm" in focal_length.lower():
                return focal_length
            # Try to convert to float
            try:
                value = float(focal_length)
                return f"{value:.1f} mm"
            except:
                pass
        
        # Default
        return f"{focal_length} mm"
    except:
        return str(focal_length)


def clean_device_name(device_name: str) -> str:
    """
    Clean up device name by removing common prefixes and formatting.
    
    Args:
        device_name: Raw device name from metadata
        
    Returns:
        Cleaned device name
    """
    if not device_name:
        return "Unknown Device"
    
    # Remove common prefixes
    prefixes = ["DEVICE ", "CAMERA ", "CAM-", "PHONE-"]
    cleaned = device_name
    for prefix in prefixes:
        if cleaned.upper().startswith(prefix):
            cleaned = cleaned[len(prefix):]
    
    # Remove excessive spaces and special characters
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'[^\w\s\-\.]', '', cleaned)
    
    return cleaned if cleaned else "Unknown Device"