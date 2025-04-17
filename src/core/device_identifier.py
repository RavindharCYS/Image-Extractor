"""
Device Identifier Module

This module provides functionality for identifying camera and device information
from image metadata, including make, model, and software details.
"""

import logging
import re
import json
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Get the package logger
logger = logging.getLogger(__name__)


class DeviceIdentifier:
    """
    A class for identifying camera and device information from image metadata.
    
    This class provides methods to extract and normalize device information,
    identify specific camera models, and provide additional device details.
    """
    
    def __init__(self):
        """Initialize the DeviceIdentifier."""
        # Load device database
        self.device_db = self._load_device_database()
        
        # Common camera manufacturers
        self.known_manufacturers = {
            # Mobile phone manufacturers
            'apple': 'Apple',
            'samsung': 'Samsung',
            'huawei': 'Huawei',
            'xiaomi': 'Xiaomi',
            'google': 'Google',
            'oneplus': 'OnePlus',
            'oppo': 'OPPO',
            'vivo': 'Vivo',
            'motorola': 'Motorola',
            'lg': 'LG',
            'sony': 'Sony',
            'htc': 'HTC',
            'nokia': 'Nokia',
            'asus': 'ASUS',
            'lenovo': 'Lenovo',
            'zte': 'ZTE',
            
            # Camera manufacturers
            'canon': 'Canon',
            'nikon': 'Nikon',
            'sony': 'Sony',
            'fuji': 'Fujifilm',
            'fujifilm': 'Fujifilm',
            'olympus': 'Olympus',
            'panasonic': 'Panasonic',
            'pentax': 'Pentax',
            'leica': 'Leica',
            'hasselblad': 'Hasselblad',
            'kodak': 'Kodak',
            'sigma': 'Sigma',
            'ricoh': 'Ricoh',
            'gopro': 'GoPro',
            'dji': 'DJI',
        }
        
        # Common software that processes images
        self.known_software = {
            'photoshop': 'Adobe Photoshop',
            'lightroom': 'Adobe Lightroom',
            'gimp': 'GIMP',
            'affinity': 'Affinity Photo',
            'capture one': 'Capture One',
            'luminar': 'Luminar',
            'snapseed': 'Snapseed',
            'instagram': 'Instagram',
            'vsco': 'VSCO',
            'pixlr': 'Pixlr',
            'paintshop': 'PaintShop Pro',
            'photolab': 'DxO PhotoLab',
            'acdsee': 'ACDSee',
            'aperture': 'Apple Aperture',
            'photos': 'Apple Photos',
            'picasa': 'Google Picasa',
            'darktable': 'Darktable',
            'rawtherapee': 'RawTherapee',
            'pixelmator': 'Pixelmator',
        }
        
        logger.debug("DeviceIdentifier initialized")
    
    def _load_device_database(self) -> Dict[str, Any]:
        """
        Load the device database from JSON file.
        
        Returns:
            Dictionary containing device information
        """
        try:
            # Try to load the database from the package directory
            db_path = os.path.join(os.path.dirname(__file__), 'data', 'device_database.json')
            
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # If not found, try to load from a few other possible locations
            alt_paths = [
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'device_database.json'),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'device_database.json'),
            ]
            
            for path in alt_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            
            # If no database file is found, return an empty database
            logger.warning("Device database file not found. Using empty database.")
            return {
                "cameras": {},
                "phones": {},
                "software": {},
                "lenses": {}
            }
            
        except Exception as e:
            logger.error(f"Error loading device database: {e}")
            # Return an empty database as fallback
            return {
                "cameras": {},
                "phones": {},
                "software": {},
                "lenses": {}
            }
    
    def identify_device(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify device information from metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            Dictionary with device information
        """
        device_info = {}
        
        try:
            # Extract basic device information
            make, model = self._extract_make_model(metadata)
            software = self._extract_software(metadata)
            
            # Add to device info if found
            if make:
                device_info['DeviceMake'] = make
            
            if model:
                device_info['DeviceModel'] = model
            
            if software:
                device_info['Software'] = software
            
            # Identify device type
            device_type = self._identify_device_type(make, model, metadata)
            if device_type:
                device_info['DeviceType'] = device_type
            
            # Extract lens information for cameras
            if device_type == 'Camera':
                lens_info = self._extract_lens_info(metadata)
                if lens_info:
                    device_info.update(lens_info)
            
            # Extract additional device details
            additional_info = self._extract_additional_device_info(metadata, device_type)
            if additional_info:
                device_info.update(additional_info)
            
            # Look up device in database for more details
            db_info = self._lookup_device_in_database(make, model, device_type)
            if db_info:
                # Don't overwrite existing info, only add missing details
                for key, value in db_info.items():
                    if key not in device_info:
                        device_info[key] = value
            
            # Add normalized manufacturer name
            if make and 'Manufacturer' not in device_info:
                normalized_make = self._normalize_manufacturer(make)
                if normalized_make != make:
                    device_info['Manufacturer'] = normalized_make
            
            # Add full device name
            if make and model and 'DeviceName' not in device_info:
                device_info['DeviceName'] = f"{make} {model}"
            
            return device_info
            
        except Exception as e:
            logger.error(f"Error identifying device: {e}")
            return device_info
    
    def _extract_make_model(self, metadata: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract make and model information from metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            Tuple of (make, model) or (None, None) if not found
        """
        make = None
        model = None
        
        # Check for make in various metadata fields
        make_keys = [
            'Make', 'make', 'EXIF:Make', 'IFD0:Make', 'Image Make',
            'Manufacturer', 'CameraManufacturer', 'DeviceManufacturer',
            'EXIF:Manufacturer', 'XMP:Manufacturer', 'IPTC:Manufacturer'
        ]
        
        for key in make_keys:
            if key in metadata and metadata[key]:
                make = str(metadata[key]).strip()
                break
        
        # Check for model in various metadata fields
        model_keys = [
            'Model', 'model', 'EXIF:Model', 'IFD0:Model', 'Image Model',
            'CameraModel', 'DeviceModel', 'EXIF:CameraModel',
            'XMP:Model', 'IPTC:Model'
        ]
        
        for key in model_keys:
            if key in metadata and metadata[key]:
                model = str(metadata[key]).strip()
                break
        
        # Clean up make and model
        if make:
            make = self._clean_device_string(make)
        
        if model:
            model = self._clean_device_string(model)
            
            # Some models include the make, remove it if that's the case
            if make and model.lower().startswith(make.lower()):
                model = model[len(make):].strip()
        
        return make, model
    
    def _extract_software(self, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Extract software information from metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            Software name or None if not found
        """
        # Check for software in various metadata fields
        software_keys = [
            'Software', 'software', 'EXIF:Software', 'IFD0:Software', 'Image Software',
            'ProcessingSoftware', 'CreatorTool', 'XMP:CreatorTool', 'XMP:Software',
            'IPTC:ProcessingSoftware'
        ]
        
        for key in software_keys:
            if key in metadata and metadata[key]:
                software = str(metadata[key]).strip()
                return self._clean_device_string(software)
        
        return None
    
    def _clean_device_string(self, text: str) -> str:
        """
        Clean up device string by removing unnecessary characters.
        
        Args:
            text: String to clean
            
        Returns:
            Cleaned string
        """
        if not text:
            return ""
        
        # Convert to string if not already
        text = str(text)
        
        # Remove null bytes and trim
        text = text.replace('\x00', '').strip()
        
        # Remove ASCII control characters
        text = ''.join(c for c in text if ord(c) >= 32 or ord(c) == 9)
        
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _identify_device_type(self, make: Optional[str], model: Optional[str], metadata: Dict[str, Any]) -> Optional[str]:
        """
        Identify the type of device that captured the image.
        
        Args:
            make: Device manufacturer
            model: Device model
            metadata: Dictionary containing image metadata
            
        Returns:
            Device type ('Camera', 'Smartphone', 'Tablet', 'Drone', etc.) or None if unknown
        """
        # Check if we have explicit device type information
        if 'DeviceType' in metadata:
            return metadata['DeviceType']
        
        # If no make/model, we can't determine the device type
        if not make and not model:
            return None
        
        # Convert to lowercase for comparison
        make_lower = make.lower() if make else ""
        model_lower = model.lower() if model else ""
        
        # Check for smartphone manufacturers
        smartphone_manufacturers = [
            'apple', 'iphone', 'samsung', 'huawei', 'xiaomi', 'google', 'pixel',
            'oneplus', 'oppo', 'vivo', 'motorola', 'lg', 'htc', 'nokia', 'asus',
            'lenovo', 'zte', 'realme', 'honor', 'poco'
        ]
        
        if any(mfr in make_lower for mfr in smartphone_manufacturers):
            # Check if it's a tablet
            tablet_indicators = ['ipad', 'tab', 'tablet', 'pad', 'galaxy tab']
            if any(indicator in model_lower for indicator in tablet_indicators):
                return 'Tablet'
            return 'Smartphone'
        
        # Check for camera manufacturers
        camera_manufacturers = [
            'canon', 'nikon', 'sony', 'fuji', 'fujifilm', 'olympus', 'panasonic',
            'pentax', 'leica', 'hasselblad', 'kodak', 'sigma', 'ricoh'
        ]
        
        if any(mfr in make_lower for mfr in camera_manufacturers):
            return 'Camera'
        
        # Check for drone manufacturers
        drone_manufacturers = ['dji', 'parrot', 'autel', 'skydio', 'yuneec']
        if any(mfr in make_lower for mfr in drone_manufacturers):
            return 'Drone'
        
        # Check for action cameras
        action_camera_indicators = ['gopro', 'hero', 'action', 'insta360']
        if any(indicator in make_lower or indicator in model_lower for indicator in action_camera_indicators):
            return 'Action Camera'
        
        # Check for specific model indicators
        if model_lower:
            if any(indicator in model_lower for indicator in ['phone', 'smartphone']):
                return 'Smartphone'
            if any(indicator in model_lower for indicator in ['camera', 'dslr', 'mirrorless']):
                return 'Camera'
            if any(indicator in model_lower for indicator in ['drone']):
                return 'Drone'
        
        # Check for lens information as an indicator of a dedicated camera
        lens_indicators = ['Lens', 'LensModel', 'LensInfo', 'LensSerialNumber']
        if any(key in metadata for key in lens_indicators):
            return 'Camera'
        
        # Check for focal length and aperture as indicators of a dedicated camera
        if 'FocalLength' in metadata or 'FNumber' in metadata:
            # Smartphones have these too, so check for other indicators
            if 'ISO' in metadata and 'ExposureTime' in metadata:
                # More likely to be a dedicated camera
                return 'Camera'
        
        # Default to generic "Digital Camera" if we can't determine more specifically
        if make or model:
            return 'Digital Camera'
        
        return None
    
    def _extract_lens_info(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract lens information from metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            Dictionary with lens information
        """
        lens_info = {}
        
        # Check for lens model
        lens_model_keys = [
            'LensModel', 'Lens', 'EXIF:LensModel', 'MakerNotes:LensModel',
            'XMP:LensModel', 'Lens Model', 'Lens Info', 'LensInfo'
        ]
        
        for key in lens_model_keys:
            if key in metadata and metadata[key]:
                lens_model = str(metadata[key]).strip()
                lens_info['LensModel'] = self._clean_device_string(lens_model)
                break
        
        # Check for lens make
        lens_make_keys = [
            'LensMake', 'EXIF:LensMake', 'MakerNotes:LensMake',
            'XMP:LensMake', 'Lens Make'
        ]
        
        for key in lens_make_keys:
            if key in metadata and metadata[key]:
                lens_make = str(metadata[key]).strip()
                lens_info['LensMake'] = self._clean_device_string(lens_make)
                break
        
        # Check for lens serial number
        lens_serial_keys = [
            'LensSerialNumber', 'EXIF:LensSerialNumber', 'MakerNotes:LensSerialNumber',
            'XMP:LensSerialNumber', 'Lens Serial Number'
        ]
        
        for key in lens_serial_keys:
            if key in metadata and metadata[key]:
                lens_serial = str(metadata[key]).strip()
                lens_info['LensSerialNumber'] = self._clean_device_string(lens_serial)
                break
        
        # Extract lens specifications
        lens_spec_keys = [
            'LensSpecification', 'EXIF:LensSpecification', 'MakerNotes:LensSpecification',
            'XMP:LensSpecification', 'Lens Specification'
        ]
        
        for key in lens_spec_keys:
            if key in metadata and metadata[key]:
                lens_spec = metadata[key]
                
                # Process lens specifications
                if isinstance(lens_spec, (list, tuple)) and len(lens_spec) >= 4:
                    try:
                        min_focal_length = float(lens_spec[0])
                        max_focal_length = float(lens_spec[1])
                        min_aperture = float(lens_spec[2])
                        max_aperture = float(lens_spec[3])
                        
                        lens_info['MinFocalLength'] = min_focal_length
                        lens_info['MaxFocalLength'] = max_focal_length
                        lens_info['MinAperture'] = min_aperture
                        lens_info['MaxAperture'] = max_aperture
                        
                        # Create a human-readable lens specification
                        if min_focal_length == max_focal_length:
                            focal_length_str = f"{min_focal_length}mm"
                        else:
                            focal_length_str = f"{min_focal_length}-{max_focal_length}mm"
                        
                        if min_aperture == max_aperture:
                            aperture_str = f"f/{min_aperture}"
                        else:
                            aperture_str = f"f/{min_aperture}-{max_aperture}"
                        
                        lens_info['LensSpecification'] = f"{focal_length_str} {aperture_str}"
                    except (ValueError, TypeError):
                        pass
                
                break
        
        # If we have a lens model but no lens make, try to extract make from model
        if 'LensModel' in lens_info and 'LensMake' not in lens_info:
            lens_model = lens_info['LensModel']
            lens_make = self._extract_lens_make_from_model(lens_model)
            if lens_make:
                lens_info['LensMake'] = lens_make
        
        # If we have lens info, add a combined field
        if 'LensMake' in lens_info and 'LensModel' in lens_info:
            lens_info['Lens'] = f"{lens_info['LensMake']} {lens_info['LensModel']}"
        elif 'LensModel' in lens_info:
            lens_info['Lens'] = lens_info['LensModel']
        
        return lens_info
    
    def _extract_lens_make_from_model(self, lens_model: str) -> Optional[str]:
        """
        Extract lens manufacturer from lens model string.
        
        Args:
            lens_model: Lens model string
            
        Returns:
            Lens manufacturer or None if not found
        """
        if not lens_model:
            return None
        
        # Common lens manufacturers
        lens_manufacturers = {
            'canon': 'Canon',
            'ef-s': 'Canon',
            'ef-m': 'Canon',
            'ef': 'Canon',
            'rf': 'Canon',
            'nikkor': 'Nikon',
            'nikon': 'Nikon',
            'sony': 'Sony',
            'zeiss': 'Zeiss',
            'leica': 'Leica',
            'sigma': 'Sigma',
            'tamron': 'Tamron',
            'tokina': 'Tokina',
            'samyang': 'Samyang',
            'rokinon': 'Rokinon',
            'voigtlander': 'Voigtlander',
            'olympus': 'Olympus',
            'zuiko': 'Olympus',
            'panasonic': 'Panasonic',
            'lumix': 'Panasonic',
            'fuji': 'Fujifilm',
            'fujinon': 'Fujifilm',
            'fujifilm': 'Fujifilm',
            'pentax': 'Pentax',
            'hasselblad': 'Hasselblad',
            'schneider': 'Schneider',
            'mamiya': 'Mamiya',
            'meyer': 'Meyer-Optik',
            'laowa': 'Laowa',
            'venus': 'Venus Optics',
            'irix': 'Irix',
            'ttartisan': 'TTArtisan',
            '7artisans': '7Artisans'
        }
        
        lens_model_lower = lens_model.lower()
        
        # Check if the lens model starts with a known manufacturer
        for key, manufacturer in lens_manufacturers.items():
            if lens_model_lower.startswith(key):
                return manufacturer
            if key in lens_model_lower:
                # If the manufacturer is in the model string, check if it's at a word boundary
                pattern = r'\b' + re.escape(key) + r'\b'
                if re.search(pattern, lens_model_lower):
                    return manufacturer
        
        return None
    
    def _extract_additional_device_info(self, metadata: Dict[str, Any], device_type: Optional[str]) -> Dict[str, Any]:
        """
        Extract additional device information from metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            device_type: Type of device
            
        Returns:
            Dictionary with additional device information
        """
        additional_info = {}
        
        # Extract camera serial number
        serial_keys = [
            'SerialNumber', 'CameraSerialNumber', 'BodySerialNumber',
            'EXIF:SerialNumber', 'MakerNotes:SerialNumber',
            'XMP:SerialNumber', 'Camera Serial Number'
        ]
        
        for key in serial_keys:
            if key in metadata and metadata[key]:
                serial = str(metadata[key]).strip()
                additional_info['DeviceSerialNumber'] = self._clean_device_string(serial)
                break
        
        # Extract firmware version
        firmware_keys = [
            'FirmwareVersion', 'Firmware', 'EXIF:FirmwareVersion',
            'MakerNotes:FirmwareVersion', 'XMP:FirmwareVersion'
        ]
        
        for key in firmware_keys:
            if key in metadata and metadata[key]:
                firmware = str(metadata[key]).strip()
                additional_info['FirmwareVersion'] = self._clean_device_string(firmware)
                break
        
        # Extract owner information
        owner_keys = [
            'OwnerName', 'CameraOwnerName', 'EXIF:OwnerName',
            'MakerNotes:OwnerName', 'XMP:OwnerName', 'Owner'
        ]
        
        for key in owner_keys:
            if key in metadata and metadata[key]:
                owner = str(metadata[key]).strip()
                additional_info['OwnerName'] = self._clean_device_string(owner)
                break
        
        # Extract camera settings for dedicated cameras
        if device_type in ['Camera', 'Digital Camera', 'Action Camera']:
            # Extract shooting mode
            mode_keys = [
                'ExposureMode', 'ExposureProgram', 'SceneCaptureType',
                'EXIF:ExposureMode', 'EXIF:ExposureProgram', 'EXIF:SceneCaptureType',
                'MakerNotes:ExposureMode', 'XMP:ExposureMode'
            ]
            
            for key in mode_keys:
                if key in metadata and metadata[key] is not None:
                    mode = metadata[key]
                    
                    # Convert numeric exposure program to text
                    if key.endswith('ExposureProgram') and isinstance(mode, (int, str)) and str(mode).isdigit():
                        mode_int = int(mode)
                        exposure_programs = {
                            0: 'Not Defined',
                            1: 'Manual',
                            2: 'Program AE',
                            3: 'Aperture Priority',
                            4: 'Shutter Priority',
                            5: 'Creative (Slow Speed)',
                            6: 'Action (High Speed)',
                            7: 'Portrait',
                            8: 'Landscape',
                            9: 'Bulb'
                        }
                        mode = exposure_programs.get(mode_int, f"Unknown ({mode_int})")
                    
                    # Convert numeric scene capture type to text
                    if key.endswith('SceneCaptureType') and isinstance(mode, (int, str)) and str(mode).isdigit():
                        mode_int = int(mode)
                        scene_types = {
                            0: 'Standard',
                            1: 'Landscape',
                            2: 'Portrait',
                            3: 'Night',
                            4: 'Night Portrait',
                            5: 'Backlight',
                            6: 'Backlight Portrait',
                            7: 'Macro',
                            8: 'Sports',
                            9: 'Action',
                            10: 'Fireworks',
                            11: 'Children',
                            12: 'Pets'
                        }
                        mode = scene_types.get(mode_int, f"Unknown ({mode_int})")
                    
                    additional_info['ShootingMode'] = str(mode)
                    break
        
        # Extract smartphone-specific information
        if device_type in ['Smartphone', 'Tablet']:
            # Check for OS version
            os_keys = [
                'OSVersion', 'OperatingSystem', 'Software',
                'XMP:OSVersion', 'XMP:OperatingSystem'
            ]
            
            for key in os_keys:
                if key in metadata and metadata[key]:
                    os_version = str(metadata[key]).strip()
                    
                    # Try to extract OS name and version
                    if 'iOS' in os_version or 'iPhone OS' in os_version:
                        additional_info['OperatingSystem'] = 'iOS'
                        # Extract version number
                        version_match = re.search(r'(\d+(?:\.\d+)*)', os_version)
                        if version_match:
                            additional_info['OSVersion'] = version_match.group(1)
                    elif 'Android' in os_version:
                        additional_info['OperatingSystem'] = 'Android'
                        # Extract version number
                        version_match = re.search(r'(\d+(?:\.\d+)*)', os_version)
                        if version_match:
                            additional_info['OSVersion'] = version_match.group(1)
                    else:
                        additional_info['OSVersion'] = self._clean_device_string(os_version)
                    
                    break
        
        return additional_info
    
    def _lookup_device_in_database(self, make: Optional[str], model: Optional[str], device_type: Optional[str]) -> Dict[str, Any]:
        """
        Look up device information in the database.
        
        Args:
            make: Device manufacturer
            model: Device model
            device_type: Type of device
            
        Returns:
            Dictionary with device information from database
        """
        if not make or not model or not self.device_db:
            return {}
        
        # Normalize make and model for lookup
        make_lower = make.lower()
        model_lower = model.lower()
        
        # Determine which database to search based on device type
        db_category = 'cameras'
        if device_type == 'Smartphone':
            db_category = 'phones'
        elif device_type == 'Tablet':
            db_category = 'phones'  # Tablets are in the phones database
        elif device_type == 'Drone':
            db_category = 'cameras'  # Drones are in the cameras database
        
        # Check if the database has this category
        if db_category not in self.device_db:
            return {}
        
        # Search for the device in the database
        device_db = self.device_db[db_category]
        
        # First, try exact match on make and model
        for device_id, device_info in device_db.items():
            db_make = device_info.get('make', '').lower()
            db_model = device_info.get('model', '').lower()
            
            if db_make == make_lower and db_model == model_lower:
                return self._format_db_device_info(device_info)
        
        # If no exact match, try fuzzy matching
        for device_id, device_info in device_db.items():
            db_make = device_info.get('make', '').lower()
            db_model = device_info.get('model', '').lower()
            
            # Check if make matches and model is similar
            if db_make == make_lower and (
                model_lower in db_model or db_model in model_lower or
                self._string_similarity(db_model, model_lower) > 0.8
            ):
                return self._format_db_device_info(device_info)
        
        # If still no match, try even more fuzzy matching
        best_match = None
        best_score = 0
        
        for device_id, device_info in device_db.items():
            db_make = device_info.get('make', '').lower()
            db_model = device_info.get('model', '').lower()
            
            # Calculate similarity scores
            make_score = self._string_similarity(db_make, make_lower)
            model_score = self._string_similarity(db_model, model_lower)
            
            # Combined score with more weight on model
            combined_score = (make_score * 0.4) + (model_score * 0.6)
            
            if combined_score > best_score and combined_score > 0.7:
                best_score = combined_score
                best_match = device_info
        
        if best_match:
            return self._format_db_device_info(best_match)
        
        return {}
    
    def _format_db_device_info(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format device information from database for output.
        
        Args:
            device_info: Raw device information from database
            
        Returns:
            Formatted device information
        """
        formatted = {}
        
        # Map database fields to output fields
        field_mapping = {
            'make': 'Manufacturer',
            'model': 'FullModel',
            'release_date': 'ReleaseDate',
            'sensor_type': 'SensorType',
            'sensor_size': 'SensorSize',
            'megapixels': 'Megapixels',
            'max_resolution': 'MaxResolution',
            'lens_mount': 'LensMount',
            'screen_size': 'ScreenSize',
            'os': 'OperatingSystem',
            'cpu': 'Processor',
            'storage': 'Storage',
            'battery': 'Battery',
            'weight': 'Weight',
            'dimensions': 'Dimensions',
            'price': 'Price',
            'url': 'ProductURL'
        }
        
        # Copy and rename fields
        for db_field, output_field in field_mapping.items():
            if db_field in device_info and device_info[db_field]:
                formatted[output_field] = device_info[db_field]
        
        return formatted
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        # Simple implementation using Levenshtein distance
        if not s1 or not s2:
            return 0
        
        # Normalize strings
        s1 = s1.lower()
        s2 = s2.lower()
        
        # If one string contains the other, they're very similar
        if s1 in s2 or s2 in s1:
            return 0.9
        
        # Calculate Levenshtein distance
        try:
            from Levenshtein import distance
            max_len = max(len(s1), len(s2))
            if max_len == 0:
                return 1.0
            return 1.0 - (distance(s1, s2) / max_len)
        except ImportError:
            # Fallback to a simpler similarity measure
            # Count matching characters
            matches = sum(c1 == c2 for c1, c2 in zip(s1, s2))
            max_len = max(len(s1), len(s2))
            if max_len == 0:
                return 1.0
            return matches / max_len
    
    def _normalize_manufacturer(self, make: str) -> str:
        """
        Normalize manufacturer name.
        
        Args:
            make: Manufacturer name
            
        Returns:
            Normalized manufacturer name
        """
        if not make:
            return make
        
        make_lower = make.lower()
        
        # Check against known manufacturers
        for key, normalized in self.known_manufacturers.items():
            if key == make_lower or make_lower.startswith(key):
                return normalized
        
        # If not found, return the original with proper capitalization
        return make
    
    def get_device_database_stats(self) -> Dict[str, int]:
        """
        Get statistics about the device database.
        
        Returns:
            Dictionary with database statistics
        """
        stats = {}
        
        if not self.device_db:
            return {'total': 0}
        
        for category, devices in self.device_db.items():
            stats[category] = len(devices)
        
        stats['total'] = sum(stats.values())
        
        return stats
    
    def search_device_database(self, query: str, device_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search the device database for matching devices.
        
        Args:
            query: Search query
            device_type: Optional device type to filter results
            
        Returns:
            List of matching devices
        """
        if not query or not self.device_db:
            return []
        
        query = query.lower()
        results = []
        
        # Determine which categories to search
        categories = list(self.device_db.keys())
        if device_type:
            if device_type.lower() in ['camera', 'digital camera']:
                categories = ['cameras']
            elif device_type.lower() in ['smartphone', 'phone', 'mobile']:
                categories = ['phones']
            elif device_type.lower() in ['lens', 'camera lens']:
                categories = ['lenses']
            elif device_type.lower() in ['software', 'app', 'application']:
                categories = ['software']
        
        # Search each category
        for category in categories:
            if category not in self.device_db:
                continue
            
            for device_id, device_info in self.device_db[category].items():
                # Check if query matches make or model
                make = device_info.get('make', '').lower()
                model = device_info.get('model', '').lower()
                
                if query in make or query in model or query in (make + ' ' + model):
                    # Format the result
                    result = self._format_db_device_info(device_info)
                    result['DeviceType'] = self._map_category_to_device_type(category)
                    results.append(result)
        
        # Sort results by relevance
        results.sort(key=lambda x: self._calculate_search_relevance(x, query), reverse=True)
        
        # Limit to top 20 results
        return results[:20]
    
    def _map_category_to_device_type(self, category: str) -> str:
        """
        Map database category to device type.
        
        Args:
            category: Database category
            
        Returns:
            Device type
        """
        category_map = {
            'cameras': 'Camera',
            'phones': 'Smartphone',
            'lenses': 'Camera Lens',
            'software': 'Software'
        }
        
        return category_map.get(category, category.capitalize())
    
    def _calculate_search_relevance(self, device: Dict[str, Any], query: str) -> float:
        """
        Calculate search result relevance score.
        
        Args:
            device: Device information
            query: Search query
            
        Returns:
            Relevance score
        """
        score = 0.0
        query = query.lower()
        
        # Check manufacturer match
        if 'Manufacturer' in device:
            manufacturer = device['Manufacturer'].lower()
            if query == manufacturer:
                score += 3.0
            elif query in manufacturer:
                score += 1.5
        
        # Check model match
        if 'FullModel' in device:
            model = device['FullModel'].lower()
            if query == model:
                score += 5.0
            elif query in model:
                score += 2.5
            elif model in query:
                score += 1.0
        
        # Newer devices get higher scores
        if 'ReleaseDate' in device:
            try:
                release_date = device['ReleaseDate']
                if isinstance(release_date, str):
                    # Try to parse year from the release date
                    year_match = re.search(r'(\d{4})', release_date)
                    if year_match:
                        year = int(year_match.group(1))
                        current_year = datetime.now().year
                        # Add up to 2.0 points for newer devices
                        score += min(2.0, max(0, (year - 2000) / 10))
            except:
                pass
        
        return score
    
    def update_device_database(self, new_data: Dict[str, Any]) -> bool:
        """
        Update the device database with new data.
        
        Args:
            new_data: New device data to add or update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Merge new data with existing database
            for category, devices in new_data.items():
                if category not in self.device_db:
                    self.device_db[category] = {}
                
                # Add or update devices
                for device_id, device_info in devices.items():
                    self.device_db[category][device_id] = device_info
            
            # Save the updated database
            self._save_device_database()
            
            return True
        except Exception as e:
            logger.error(f"Error updating device database: {e}")
            return False
    
    def _save_device_database(self) -> bool:
        """
        Save the device database to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to save to the package directory
            db_path = os.path.join(os.path.dirname(__file__), 'data', 'device_database.json')
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Save the database
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(self.device_db, f, indent=2)
            
            logger.info(f"Device database saved to {db_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving device database: {e}")
            
            # Try alternate locations
            try:
                alt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'device_database.json')
                os.makedirs(os.path.dirname(alt_path), exist_ok=True)
                
                with open(alt_path, 'w', encoding='utf-8') as f:
                    json.dump(self.device_db, f, indent=2)
                
                logger.info(f"Device database saved to alternate location: {alt_path}")
                return True
            except Exception as e2:
                logger.error(f"Error saving device database to alternate location: {e2}")
                return False
    
    def get_software_info(self, software_name: str) -> Dict[str, Any]:
        """
        Get information about image processing software.
        
        Args:
            software_name: Name of the software
            
        Returns:
            Dictionary with software information
        """
        if not software_name:
            return {}
        
        software_name_lower = software_name.lower()
        
        # Check if we have this software in our database
        if 'software' in self.device_db:
            for software_id, software_info in self.device_db['software'].items():
                db_name = software_info.get('name', '').lower()
                
                if software_name_lower == db_name or software_name_lower in db_name or db_name in software_name_lower:
                    return {
                        'SoftwareName': software_info.get('name', ''),
                        'SoftwareVersion': software_info.get('version', ''),
                        'SoftwareCompany': software_info.get('company', ''),
                        'SoftwareType': software_info.get('type', ''),
                        'SoftwareURL': software_info.get('url', '')
                    }
        
        # If not in database, try to identify common software
        for key, normalized in self.known_software.items():
            if key in software_name_lower:
                # Try to extract version number
                version_match = re.search(r'(\d+(?:\.\d+)+)', software_name)
                version = version_match.group(1) if version_match else ''
                
                return {
                    'SoftwareName': normalized,
                    'SoftwareVersion': version
                }
        
        # If all else fails, just return the name
        return {
            'SoftwareName': software_name
        }
    
    def create_device_profile(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a comprehensive device profile from metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            Dictionary with device profile information
        """
        # First, identify basic device info
        device_info = self.identify_device(metadata)
        
        # Get device type
        device_type = device_info.get('DeviceType', 'Unknown')
        
        # Add software information
        if 'Software' in device_info:
            software_info = self.get_software_info(device_info['Software'])
            # Only add new information
            for key, value in software_info.items():
                if key not in device_info:
                    device_info[key] = value
        
        # Add camera settings if available
        camera_settings = self._extract_camera_settings(metadata)
        if camera_settings:
            device_info.update(camera_settings)
        
        # Add privacy and security assessment
        privacy_assessment = self._assess_privacy_implications(metadata, device_type)
        if privacy_assessment:
            device_info['PrivacyAssessment'] = privacy_assessment
        
        return device_info
    
    def _extract_camera_settings(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract camera settings from metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            
        Returns:
            Dictionary with camera settings
        """
        settings = {}
        
        # Common camera settings to extract
        setting_keys = {
            'FNumber': 'Aperture',
            'ApertureValue': 'Aperture',
            'FocalLength': 'FocalLength',
            'FocalLengthIn35mmFormat': 'FocalLength35mm',
            'ExposureTime': 'ExposureTime',
            'ShutterSpeedValue': 'ShutterSpeed',
            'ISOSpeedRatings': 'ISO',
            'ISO': 'ISO',
            'WhiteBalance': 'WhiteBalance',
            'MeteringMode': 'MeteringMode',
            'ExposureProgram': 'ExposureProgram',
            'ExposureMode': 'ExposureMode',
            'ExposureCompensation': 'ExposureCompensation',
            'Flash': 'Flash',
            'FlashMode': 'FlashMode',
            'FocusMode': 'FocusMode',
            'DigitalZoomRatio': 'DigitalZoom'
        }
        
        # Check for each setting in metadata
        for exif_key, setting_name in setting_keys.items():
            # Try different variations of the key
            possible_keys = [
                exif_key,
                f'EXIF:{exif_key}',
                f'MakerNotes:{exif_key}',
                f'XMP:{exif_key}',
                f'Image {exif_key}'
            ]
            
            for key in possible_keys:
                if key in metadata and metadata[key] is not None:
                    value = metadata[key]
                    
                    # Format specific values
                    if setting_name == 'Aperture' and isinstance(value, (int, float)):
                        settings[setting_name] = f"f/{value}"
                    elif setting_name == 'FocalLength' and isinstance(value, (int, float)):
                        settings[setting_name] = f"{value}mm"
                    elif setting_name == 'ExposureTime' and isinstance(value, (int, float)):
                        if value < 1:
                            # Convert to fraction (e.g., 0.5 -> 1/2)
                            denominator = round(1 / value)
                            settings[setting_name] = f"1/{denominator}s"
                        else:
                            settings[setting_name] = f"{value}s"
                    else:
                        settings[setting_name] = value
                    
                    break
        
        # Process flash information
        if 'Flash' in settings:
            flash_value = settings['Flash']
            if isinstance(flash_value, int) or (isinstance(flash_value, str) and flash_value.isdigit()):
                flash_int = int(flash_value)
                flash_descriptions = {
                    0: "No Flash",
                    1: "Flash Fired",
                    5: "Flash Fired, Return not detected",
                    7: "Flash Fired, Return detected",
                    8: "On, Flash did not fire",
                    9: "Flash Fired, Compulsory mode",
                    13: "Flash Fired, Compulsory mode, Return not detected",
                    15: "Flash Fired, Compulsory mode, Return detected",
                    16: "Off, Flash did not fire",
                    24: "Off, Flash did not fire, Return not detected",
                    25: "Flash Fired, Auto mode",
                    29: "Flash Fired, Auto mode, Return not detected",
                    31: "Flash Fired, Auto mode, Return detected",
                    32: "No flash function",
                    65: "Flash Fired, Red-eye reduction",
                    69: "Flash Fired, Red-eye reduction, Return not detected",
                    71: "Flash Fired, Red-eye reduction, Return detected",
                    73: "Flash Fired, Compulsory mode, Red-eye reduction",
                    77: "Flash Fired, Compulsory mode, Red-eye reduction, Return not detected",
                    79: "Flash Fired, Compulsory mode, Red-eye reduction, Return detected",
                    89: "Flash Fired, Auto mode, Red-eye reduction",
                    93: "Flash Fired, Auto mode, Red-eye reduction, Return not detected",
                    95: "Flash Fired, Auto mode, Red-eye reduction, Return detected"
                }
                settings['Flash'] = flash_descriptions.get(flash_int, f"Unknown ({flash_int})")
        
        # Process metering mode
        if 'MeteringMode' in settings:
            metering_value = settings['MeteringMode']
            if isinstance(metering_value, int) or (isinstance(metering_value, str) and metering_value.isdigit()):
                metering_int = int(metering_value)
                metering_modes = {
                    0: "Unknown",
                    1: "Average",
                    2: "Center-weighted average",
                    3: "Spot",
                    4: "Multi-spot",
                    5: "Pattern",
                    6: "Partial",
                    255: "Other"
                }
                settings['MeteringMode'] = metering_modes.get(metering_int, f"Unknown ({metering_int})")
        
        # Process white balance
        if 'WhiteBalance' in settings:
            wb_value = settings['WhiteBalance']
            if isinstance(wb_value, int) or (isinstance(wb_value, str) and wb_value.isdigit()):
                wb_int = int(wb_value)
                wb_modes = {
                    0: "Auto",
                    1: "Manual"
                }
                settings['WhiteBalance'] = wb_modes.get(wb_int, f"Unknown ({wb_int})")
        
        return settings
    
    def _assess_privacy_implications(self, metadata: Dict[str, Any], device_type: str) -> Dict[str, Any]:
        """
        Assess privacy implications of the metadata.
        
        Args:
            metadata: Dictionary containing image metadata
            device_type: Type of device
            
        Returns:
            Dictionary with privacy assessment
        """
        assessment = {
            'PrivacyRisk': 'Low',
            'SensitiveDataPresent': False,
            'Recommendations': []
        }
        
        sensitive_fields = []
        
        # Check for GPS data
        has_gps = False
        gps_keys = ['GPS:GPSLatitude', 'GPS:GPSLongitude', 'GPSLatitude', 'GPSLongitude', 'Latitude', 'Longitude']
        for key in gps_keys:
            if key in metadata and metadata[key] is not None:
                has_gps = True
                sensitive_fields.append('GPS Location')
                break
        
        if has_gps:
            assessment['Recommendations'].append("Remove GPS data to protect location privacy")
            assessment['SensitiveDataPresent'] = True
            assessment['PrivacyRisk'] = 'High'
        
        # Check for serial numbers
        has_serial = False
        serial_keys = ['SerialNumber', 'CameraSerialNumber', 'BodySerialNumber', 'LensSerialNumber']
        for key in serial_keys:
            if key in metadata and metadata[key]:
                has_serial = True
                sensitive_fields.append('Serial Number')
                break
        
        if has_serial:
            assessment['Recommendations'].append("Remove serial numbers to prevent device tracking")
            assessment['SensitiveDataPresent'] = True
            if assessment['PrivacyRisk'] != 'High':
                assessment['PrivacyRisk'] = 'Medium'
        
        # Check for owner information
        has_owner_info = False
        owner_keys = ['OwnerName', 'CameraOwnerName', 'Artist', 'Author', 'Creator', 'By-line']
        for key in owner_keys:
            if key in metadata and metadata[key]:
                has_owner_info = True
                sensitive_fields.append('Owner/Author Information')
                break
        
        if has_owner_info:
            assessment['Recommendations'].append("Remove owner/author information for anonymity")
            assessment['SensitiveDataPresent'] = True
            if assessment['PrivacyRisk'] != 'High':
                assessment['PrivacyRisk'] = 'Medium'
        
        # Check for unique identifiers in smartphones
        if device_type in ['Smartphone', 'Tablet']:
            has_device_id = False
            device_id_keys = ['DeviceID', 'UniqueID', 'IMEI', 'UUID']
            for key in metadata:
                if any(id_key in key for id_key in device_id_keys) and metadata[key]:
                    has_device_id = True
                    sensitive_fields.append('Device Identifier')
                    break
            
            if has_device_id:
                assessment['Recommendations'].append("Remove unique device identifiers")
                assessment['SensitiveDataPresent'] = True
                if assessment['PrivacyRisk'] != 'High':
                    assessment['PrivacyRisk'] = 'Medium'
        
        # Check for timestamps
        has_timestamp = False
        timestamp_keys = ['DateTimeOriginal', 'CreateDate', 'ModifyDate', 'DateCreated']
        for key in timestamp_keys:
            if key in metadata and metadata[key]:
                has_timestamp = True
                sensitive_fields.append('Timestamp')
                break
        
        if has_timestamp:
            assessment['Recommendations'].append("Consider removing timestamps if time information is sensitive")
            # Timestamps alone are low risk
            if not assessment['SensitiveDataPresent']:
                assessment['SensitiveDataPresent'] = True
                assessment['PrivacyRisk'] = 'Low'
        
        # Check for software information that might reveal workflow
        has_software_info = False
        software_keys = ['Software', 'ProcessingSoftware', 'CreatorTool']
        for key in software_keys:
            if key in metadata and metadata[key]:
                has_software_info = True
                sensitive_fields.append('Software Information')
                break
        
        if has_software_info:
            assessment['Recommendations'].append("Consider removing software information to hide workflow details")
            # Software info alone is low risk
            if not assessment['SensitiveDataPresent']:
                assessment['SensitiveDataPresent'] = True
                assessment['PrivacyRisk'] = 'Low'
        
        # Add general recommendation if any sensitive data is present
        if assessment['SensitiveDataPresent']:
            assessment['Recommendations'].append("Use metadata cleaning tools before sharing images publicly")
            assessment['SensitiveFields'] = sensitive_fields
        else:
            assessment['Recommendations'].append("No sensitive metadata detected")
        
        return assessment