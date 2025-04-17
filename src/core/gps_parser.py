"""
GPS Parser Module

This module provides functionality for parsing and converting GPS coordinates
from image metadata into human-readable formats and geographic information.
"""

import logging
import re
import math
from typing import Dict, Any, Tuple, Optional, Union, List
from fractions import Fraction

# Get the package logger
logger = logging.getLogger(__name__)

# Try to import optional geolocation libraries
try:
    import geopy
    from geopy.geocoders import Nominatim
    GEOPY_AVAILABLE = True
except ImportError:
    logger.info("geopy library not available. Reverse geocoding will be limited.")
    GEOPY_AVAILABLE = False

try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    logger.info("folium library not available. Map generation will be limited.")
    FOLIUM_AVAILABLE = False

try:
    import reverse_geocoder
    REVERSE_GEOCODER_AVAILABLE = True
except ImportError:
    logger.info("reverse_geocoder library not available. Offline geocoding will be limited.")
    REVERSE_GEOCODER_AVAILABLE = False


class GPSParser:
    """
    A class for parsing and converting GPS coordinates from image metadata.
    
    This class provides methods to extract GPS information from image metadata,
    convert between different coordinate formats, and perform reverse geocoding
    to get location names from coordinates.
    """
    
    def __init__(self):
        """Initialize the GPSParser."""
        # Initialize geocoder if available
        self.geocoder = None
        if GEOPY_AVAILABLE:
            try:
                self.geocoder = Nominatim(user_agent="ImageMetadataExtractor")
                logger.debug("Nominatim geocoder initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Nominatim geocoder: {e}")
        
        # Cache for geocoding results to avoid repeated API calls
        self.geocoding_cache = {}
        
        logger.debug("GPSParser initialized")
    
    def parse_gps_info(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse GPS information from metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            Dictionary with parsed GPS information
        """
        gps_info = {}
        
        try:
            # Check for GPS data in various formats
            
            # 1. Check for standard EXIF GPS tags
            if self._has_exif_gps_tags(metadata):
                gps_info = self._parse_exif_gps(metadata)
            
            # 2. Check for XMP GPS data if EXIF GPS not found
            elif self._has_xmp_gps_tags(metadata) and not gps_info:
                gps_info = self._parse_xmp_gps(metadata)
            
            # 3. Check for IPTC location data if GPS still not found
            elif self._has_iptc_location_tags(metadata) and not gps_info:
                gps_info = self._parse_iptc_location(metadata)
            
            # 4. Check for any other GPS-like data
            elif not gps_info:
                gps_info = self._parse_generic_gps(metadata)
            
            # If we have coordinates, add formatted versions and location info
            if 'Latitude' in gps_info and 'Longitude' in gps_info:
                lat = gps_info['Latitude']
                lon = gps_info['Longitude']
                
                # Add decimal coordinates
                if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                    # Add formatted coordinates
                    gps_info['Location'] = f"{lat}, {lon}"
                    gps_info['Coordinates'] = f"{lat}, {lon}"
                    
                    # Add DMS (degrees, minutes, seconds) format
                    lat_dms = self.decimal_to_dms(lat, 'lat')
                    lon_dms = self.decimal_to_dms(lon, 'lon')
                    gps_info['LatitudeDMS'] = lat_dms
                    gps_info['LongitudeDMS'] = lon_dms
                    
                    # Add Google Maps URL
                    gps_info['GoogleMapsURL'] = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                    
                    # Add location name through reverse geocoding
                    location_info = self.reverse_geocode(lat, lon)
                    if location_info:
                        gps_info.update(location_info)
            
            return gps_info
            
        except Exception as e:
            logger.error(f"Error parsing GPS information: {e}")
            return {}
    
    def _has_exif_gps_tags(self, metadata: Dict[str, Any]) -> bool:
        """
        Check if metadata contains EXIF GPS tags.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            True if EXIF GPS tags are present, False otherwise
        """
        # Check for common GPS tags
        gps_tags = [
            'GPS:GPSLatitude', 'GPS:GPSLongitude',
            'GPSLatitude', 'GPSLongitude',
            'GPS:Latitude', 'GPS:Longitude',
            'GPS GPSLatitude', 'GPS GPSLongitude',
            'EXIF:GPSLatitude', 'EXIF:GPSLongitude'
        ]
        
        return any(tag in metadata for tag in gps_tags)
    
    def _has_xmp_gps_tags(self, metadata: Dict[str, Any]) -> bool:
        """
        Check if metadata contains XMP GPS tags.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            True if XMP GPS tags are present, False otherwise
        """
        # Check for common XMP GPS tags
        xmp_gps_tags = [
            'XMP:GPSLatitude', 'XMP:GPSLongitude',
            'XMP:Latitude', 'XMP:Longitude',
            'XMP-exif:GPSLatitude', 'XMP-exif:GPSLongitude'
        ]
        
        return any(tag in metadata for tag in xmp_gps_tags)
    
    def _has_iptc_location_tags(self, metadata: Dict[str, Any]) -> bool:
        """
        Check if metadata contains IPTC location tags.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            True if IPTC location tags are present, False otherwise
        """
        # Check for common IPTC location tags
        iptc_location_tags = [
            'IPTC:City', 'IPTC:Province-State', 'IPTC:Country',
            'IPTC:Sub-location', 'IPTC:LocationCode', 'IPTC:LocationName'
        ]
        
        return any(tag in metadata for tag in iptc_location_tags)
    
    def _parse_exif_gps(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse GPS information from EXIF metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            Dictionary with parsed GPS information
        """
        gps_info = {}
        
        # Extract latitude
        lat = self._extract_gps_coordinate(metadata, [
            'GPS:GPSLatitude', 'GPSLatitude', 'GPS GPSLatitude', 'EXIF:GPSLatitude'
        ])
        
        # Extract longitude
        lon = self._extract_gps_coordinate(metadata, [
            'GPS:GPSLongitude', 'GPSLongitude', 'GPS GPSLongitude', 'EXIF:GPSLongitude'
        ])
        
        # Extract reference directions (N/S/E/W)
        lat_ref = self._extract_gps_ref(metadata, [
            'GPS:GPSLatitudeRef', 'GPSLatitudeRef', 'GPS GPSLatitudeRef', 'EXIF:GPSLatitudeRef'
        ], default='N')
        
        lon_ref = self._extract_gps_ref(metadata, [
            'GPS:GPSLongitudeRef', 'GPSLongitudeRef', 'GPS GPSLongitudeRef', 'EXIF:GPSLongitudeRef'
        ], default='E')
        
        # Apply reference direction
        if lat is not None:
            lat = lat if lat_ref == 'N' else -lat
            gps_info['Latitude'] = lat
        
        if lon is not None:
            lon = lon if lon_ref == 'E' else -lon
            gps_info['Longitude'] = lon
        
        # Extract altitude
        alt = self._extract_gps_altitude(metadata)
        if alt is not None:
            gps_info['Altitude'] = alt
        
        # Extract other GPS information
        self._extract_additional_gps_info(metadata, gps_info)
        
        return gps_info
    
    def _extract_gps_coordinate(self, metadata: Dict[str, Any], possible_keys: List[str]) -> Optional[float]:
        """
        Extract a GPS coordinate from metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            possible_keys: List of possible keys for the coordinate
            
        Returns:
            Coordinate as a float, or None if not found
        """
        for key in possible_keys:
            if key in metadata:
                value = metadata[key]
                
                # Handle different value formats
                if isinstance(value, (int, float)):
                    return float(value)
                
                elif isinstance(value, str):
                    # Try to parse string as float
                    try:
                        return float(value)
                    except ValueError:
                        # Try to parse DMS format like "34 deg 56' 43.2\" N"
                        try:
                            return self.dms_to_decimal(value)
                        except:
                            pass
                
                elif isinstance(value, list) and len(value) == 3:
                    # Handle [degrees, minutes, seconds] format
                    try:
                        degrees = float(value[0])
                        minutes = float(value[1])
                        seconds = float(value[2])
                        return degrees + (minutes / 60.0) + (seconds / 3600.0)
                    except (ValueError, TypeError):
                        pass
                
                elif isinstance(value, tuple) and len(value) == 3:
                    # Handle (degrees, minutes, seconds) format
                    try:
                        degrees = float(value[0])
                        minutes = float(value[1])
                        seconds = float(value[2])
                        return degrees + (minutes / 60.0) + (seconds / 3600.0)
                    except (ValueError, TypeError):
                        pass
                
                elif isinstance(value, dict) and all(k in value for k in ['degrees', 'minutes', 'seconds']):
                    # Handle {'degrees': x, 'minutes': y, 'seconds': z} format
                    try:
                        degrees = float(value['degrees'])
                        minutes = float(value['minutes'])
                        seconds = float(value['seconds'])
                        return degrees + (minutes / 60.0) + (seconds / 3600.0)
                    except (ValueError, TypeError):
                        pass
        
        return None
    
    def _extract_gps_ref(self, metadata: Dict[str, Any], possible_keys: List[str], default: str) -> str:
        """
        Extract a GPS reference direction from metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            possible_keys: List of possible keys for the reference
            default: Default value if not found
            
        Returns:
            Reference direction ('N', 'S', 'E', or 'W')
        """
        for key in possible_keys:
            if key in metadata:
                value = metadata[key]
                
                if isinstance(value, str) and value in ['N', 'S', 'E', 'W']:
                    return value
                
                # Handle bytes
                if isinstance(value, bytes) and len(value) > 0:
                    try:
                        decoded = value.decode('ascii').strip()
                        if decoded in ['N', 'S', 'E', 'W']:
                            return decoded
                    except:
                        pass
        
        return default
    
    def _extract_gps_altitude(self, metadata: Dict[str, Any]) -> Optional[float]:
        """
        Extract GPS altitude from metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            Altitude in meters, or None if not found
        """
        # Possible keys for altitude
        altitude_keys = [
            'GPS:GPSAltitude', 'GPSAltitude', 'GPS GPSAltitude', 'EXIF:GPSAltitude'
        ]
        
        # Possible keys for altitude reference
        ref_keys = [
            'GPS:GPSAltitudeRef', 'GPSAltitudeRef', 'GPS GPSAltitudeRef', 'EXIF:GPSAltitudeRef'
        ]
        
        # Extract altitude
        altitude = None
        for key in altitude_keys:
            if key in metadata:
                value = metadata[key]
                
                if isinstance(value, (int, float)):
                    altitude = float(value)
                    break
                
                elif isinstance(value, str):
                    try:
                        altitude = float(value.replace('m', '').strip())
                        break
                    except ValueError:
                        pass
                
                elif isinstance(value, Fraction):
                    try:
                        altitude = float(value.numerator) / float(value.denominator)
                        break
                    except:
                        pass
        
        if altitude is None:
            return None
        
        # Extract altitude reference (0 = above sea level, 1 = below sea level)
        altitude_ref = 0  # Default to above sea level
        for key in ref_keys:
            if key in metadata:
                value = metadata[key]
                
                if value in [0, '0', b'0']:
                    altitude_ref = 0
                    break
                elif value in [1, '1', b'1']:
                    altitude_ref = 1
                    break
        
        # Apply reference
        return altitude if altitude_ref == 0 else -altitude
    
    def _extract_additional_gps_info(self, metadata: Dict[str, Any], gps_info: Dict[str, Any]) -> None:
        """
        Extract additional GPS information from metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            gps_info: Dictionary to update with additional GPS information
        """
        # GPS timestamp
        timestamp_keys = [
            'GPS:GPSTimeStamp', 'GPSTimeStamp', 'GPS GPSTimeStamp', 'EXIF:GPSTimeStamp'
        ]
        
        for key in timestamp_keys:
            if key in metadata:
                value = metadata[key]
                
                if isinstance(value, str):
                    gps_info['GPSTimeStamp'] = value
                    break
                
                elif isinstance(value, list) and len(value) == 3:
                    # Format as HH:MM:SS
                    try:
                        hours = int(value[0])
                        minutes = int(value[1])
                        seconds = int(value[2]) if isinstance(value[2], int) else int(float(value[2]))
                        gps_info['GPSTimeStamp'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        break
                    except (ValueError, TypeError):
                        pass
        
        # GPS date
        date_keys = [
            'GPS:GPSDateStamp', 'GPSDateStamp', 'GPS GPSDateStamp', 'EXIF:GPSDateStamp'
        ]
        
        for key in date_keys:
            if key in metadata:
                value = metadata[key]
                
                if isinstance(value, str):
                    gps_info['GPSDateStamp'] = value
                    break
        
        # GPS direction (heading)
        direction_keys = [
            'GPS:GPSImgDirection', 'GPSImgDirection', 'GPS GPSImgDirection', 'EXIF:GPSImgDirection'
        ]
        
        for key in direction_keys:
            if key in metadata:
                value = metadata[key]
                
                if isinstance(value, (int, float)):
                    gps_info['GPSDirection'] = float(value)
                    break
                
                elif isinstance(value, str):
                    try:
                        gps_info['GPSDirection'] = float(value)
                        break
                    except ValueError:
                        pass
                
                elif isinstance(value, Fraction):
                    try:
                        gps_info['GPSDirection'] = float(value.numerator) / float(value.denominator)
                        break
                    except:
                        pass
        
        # GPS speed
        speed_keys = [
            'GPS:GPSSpeed', 'GPSSpeed', 'GPS GPSSpeed', 'EXIF:GPSSpeed'
        ]
        
        for key in speed_keys:
            if key in metadata:
                value = metadata[key]
                
                if isinstance(value, (int, float)):
                    gps_info['GPSSpeed'] = float(value)
                    break
                
                elif isinstance(value, str):
                    try:
                        gps_info['GPSSpeed'] = float(value)
                        break
                    except ValueError:
                        pass
                
                elif isinstance(value, Fraction):
                    try:
                        gps_info['GPSSpeed'] = float(value.numerator) / float(value.denominator)
                        break
                    except:
                        pass
        
        # GPS speed reference (K = km/h, M = mph, N = knots)
        speed_ref_keys = [
            'GPS:GPSSpeedRef', 'GPSSpeedRef', 'GPS GPSSpeedRef', 'EXIF:GPSSpeedRef'
        ]
        
        for key in speed_ref_keys:
            if key in metadata:
                value = metadata[key]
                
                if isinstance(value, str) and value in ['K', 'M', 'N']:
                    speed_ref_map = {'K': 'km/h', 'M': 'mph', 'N': 'knots'}
                    gps_info['GPSSpeedRef'] = speed_ref_map.get(value, value)
                    break
                
                elif isinstance(value, bytes) and len(value) > 0:
                    try:
                        decoded = value.decode('ascii').strip()
                        if decoded in ['K', 'M', 'N']:
                            speed_ref_map = {'K': 'km/h', 'M': 'mph', 'N': 'knots'}
                            gps_info['GPSSpeedRef'] = speed_ref_map.get(decoded, decoded)
                            break
                    except:
                        pass
    
    def _parse_xmp_gps(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse GPS information from XMP metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            Dictionary with parsed GPS information
        """
        gps_info = {}
        
        # Extract latitude
        lat = self._extract_gps_coordinate(metadata, [
            'XMP:GPSLatitude', 'XMP:Latitude', 'XMP-exif:GPSLatitude'
        ])
        
        # Extract longitude
        lon = self._extract_gps_coordinate(metadata, [
            'XMP:GPSLongitude', 'XMP:Longitude', 'XMP-exif:GPSLongitude'
        ])
        
        if lat is not None:
            gps_info['Latitude'] = lat
        
        if lon is not None:
            gps_info['Longitude'] = lon
        
        # Extract altitude
        alt_keys = ['XMP:GPSAltitude', 'XMP:Altitude', 'XMP-exif:GPSAltitude']
        for key in alt_keys:
            if key in metadata:
                try:
                    value = metadata[key]
                    if isinstance(value, (int, float)):
                        gps_info['Altitude'] = float(value)
                        break
                    elif isinstance(value, str):
                        gps_info['Altitude'] = float(value.replace('m', '').strip())
                        break
                except (ValueError, TypeError):
                    pass
        
        return gps_info
    
    def _parse_iptc_location(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse location information from IPTC metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            Dictionary with location information
        """
        location_info = {}
        
        # Extract location components
        location_components = []
        
        # Check for sublocation
        sublocation_keys = ['IPTC:Sub-location', 'IPTC:Sublocation']
        for key in sublocation_keys:
            if key in metadata and metadata[key]:
                location_components.append(metadata[key])
                location_info['Sublocation'] = metadata[key]
                break
        
        # Check for city
        if 'IPTC:City' in metadata and metadata['IPTC:City']:
            location_components.append(metadata['IPTC:City'])
            location_info['City'] = metadata['IPTC:City']
        
        # Check for state/province
        state_keys = ['IPTC:Province-State', 'IPTC:State', 'IPTC:Province']
        for key in state_keys:
            if key in metadata and metadata[key]:
                location_components.append(metadata[key])
                location_info['State'] = metadata[key]
                break
        
        # Check for country
        if 'IPTC:Country' in metadata and metadata['IPTC:Country']:
            location_components.append(metadata['IPTC:Country'])
            location_info['Country'] = metadata['IPTC:Country']
        
        # Combine components into a location string
        if location_components:
            location_info['LocationName'] = ', '.join(location_components)
        
        return location_info
    
    def _parse_generic_gps(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse GPS information from any metadata fields that might contain coordinates.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            Dictionary with parsed GPS information
        """
        gps_info = {}
        
        # Look for any keys that might contain GPS coordinates
        for key, value in metadata.items():
            if not isinstance(value, str):
                continue
            
            # Skip if we already have coordinates
            if 'Latitude' in gps_info and 'Longitude' in gps_info:
                break
            
            # Check for coordinate patterns
            if 'gps' in key.lower() or 'location' in key.lower() or 'coordinates' in key.lower():
                # Try to extract coordinates from the value
                coords = self._extract_coordinates_from_string(value)
                if coords:
                    lat, lon = coords
                    gps_info['Latitude'] = lat
                    gps_info['Longitude'] = lon
                    break
        
        return gps_info
    
    def _extract_coordinates_from_string(self, text: str) -> Optional[Tuple[float, float]]:
        """
        Extract GPS coordinates from a string.
        
        Args:
            text: String that might contain coordinates
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Pattern for decimal coordinates like "12.345, -67.890"
        decimal_pattern = r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)'
        decimal_match = re.search(decimal_pattern, text)
        if decimal_match:
            try:
                lat = float(decimal_match.group(1))
                lon = float(decimal_match.group(2))
                # Validate coordinates
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
            except (ValueError, TypeError):
                pass
        
        # Pattern for DMS coordinates like "12° 34' 56" N, 67° 89' 12" W"
        dms_pattern = r'(\d+)°\s*(\d+)[\'′]?\s*(\d+(?:\.\d+)?)[\"″]?\s*([NS])\s*,\s*(\d+)°\s*(\d+)[\'′]?\s*(\d+(?:\.\d+)?)[\"″]?\s*([EW])'
        dms_match = re.search(dms_pattern, text)
        if dms_match:
            try:
                lat_deg = int(dms_match.group(1))
                lat_min = int(dms_match.group(2))
                lat_sec = float(dms_match.group(3))
                lat_dir = dms_match.group(4)
                
                lon_deg = int(dms_match.group(5))
                lon_min = int(dms_match.group(6))
                lon_sec = float(dms_match.group(7))
                lon_dir = dms_match.group(8)
                
                lat = lat_deg + (lat_min / 60.0) + (lat_sec / 3600.0)
                if lat_dir == 'S':
                    lat = -lat
                
                lon = lon_deg + (lon_min / 60.0) + (lon_sec / 3600.0)
                if lon_dir == 'W':
                    lon = -lon
                
                # Validate coordinates
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
            except (ValueError, TypeError):
                pass
        
        return None
    
    def decimal_to_dms(self, coord: float, coord_type: str) -> str:
        """
        Convert decimal coordinates to DMS (degrees, minutes, seconds) format.
        
        Args:
            coord: Coordinate in decimal format
            coord_type: Type of coordinate ('lat' or 'lon')
            
        Returns:
            Coordinate in DMS format
        """
        # Determine direction
        if coord_type.lower() == 'lat':
            direction = 'N' if coord >= 0 else 'S'
        else:
            direction = 'E' if coord >= 0 else 'W'
        
        # Convert to absolute value
        coord = abs(coord)
        
        # Calculate degrees, minutes, seconds
        degrees = int(coord)
        minutes_float = (coord - degrees) * 60
        minutes = int(minutes_float)
        seconds = (minutes_float - minutes) * 60
        
        # Format the result
        return f"{degrees}° {minutes}' {seconds:.2f}\" {direction}"
    
    def dms_to_decimal(self, dms_str: str) -> float:
        """
        Convert DMS (degrees, minutes, seconds) coordinates to decimal format.
        
        Args:
            dms_str: Coordinate in DMS format
            
        Returns:
            Coordinate in decimal format
        """
        # Pattern for DMS format like "12° 34' 56" N"
        dms_pattern = r'(\d+)°\s*(\d+)[\'′]?\s*(\d+(?:\.\d+)?)[\"″]?\s*([NSEW])'
        dms_match = re.search(dms_pattern, dms_str)
        
        if dms_match:
            degrees = int(dms_match.group(1))
            minutes = int(dms_match.group(2))
            seconds = float(dms_match.group(3))
            direction = dms_match.group(4)
            
            # Calculate decimal degrees
            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
            
            # Apply direction
            if direction in ['S', 'W']:
                decimal = -decimal
            
            return decimal
        
        # Alternative pattern for simpler format like "12.345° N"
        simple_pattern = r'(\d+(?:\.\d+)?)°\s*([NSEW])'
        simple_match = re.search(simple_pattern, dms_str)
        
        if simple_match:
            degrees = float(simple_match.group(1))
            direction = simple_match.group(2)
            
            # Apply direction
            if direction in ['S', 'W']:
                degrees = -degrees
            
            return degrees
        
        # If no pattern matches, try to parse as a decimal
        try:
            return float(dms_str)
        except ValueError:
            raise ValueError(f"Could not parse DMS coordinate: {dms_str}")
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, str]:
        """
        Perform reverse geocoding to get location name from coordinates.
        
        Args:
            latitude: Latitude in decimal format
            longitude: Longitude in decimal format
            
        Returns:
            Dictionary with location information
        """
        # Check cache first
        cache_key = f"{latitude:.6f},{longitude:.6f}"
        if cache_key in self.geocoding_cache:
            return self.geocoding_cache[cache_key]
        
        location_info = {}
        
        # Try online geocoding with geopy if available
        if GEOPY_AVAILABLE and self.geocoder:
            try:
                location = self.geocoder.reverse((latitude, longitude), exactly_one=True)
                if location and location.raw:
                    # Extract address components
                    address = location.raw.get('address', {})
                    
                    # Build location name
                    components = []
                    
                    # Add city/town
                    for key in ['city', 'town', 'village', 'hamlet']:
                        if key in address and address[key]:
                            components.append(address[key])
                            location_info['City'] = address[key]
                            break
                    
                    # Add county/district
                    for key in ['county', 'district', 'state_district']:
                        if key in address and address[key]:
                            components.append(address[key])
                            location_info['County'] = address[key]
                            break
                    
                    # Add state/province
                    for key in ['state', 'province']:
                        if key in address and address[key]:
                            components.append(address[key])
                            location_info['State'] = address[key]
                            break
                    
                    # Add country
                    if 'country' in address and address['country']:
                        components.append(address['country'])
                        location_info['Country'] = address['country']
                    
                    # Combine components into a location name
                    if components:
                        location_info['LocationName'] = ', '.join(components)
                    
                    # Cache the result
                    self.geocoding_cache[cache_key] = location_info
                    return location_info
            except Exception as e:
                logger.warning(f"Online reverse geocoding failed: {e}")
        
        # Try offline geocoding with reverse_geocoder if available
        if REVERSE_GEOCODER_AVAILABLE:
            try:
                results = reverse_geocoder.search([(latitude, longitude)])
                if results and len(results) > 0:
                    result = results[0]
                    
                    # Extract components
                    components = []
                    
                    if 'name' in result and result['name']:
                        components.append(result['name'])
                        location_info['City'] = result['name']
                    
                    if 'admin1' in result and result['admin1']:
                        components.append(result['admin1'])
                        location_info['State'] = result['admin1']
                    
                    if 'cc' in result and result['cc']:
                        components.append(result['cc'])
                        location_info['CountryCode'] = result['cc']
                    
                    # Combine components into a location name
                    if components:
                        location_info['LocationName'] = ', '.join(components)
                    
                    # Cache the result
                    self.geocoding_cache[cache_key] = location_info
                    return location_info
            except Exception as e:
                logger.warning(f"Offline reverse geocoding failed: {e}")
        
        # If all geocoding methods fail, return empty dict
        return location_info
    
    def generate_map(self, latitude: float, longitude: float, zoom: int = 13) -> Optional[str]:
        """
        Generate an HTML map for the given coordinates.
        
        Args:
            latitude: Latitude in decimal format
            longitude: Longitude in decimal format
            zoom: Zoom level (1-18)
            
        Returns:
            Path to the generated HTML map file, or None if generation fails
        """
        if not FOLIUM_AVAILABLE:
            logger.warning("folium library not available. Cannot generate map.")
            return None
        
        try:
            # Create a map centered at the coordinates
            m = folium.Map(location=[latitude, longitude], zoom_start=zoom)
            
            # Add a marker at the coordinates
            folium.Marker(
                location=[latitude, longitude],
                popup=f"Lat: {latitude}, Lon: {longitude}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
            
            # Create a temporary file for the map
            import tempfile
            import os
            
            # Create a temporary directory if it doesn't exist
            temp_dir = os.path.join(tempfile.gettempdir(), 'image_metadata_extractor')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate a unique filename
            map_file = os.path.join(temp_dir, f"map_{latitude:.6f}_{longitude:.6f}.html")
            
            # Save the map
            m.save(map_file)
            
            return map_file
            
        except Exception as e:
            logger.error(f"Error generating map: {e}")
            return None
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the distance between two coordinates using the Haversine formula.
        
        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point
            
        Returns:
            Distance in kilometers
        """
        # Earth radius in kilometers
        R = 6371.0
        
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
    def get_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the bearing (direction) from point 1 to point 2.
        
        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point
            
        Returns:
            Bearing in degrees (0-360, where 0 is North)
        """
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Calculate bearing
        y = math.sin(lon2_rad - lon1_rad) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad)
        bearing_rad = math.atan2(y, x)
        
        # Convert to degrees
        bearing_deg = math.degrees(bearing_rad)
        
        # Normalize to 0-360
        bearing = (bearing_deg + 360) % 360
        
        return bearing
    
    def get_cardinal_direction(self, bearing: float) -> str:
        """
        Convert a bearing to a cardinal direction.
        
        Args:
            bearing: Bearing in degrees (0-360)
            
        Returns:
            Cardinal direction (N, NE, E, SE, S, SW, W, NW)
        """
        # Define direction ranges
        directions = [
            (337.5, 22.5, "N"),
            (22.5, 67.5, "NE"),
            (67.5, 112.5, "E"),
            (112.5, 157.5, "SE"),
            (157.5, 202.5, "S"),
            (202.5, 247.5, "SW"),
            (247.5, 292.5, "W"),
            (292.5, 337.5, "NW")
        ]
        
        # Find the matching direction
        for start, end, direction in directions:
            if start <= bearing < end:
                return direction
            
        # Default to North
        return "N"
    
    def format_coordinates_for_display(self, latitude: float, longitude: float) -> Dict[str, str]:
        """
        Format coordinates in various formats for display.
        
        Args:
            latitude: Latitude in decimal format
            longitude: Longitude in decimal format
            
        Returns:
            Dictionary with formatted coordinates
        """
        formatted = {}
        
        # Decimal degrees
        formatted['Decimal'] = f"{latitude:.6f}, {longitude:.6f}"
        
        # DMS (degrees, minutes, seconds)
        formatted['DMS'] = f"{self.decimal_to_dms(latitude, 'lat')}, {self.decimal_to_dms(longitude, 'lon')}"
        
        # Degrees and decimal minutes
        lat_deg = int(abs(latitude))
        lat_min = (abs(latitude) - lat_deg) * 60
        lat_dir = 'N' if latitude >= 0 else 'S'
        
        lon_deg = int(abs(longitude))
        lon_min = (abs(longitude) - lon_deg) * 60
        lon_dir = 'E' if longitude >= 0 else 'W'
        
        formatted['DDM'] = f"{lat_deg}° {lat_min:.4f}' {lat_dir}, {lon_deg}° {lon_min:.4f}' {lon_dir}"
        
        # UTM (Universal Transverse Mercator)
        try:
            import utm
            utm_coords = utm.from_latlon(latitude, longitude)
            formatted['UTM'] = f"{utm_coords[2]}{utm_coords[3]} {utm_coords[0]:.0f}E {utm_coords[1]:.0f}N"
        except ImportError:
            formatted['UTM'] = "UTM conversion requires the 'utm' package"
        
        # MGRS (Military Grid Reference System)
        try:
            import mgrs
            m = mgrs.MGRS()
            mgrs_coords = m.toMGRS(latitude, longitude)
            formatted['MGRS'] = mgrs_coords
        except ImportError:
            formatted['MGRS'] = "MGRS conversion requires the 'mgrs' package"
        
        # Google Maps URL
        formatted['GoogleMapsURL'] = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
        
        # OpenStreetMap URL
        formatted['OpenStreetMapURL'] = f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}&zoom=15"
        
        return formatted
    
    def is_valid_coordinate(self, latitude: float, longitude: float) -> bool:
        """
        Check if coordinates are valid.
        
        Args:
            latitude: Latitude to check
            longitude: Longitude to check
            
        Returns:
            True if coordinates are valid, False otherwise
        """
        try:
            # Convert to float if they're strings
            if isinstance(latitude, str):
                latitude = float(latitude)
            if isinstance(longitude, str):
                longitude = float(longitude)
            
            # Check ranges
            return -90 <= latitude <= 90 and -180 <= longitude <= 180
        except (ValueError, TypeError):
            return False
    
    def extract_coordinates_from_text(self, text: str) -> List[Tuple[float, float]]:
        """
        Extract all GPS coordinates from a text string.
        
        Args:
            text: Text that might contain coordinates
            
        Returns:
            List of (latitude, longitude) tuples
        """
        coordinates = []
        
        # Pattern for decimal coordinates like "12.345, -67.890"
        decimal_pattern = r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)'
        decimal_matches = re.finditer(decimal_pattern, text)
        
        for match in decimal_matches:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                # Validate coordinates
                if self.is_valid_coordinate(lat, lon):
                    coordinates.append((lat, lon))
            except (ValueError, TypeError):
                pass
        
        # Pattern for DMS coordinates like "12° 34' 56" N, 67° 89' 12" W"
        dms_pattern = r'(\d+)°\s*(\d+)[\'′]?\s*(\d+(?:\.\d+)?)[\"″]?\s*([NS])\s*,\s*(\d+)°\s*(\d+)[\'′]?\s*(\d+(?:\.\d+)?)[\"″]?\s*([EW])'
        dms_matches = re.finditer(dms_pattern, text)
        
        for match in dms_matches:
            try:
                lat_deg = int(match.group(1))
                lat_min = int(match.group(2))
                lat_sec = float(match.group(3))
                lat_dir = match.group(4)
                
                lon_deg = int(match.group(5))
                lon_min = int(match.group(6))
                lon_sec = float(match.group(7))
                lon_dir = match.group(8)
                
                lat = lat_deg + (lat_min / 60.0) + (lat_sec / 3600.0)
                if lat_dir == 'S':
                    lat = -lat
                
                lon = lon_deg + (lon_min / 60.0) + (lon_sec / 3600.0)
                if lon_dir == 'W':
                    lon = -lon
                
                # Validate coordinates
                if self.is_valid_coordinate(lat, lon):
                    coordinates.append((lat, lon))
            except (ValueError, TypeError):
                pass
        
        return coordinates
    
    def get_timezone_from_coordinates(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Get the timezone for a location based on coordinates.
        
        Args:
            latitude: Latitude in decimal format
            longitude: Longitude in decimal format
            
        Returns:
            Timezone name or None if not found
        """
        try:
            from timezonefinder import TimezoneFinder
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
            return timezone_str
        except ImportError:
            logger.info("timezonefinder library not available. Cannot determine timezone.")
            return None
        except Exception as e:
            logger.warning(f"Error determining timezone: {e}")
            return None
    
    def get_elevation_from_coordinates(self, latitude: float, longitude: float) -> Optional[float]:
        """
        Get the elevation for a location based on coordinates.
        
        Args:
            latitude: Latitude in decimal format
            longitude: Longitude in decimal format
            
        Returns:
            Elevation in meters or None if not found
        """
        try:
            import requests
            # Use the Open-Elevation API
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={latitude},{longitude}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and len(data['results']) > 0:
                    return data['results'][0].get('elevation')
            return None
        except ImportError:
            logger.info("requests library not available. Cannot determine elevation.")
            return None
        except Exception as e:
            logger.warning(f"Error determining elevation: {e}")
            return None