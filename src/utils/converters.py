"""
Converters Module

This module provides utility functions for converting data between different formats.
"""

import logging
import re
from datetime import datetime
from typing import Optional, Tuple, Union, Dict, Any

# Get the package logger
logger = logging.getLogger(__name__)

def convert_coordinates(coordinates: Union[str, Tuple[float, float]]) -> Optional[Tuple[float, float]]:
    """
    Convert coordinates from various formats to decimal degrees.
    
    Args:
        coordinates: Coordinates as string or tuple
        
    Returns:
        Tuple of (latitude, longitude) or None if conversion failed
    """
    if isinstance(coordinates, tuple) and len(coordinates) == 2:
        # Already in the right format
        return coordinates
    
    if isinstance(coordinates, str):
        # Try to parse from string
        # Pattern for decimal coordinates like "12.345, -67.890"
        decimal_pattern = r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)'
        decimal_match = re.search(decimal_pattern, coordinates)
        if decimal_match:
            try:
                lat = float(decimal_match.group(1))
                lon = float(decimal_match.group(2))
                return lat, lon
            except (ValueError, TypeError):
                pass
    
    # If we get here, conversion failed
    return None

def convert_timestamp(timestamp: Union[str, datetime, int]) -> Optional[datetime]:
    """
    Convert timestamp from various formats to datetime object.
    
    Args:
        timestamp: Timestamp as string, datetime, or unix timestamp
        
    Returns:
        Datetime object or None if conversion failed
    """
    if isinstance(timestamp, datetime):
        # Already a datetime object
        return timestamp
    
    if isinstance(timestamp, int) or (isinstance(timestamp, str) and timestamp.isdigit()):
        # Unix timestamp
        try:
            return datetime.fromtimestamp(int(timestamp))
        except (ValueError, TypeError, OSError):
            pass
    
    if isinstance(timestamp, str):
        # Try common datetime formats
        formats = [
            '%Y:%m:%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%Y:%m:%d',
            '%Y-%m-%d',
            '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp, fmt)
            except ValueError:
                continue
    
    # If we get here, conversion failed
    return None