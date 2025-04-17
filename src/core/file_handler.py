"""
File Handler Module

This module provides functionality for file operations, including loading images,
saving extracted metadata to various formats, and managing recent files.
"""

import os
import sys
import json
import csv
import logging
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, BinaryIO, TextIO
import re

# Get the package logger
logger = logging.getLogger(__name__)

# Try to import optional dependencies with fallbacks
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    logger.info("pandas library not available. Excel export will be limited.")
    PANDAS_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    logger.info("reportlab library not available. PDF export will be limited.")
    REPORTLAB_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    logger.info("PyYAML library not available. YAML export will be limited.")
    YAML_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    logger.info("PIL/Pillow library not available. Image preview in reports will be limited.")
    PIL_AVAILABLE = False


class FileHandler:
    """
    A class for handling file operations related to image metadata.
    
    This class provides methods for loading images, saving extracted metadata
    to various formats, and managing recent files.
    """
    
    def __init__(self, max_recent_files: int = 10):
        """
        Initialize the FileHandler.
        
        Args:
            max_recent_files: Maximum number of recent files to track
        """
        self.max_recent_files = max_recent_files
        self.recent_files = self._load_recent_files()
        self.config_dir = self._get_config_dir()
        
        # Create config directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            try:
                os.makedirs(self.config_dir)
                logger.debug(f"Created config directory: {self.config_dir}")
            except Exception as e:
                logger.warning(f"Failed to create config directory: {e}")
        
        logger.debug("FileHandler initialized")
    
    def _get_config_dir(self) -> str:
        """
        Get the configuration directory for the application.
        
        Returns:
            Path to the configuration directory
        """
        # Use platform-specific config directory
        if sys.platform == 'win32':
            base_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
            return os.path.join(base_dir, 'ImageMetadataExtractor')
        elif sys.platform == 'darwin':  # macOS
            return os.path.expanduser('~/Library/Application Support/ImageMetadataExtractor')
        else:  # Linux and other Unix-like systems
            return os.path.expanduser('~/.config/image_metadata_extractor')
    
    def _load_recent_files(self) -> List[str]:
        """
        Load the list of recent files from the configuration file.
        
        Returns:
            List of recent file paths
        """
        try:
            config_dir = self._get_config_dir()
            recent_files_path = os.path.join(config_dir, 'recent_files.json')
            
            if os.path.exists(recent_files_path):
                with open(recent_files_path, 'r', encoding='utf-8') as f:
                    recent_files = json.load(f)
                
                # Filter out files that no longer exist
                recent_files = [f for f in recent_files if os.path.exists(f)]
                
                logger.debug(f"Loaded {len(recent_files)} recent files")
                return recent_files
            
            return []
            
        except Exception as e:
            logger.warning(f"Failed to load recent files: {e}")
            return []
    
    def _save_recent_files(self) -> bool:
        """
        Save the list of recent files to the configuration file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            recent_files_path = os.path.join(self.config_dir, 'recent_files.json')
            
            with open(recent_files_path, 'w', encoding='utf-8') as f:
                json.dump(self.recent_files, f, indent=2)
            
            logger.debug(f"Saved {len(self.recent_files)} recent files")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to save recent files: {e}")
            return False
    
    def add_recent_file(self, file_path: str) -> None:
        """
        Add a file to the list of recent files.
        
        Args:
            file_path: Path to the file to add
        """
        if not file_path or not os.path.exists(file_path):
            return
        
        # Convert to absolute path
        file_path = os.path.abspath(file_path)
        
        # Remove if already in the list
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        # Add to the beginning of the list
        self.recent_files.insert(0, file_path)
        
        # Trim the list if needed
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
        
        # Save the updated list
        self._save_recent_files()
    
    def get_recent_files(self) -> List[str]:
        """
        Get the list of recent files.
        
        Returns:
            List of recent file paths
        """
        return self.recent_files
    
    def clear_recent_files(self) -> None:
        """Clear the list of recent files."""
        self.recent_files = []
        self._save_recent_files()
        logger.info("Cleared recent files list")
    
    def is_valid_image(self, file_path: str) -> bool:
        """
        Check if a file is a valid image.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file is a valid image, False otherwise
        """
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return False
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        valid_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp', '.heic', '.heif']
        
        if ext.lower() not in valid_extensions:
            return False
        
        # Try to open with PIL if available
        if PIL_AVAILABLE:
            try:
                with Image.open(file_path) as img:
                    # Check if the image can be loaded
                    img.verify()
                return True
            except Exception:
                return False
        
        # If PIL is not available, just check the extension
        return True
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        if not os.path.exists(file_path):
            return {'error': 'File not found'}
        
        try:
            file_stat = os.stat(file_path)
            file_info = {
                'filename': os.path.basename(file_path),
                'path': os.path.abspath(file_path),
                'size': file_stat.st_size,
                'size_formatted': self._format_file_size(file_stat.st_size),
                'created': datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'accessed': datetime.fromtimestamp(file_stat.st_atime).strftime('%Y-%m-%d %H:%M:%S'),
                'extension': os.path.splitext(file_path)[1].lower(),
            }
            
            # Get MIME type if python-magic is available
            try:
                import magic
                mime = magic.Magic(mime=True)
                file_info['mime_type'] = mime.from_file(file_path)
            except ImportError:
                # Fallback to basic MIME type detection
                ext = os.path.splitext(file_path)[1].lower()
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
                file_info['mime_type'] = mime_types.get(ext, 'application/octet-stream')
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {'error': str(e)}
    
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
    
    def save_csv(self, metadata: Dict[str, Any], output_file: str) -> bool:
        """
        Save metadata to a CSV file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Flatten nested dictionaries
            flattened_metadata = self._flatten_dict(metadata)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['Property', 'Value'])
                
                # Write data
                for key, value in flattened_metadata.items():
                    writer.writerow([key, value])
            
            logger.info(f"Saved metadata to CSV: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving metadata to CSV: {e}")
            return False
    
    def save_json(self, metadata: Dict[str, Any], output_file: str) -> bool:
        """
        Save metadata to a JSON file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert non-serializable objects to strings
            serializable_metadata = self._make_serializable(metadata)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved metadata to JSON: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving metadata to JSON: {e}")
            return False
    
    def save_text(self, metadata: Dict[str, Any], output_file: str) -> bool:
        """
        Save metadata to a plain text file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Flatten nested dictionaries
            flattened_metadata = self._flatten_dict(metadata)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("IMAGE METADATA REPORT\n")
                f.write("=" * 50 + "\n\n")
                
                # Add timestamp
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write data
                for key, value in flattened_metadata.items():
                    f.write(f"{key}: {value}\n")
            
            logger.info(f"Saved metadata to text file: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving metadata to text file: {e}")
            return False
    
    def save_excel(self, metadata: Dict[str, Any], output_file: str) -> bool:
        """
        Save metadata to an Excel file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            
        Returns:
            True if successful, False otherwise
        """
        if not PANDAS_AVAILABLE:
            logger.error("pandas library not available. Cannot save to Excel.")
            return False
        
        try:
            # Flatten nested dictionaries
            flattened_metadata = self._flatten_dict(metadata)
            
            # Create DataFrame
            df = pd.DataFrame(list(flattened_metadata.items()), columns=['Property', 'Value'])
            
            # Save to Excel
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Metadata', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Metadata']
                for i, col in enumerate(['A', 'B']):
                    max_length = 0
                    column = worksheet[col]
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    worksheet.column_dimensions[col].width = min(adjusted_width, 100)
            
            logger.info(f"Saved metadata to Excel: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving metadata to Excel: {e}")
            return False
    
    def save_pdf(self, metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Save metadata to a PDF file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            **kwargs: Additional options
                - image_path: Path to the image for preview
                - include_preview: Whether to include image preview (default: True)
                - title: Custom title for the report
                - page_size: Page size ('letter' or 'A4', default: 'letter')
                - company_name: Company name for the report header
            
        Returns:
            True if successful, False otherwise
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("reportlab library not available. Cannot save to PDF.")
            return False
        
        try:
            # Get options
            image_path = kwargs.get('image_path', None)
            include_preview = kwargs.get('include_preview', True)
            title = kwargs.get('title', 'Image Metadata Report')
            page_size = kwargs.get('page_size', 'letter')
            company_name = kwargs.get('company_name', '')
            
            # Set page size
            page_dimensions = letter if page_size.lower() == 'letter' else A4
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_file,
                pagesize=page_dimensions,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = styles['Title']
            heading_style = styles['Heading2']
            normal_style = styles['Normal']
            
            # Create custom style for metadata
            metadata_style = ParagraphStyle(
                'MetadataStyle',
                parent=styles['Normal'],
                fontName='Courier',
                fontSize=9,
                leading=12
            )
            
            # Create content elements
            elements = []
            
            # Add title
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Add company name if provided
            if company_name:
                elements.append(Paragraph(f"Prepared by: {company_name}", normal_style))
                elements.append(Spacer(1, 0.1 * inch))
            
            # Add timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elements.append(Paragraph(f"Generated: {timestamp}", normal_style))
            elements.append(Spacer(1, 0.25 * inch))
            
            # Add image preview if available
            if include_preview and image_path and os.path.exists(image_path) and PIL_AVAILABLE:
                try:
                    # Add image preview heading
                    elements.append(Paragraph("Image Preview", heading_style))
                    elements.append(Spacer(1, 0.1 * inch))
                    
                    # Open and resize image for preview
                    img = Image.open(image_path)
                    
                    # Calculate dimensions to fit on page
                    max_width = page_dimensions[0] - 2 * 72  # Page width minus margins
                    max_height = 3 * inch  # Limit height to 3 inches
                    
                    width, height = img.size
                    aspect = width / height
                    
                    if width > max_width:
                        width = max_width
                        height = width / aspect
                    
                    if height > max_height:
                        height = max_height
                        width = height * aspect
                    
                    # Create temporary file for the image
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                        temp_filename = temp_file.name
                    
                    # Save resized image to temp file
                    img_copy = img.copy()
                    img_copy.thumbnail((int(width), int(height)), Image.LANCZOS)
                    img_copy.save(temp_filename, format='JPEG')
                    
                    # Add image to PDF
                    elements.append(RLImage(temp_filename, width=width, height=height))
                    elements.append(Spacer(1, 0.25 * inch))
                    
                except Exception as e:
                    logger.warning(f"Error adding image preview to PDF: {e}")
            
            # Add file information if available
            if 'FileName' in metadata or 'FilePath' in metadata:
                elements.append(Paragraph("File Information", heading_style))
                elements.append(Spacer(1, 0.1 * inch))
                
                file_info = []
                
                if 'FileName' in metadata:
                    file_info.append(['File Name', str(metadata['FileName'])])
                
                if 'FilePath' in metadata:
                    file_info.append(['File Path', str(metadata['FilePath'])])
                
                if 'FileSize' in metadata and 'FileSizeFormatted' in metadata:
                    file_info.append(['File Size', str(metadata['FileSizeFormatted'])])
                
                if 'FileModifyDate' in metadata:
                    file_info.append(['Modified', str(metadata['FileModifyDate'])])
                
                if 'FileCreateDate' in metadata:
                    file_info.append(['Created', str(metadata['FileCreateDate'])])
                
                # Create table for file info
                if file_info:
                    table = Table(file_info, colWidths=[1.5 * inch, 4 * inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 0.25 * inch))
            
            # Organize metadata into categories
            categories = self._categorize_metadata(metadata)
            
            # Add each category
            for category_name, category_data in categories.items():
                if not category_data:
                    continue
                
                elements.append(Paragraph(category_name, heading_style))
                elements.append(Spacer(1, 0.1 * inch))
                
                # Create table data
                table_data = []
                for key, value in category_data.items():
                    # Format value
                    if isinstance(value, (list, tuple)):
                        value = ', '.join(str(item) for item in value)
                    elif not isinstance(value, str):
                        value = str(value)
                    
                    table_data.append([key, value])
                
                # Create table
                if table_data:
                    table = Table(table_data, colWidths=[2.5 * inch, 3 * inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 0.25 * inch))
            
            # Add privacy assessment if available
            if 'PrivacyAssessment' in metadata:
                elements.append(Paragraph("Privacy Assessment", heading_style))
                elements.append(Spacer(1, 0.1 * inch))
                
                privacy = metadata['PrivacyAssessment']
                
                # Create table data
                privacy_data = []
                
                if 'PrivacyRisk' in privacy:
                    risk_level = privacy['PrivacyRisk']
                    risk_color = colors.green
                    if risk_level == 'Medium':
                        risk_color = colors.orange
                    elif risk_level == 'High':
                        risk_color = colors.red
                    
                    privacy_data.append(['Privacy Risk Level', risk_level])
                
                if 'SensitiveDataPresent' in privacy:
                    privacy_data.append(['Sensitive Data Present', 'Yes' if privacy['SensitiveDataPresent'] else 'No'])
                
                if 'SensitiveFields' in privacy and privacy['SensitiveFields']:
                    fields = ', '.join(privacy['SensitiveFields'])
                    privacy_data.append(['Sensitive Fields', fields])
                
                # Create table
                if privacy_data:
                    table = Table(privacy_data, colWidths=[2 * inch, 3.5 * inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 0.15 * inch))
                
                # Add recommendations
                if 'Recommendations' in privacy and privacy['Recommendations']:
                    elements.append(Paragraph("Recommendations:", normal_style))
                    elements.append(Spacer(1, 0.05 * inch))
                    
                    for recommendation in privacy['Recommendations']:
                        bullet_para = Paragraph(f"• {recommendation}", normal_style)
                        elements.append(bullet_para)
                        elements.append(Spacer(1, 0.05 * inch))
                    
                    elements.append(Spacer(1, 0.15 * inch))
            
            # Add footer
            elements.append(Spacer(1, 0.5 * inch))
            footer_text = "Generated by Image Metadata Extractor"
            elements.append(Paragraph(footer_text, normal_style))
            
            # Build PDF
            doc.build(elements)
            
            # Clean up temporary files
            if include_preview and 'temp_filename' in locals():
                try:
                    os.unlink(temp_filename)
                except:
                    pass
            
            logger.info(f"Saved metadata to PDF: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving metadata to PDF: {e}")
            return False
    
    def save_html(self, metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Save metadata to an HTML file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            **kwargs: Additional options
                - image_path: Path to the image for preview
                - include_preview: Whether to include image preview (default: True)
                - title: Custom title for the report
                - company_name: Company name for the report header
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get options
            image_path = kwargs.get('image_path', None)
            include_preview = kwargs.get('include_preview', True)
            title = kwargs.get('title', 'Image Metadata Report')
            company_name = kwargs.get('company_name', '')
            
            # Categorize metadata
            categories = self._categorize_metadata(metadata)
            
            # Start HTML content
            html = [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                f"    <title>{title}</title>",
                "    <style>",
                "        body { font-family: Arial, sans-serif; margin: 20px; }",
                "        h1 { color: #2c3e50; }",
                "        h2 { color: #3498db; margin-top: 20px; }",
                "        .metadata-section { margin-bottom: 20px; }",
                "        .metadata-table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }",
                "        .metadata-table th, .metadata-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
                "        .metadata-table th { background-color: #f2f2f2; width: 30%; }",
                "        .metadata-table tr:nth-child(even) { background-color: #f9f9f9; }",
                "        .image-preview { max-width: 500px; max-height: 500px; margin-bottom: 20px; }",
                "        .timestamp { color: #7f8c8d; font-size: 0.9em; margin-top: 10px; }",
                "        .footer { margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; color: #7f8c8d; font-size: 0.9em; }",
                "        .risk-low { color: green; }",
                "        .risk-medium { color: orange; }",
                "        .risk-high { color: red; }",
                "    </style>",
                "</head>",
                "<body>",
                f"    <h1>{title}</h1>"
            ]
            
            # Add company name if provided
            if company_name:
                html.append(f"    <p>Prepared by: {company_name}</p>")
            
            # Add timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            html.append(f"    <p class='timestamp'>Generated: {timestamp}</p>")
            
            # Add image preview if available
            if include_preview and image_path and os.path.exists(image_path):
                html.append("    <div class='metadata-section'>")
                html.append("        <h2>Image Preview</h2>")
                
                # Create a copy of the image in the same directory as the HTML file
                if PIL_AVAILABLE:
                    try:
                        # Create preview directory
                        preview_dir = os.path.join(os.path.dirname(output_file), 'preview')
                        os.makedirs(preview_dir, exist_ok=True)
                        
                        # Create preview filename
                        preview_filename = os.path.join(preview_dir, f"preview_{os.path.basename(image_path)}")
                        
                        # Create preview image
                        img = Image.open(image_path)
                        img.thumbnail((500, 500), Image.LANCZOS)
                        img.save(preview_filename)
                        
                        # Add relative path to HTML
                        rel_path = os.path.relpath(preview_filename, os.path.dirname(output_file))
                        html.append(f"        <img src='{rel_path}' class='image-preview' alt='Image preview'>")
                    except Exception as e:
                        logger.warning(f"Error creating image preview for HTML: {e}")
                        # Fallback to direct reference
                        html.append(f"        <img src='file://{image_path.replace(' ', '%20')}' class='image-preview' alt='Image preview'>")
                else:
                    # Direct reference if PIL is not available
                    html.append(f"        <img src='file://{image_path.replace(' ', '%20')}' class='image-preview' alt='Image preview'>")
                
                html.append("    </div>")
            
            # Add file information if available
            if 'FileName' in metadata or 'FilePath' in metadata:
                html.append("    <div class='metadata-section'>")
                html.append("        <h2>File Information</h2>")
                html.append("        <table class='metadata-table'>")
                
                if 'FileName' in metadata:
                    html.append(f"            <tr><th>File Name</th><td>{metadata['FileName']}</td></tr>")
                
                if 'FilePath' in metadata:
                    html.append(f"            <tr><th>File Path</th><td>{metadata['FilePath']}</td></tr>")
                
                if 'FileSize' in metadata and 'FileSizeFormatted' in metadata:
                    html.append(f"            <tr><th>File Size</th><td>{metadata['FileSizeFormatted']}</td></tr>")
                
                if 'FileModifyDate' in metadata:
                    html.append(f"            <tr><th>Modified</th><td>{metadata['FileModifyDate']}</td></tr>")
                
                if 'FileCreateDate' in metadata:
                    html.append(f"            <tr><th>Created</th><td>{metadata['FileCreateDate']}</td></tr>")
                
                html.append("        </table>")
                html.append("    </div>")
            
            # Add each category
            for category_name, category_data in categories.items():
                if not category_data:
                    continue
                
                html.append("    <div class='metadata-section'>")
                html.append(f"        <h2>{category_name}</h2>")
                html.append("        <table class='metadata-table'>")
                
                for key, value in category_data.items():
                    # Format value
                    if isinstance(value, (list, tuple)):
                        value = ', '.join(str(item) for item in value)
                    elif not isinstance(value, str):
                        value = str(value)
                    
                    # Escape HTML special characters
                    value = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    
                    html.append(f"            <tr><th>{key}</th><td>{value}</td></tr>")
                
                html.append("        </table>")
                html.append("    </div>")
            
            # Add privacy assessment if available
            if 'PrivacyAssessment' in metadata:
                html.append("    <div class='metadata-section'>")
                html.append("        <h2>Privacy Assessment</h2>")
                html.append("        <table class='metadata-table'>")
                
                privacy = metadata['PrivacyAssessment']
                
                if 'PrivacyRisk' in privacy:
                    risk_level = privacy['PrivacyRisk']
                    risk_class = f"risk-{risk_level.lower()}"
                    html.append(f"            <tr><th>Privacy Risk Level</th><td class='{risk_class}'>{risk_level}</td></tr>")
                
                if 'SensitiveDataPresent' in privacy:
                    html.append(f"            <tr><th>Sensitive Data Present</th><td>{'Yes' if privacy['SensitiveDataPresent'] else 'No'}</td></tr>")
                
                if 'SensitiveFields' in privacy and privacy['SensitiveFields']:
                    fields = ', '.join(privacy['SensitiveFields'])
                    html.append(f"            <tr><th>Sensitive Fields</th><td>{fields}</td></tr>")
                
                html.append("        </table>")
                
                # Add recommendations
                if 'Recommendations' in privacy and privacy['Recommendations']:
                    html.append("        <h3>Recommendations:</h3>")
                    html.append("        <ul>")
                    
                    for recommendation in privacy['Recommendations']:
                        html.append(f"            <li>{recommendation}</li>")
                    
                    html.append("        </ul>")
                
                html.append("    </div>")
            
            # Add footer
            html.append("    <div class='footer'>")
            html.append("        Generated by Image Metadata Extractor")
            html.append("    </div>")
            
            # Close HTML
            html.append("</body>")
            html.append("</html>")
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(html))
            
            logger.info(f"Saved metadata to HTML: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving metadata to HTML: {e}")
            return False
    
    def save_yaml(self, metadata: Dict[str, Any], output_file: str) -> bool:
        """
        Save metadata to a YAML file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            
        Returns:
            True if successful, False otherwise
        """
        if not YAML_AVAILABLE:
            logger.error("PyYAML library not available. Cannot save to YAML.")
            return False
        
        try:
            # Convert non-serializable objects to strings
            serializable_metadata = self._make_serializable(metadata)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(serializable_metadata, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Saved metadata to YAML: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving metadata to YAML: {e}")
            return False
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        Flatten a nested dictionary.
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key for nested dictionaries
            sep: Separator for keys
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict) and v:
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, (list, tuple)) and v and isinstance(v[0], dict):
                # Handle list of dictionaries
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    def _make_serializable(self, obj: Any) -> Any:
        """
        Convert non-serializable objects to serializable types.
        
        Args:
            obj: Object to convert
            
        Returns:
            Serializable object
        """
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(x) for x in obj]
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return self._make_serializable(obj.__dict__)
        else:
            return str(obj)
    
    def _categorize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Categorize metadata into logical groups.
        
        Args:
            metadata: Dictionary containing metadata
            
        Returns:
            Dictionary with categorized metadata
        """
        categories = {
            'Basic Information': {},
            'Camera Information': {},
            'Lens Information': {},
            'Exposure Information': {},
            'GPS Information': {},
            'EXIF Data': {},
            'IPTC Data': {},
            'XMP Data': {},
            'File Information': {},
            'Other Metadata': {}
        }
        
        # Skip these keys as they're handled separately
        skip_keys = ['PrivacyAssessment']
        
        for key, value in metadata.items():
            if key in skip_keys:
                continue
            
            # File information
            if key.startswith('File') or key in ['FileName', 'FilePath', 'FileSize', 'FileSizeFormatted']:
                categories['File Information'][key] = value
            
            # Basic information
            elif key in ['ImageWidth', 'ImageHeight', 'ImageSize', 'Megapixels', 'AspectRatio', 'ColorSpace', 'BitsPerPixel']:
                categories['Basic Information'][key] = value
            
            # Camera information
            elif key in ['Make', 'Model', 'DeviceMake', 'DeviceModel', 'DeviceType', 'Software', 'CameraSerialNumber', 'DeviceSerialNumber']:
                categories['Camera Information'][key] = value
            
            # Lens information
            elif 'Lens' in key or key in ['FocalLength', 'FocalLength35mm']:
                categories['Lens Information'][key] = value
            
            # Exposure information
            elif key in ['Aperture', 'ShutterSpeed', 'ISO', 'ExposureTime', 'ExposureProgram', 'ExposureMode', 'ExposureCompensation', 'MeteringMode', 'Flash', 'WhiteBalance']:
                categories['Exposure Information'][key] = value
            
            # GPS information
            elif key.startswith('GPS') or key in ['Latitude', 'Longitude', 'Altitude', 'Location', 'LocationName', 'City', 'State', 'Country']:
                categories['GPS Information'][key] = value
            
            # EXIF data
            elif key.startswith('EXIF:') or key.startswith('EXIF'):
                categories['EXIF Data'][key] = value
            
            # IPTC data
            elif key.startswith('IPTC:') or key.startswith('IPTC'):
                categories['IPTC Data'][key] = value
            
            # XMP data
            elif key.startswith('XMP:') or key.startswith('XMP'):
                categories['XMP Data'][key] = value
            
            # Other metadata
            else:
                categories['Other Metadata'][key] = value
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def copy_file(self, source_path: str, dest_path: str) -> bool:
        """
        Copy a file from source to destination.
        
        Args:
            source_path: Path to the source file
            dest_path: Path to the destination file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            shutil.copy2(source_path, dest_path)
            logger.info(f"Copied file from {source_path} to {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Error copying file: {e}")
            return False
    
    def create_backup(self, file_path: str) -> Optional[str]:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file, or None if backup failed
        """
        try:
            # Create backup filename
            backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.basename(file_path)
            backup_path = os.path.join(backup_dir, f"{os.path.splitext(filename)[0]}_{timestamp}{os.path.splitext(filename)[1]}")
            
            # Copy file to backup
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup of {file_path} at {backup_path}")
            
            return backup_path
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def restore_backup(self, backup_path: str, original_path: str) -> bool:
        """
        Restore a file from backup.
        
        Args:
            backup_path: Path to the backup file
            original_path: Path to restore to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            shutil.copy2(backup_path, original_path)
            logger.info(f"Restored backup from {backup_path} to {original_path}")
            return True
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def list_backups(self, file_path: str) -> List[str]:
        """
        List available backups for a file.
        
        Args:
            file_path: Path to the original file
            
        Returns:
            List of backup file paths
        """
        try:
            # Get backup directory
            backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
            if not os.path.exists(backup_dir):
                return []
            
            # Get filename without extension
            filename_base = os.path.splitext(os.path.basename(file_path))[0]
            ext = os.path.splitext(file_path)[1]
            
            # Find matching backups
            pattern = re.compile(f"^{re.escape(filename_base)}_\\d{{8}}_\\d{{6}}{re.escape(ext)}$")
            backups = []
            
            for filename in os.listdir(backup_dir):
                if pattern.match(filename):
                    backups.append(os.path.join(backup_dir, filename))
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            return backups
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def delete_backup(self, backup_path: str) -> bool:
        """
        Delete a backup file.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.remove(backup_path)
            logger.info(f"Deleted backup: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            return False
    
    def create_temp_directory(self) -> Optional[str]:
        """
        Create a temporary directory.
        
        Returns:
            Path to the temporary directory, or None if creation failed
        """
        try:
            temp_dir = tempfile.mkdtemp(prefix="image_metadata_extractor_")
            logger.debug(f"Created temporary directory: {temp_dir}")
            return temp_dir
        except Exception as e:
            logger.error(f"Error creating temporary directory: {e}")
            return None
    
    def cleanup_temp_directory(self, temp_dir: str) -> bool:
        """
        Clean up a temporary directory.
        
        Args:
            temp_dir: Path to the temporary directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up temporary directory: {e}")
            return False
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """
        Get supported file formats for import and export.
        
        Returns:
            Dictionary with supported formats
        """
        import_formats = [
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp'
        ]
        
        # Add HEIC/HEIF if PIL supports it
        if PIL_AVAILABLE:
            try:
                from PIL import features
                if features.check('libjpeg_turbo'):
                    import_formats.extend(['.heic', '.heif'])
            except (ImportError, AttributeError):
                pass
        
        export_formats = {
            'CSV': ['.csv'],
            'JSON': ['.json'],
            'Text': ['.txt'],
            'Excel': ['.xlsx'] if PANDAS_AVAILABLE else [],
            'PDF': ['.pdf'] if REPORTLAB_AVAILABLE else [],
            'HTML': ['.html'],
            'YAML': ['.yaml', '.yml'] if YAML_AVAILABLE else []
        }
        
        return {
            'import': import_formats,
            'export': export_formats
        }
    
    def batch_process(self, file_paths: List[str], output_dir: str, output_format: str, **kwargs) -> Dict[str, Any]:
        """
        Process multiple files in batch mode.
        
        Args:
            file_paths: List of file paths to process
            output_dir: Directory to save output files
            output_format: Format to save in (csv, json, etc.)
            **kwargs: Additional options for specific formats
            
        Returns:
            Dictionary with processing results
        """
        results = {
            'total': len(file_paths),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                logger.error(f"Error creating output directory: {e}")
                results['errors'].append(f"Failed to create output directory: {str(e)}")
                return results
        
        # Process each file
        for file_path in file_paths:
            try:
                # Check if file exists and is a valid image
                if not os.path.exists(file_path):
                    results['skipped'] += 1
                    results['errors'].append(f"File not found: {file_path}")
                    continue
                
                if not self.is_valid_image(file_path):
                    results['skipped'] += 1
                    results['errors'].append(f"Not a valid image: {file_path}")
                    continue
                
                # Get base filename without extension
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # Create output filename
                output_file = os.path.join(output_dir, f"{base_name}_metadata.{output_format}")
                
                # Extract metadata (this would be done by the MetadataExtractor class)
                # For this file, we'll just assume metadata is provided externally
                metadata = kwargs.get('metadata_extractor', None)
                
                if metadata is None:
                    results['skipped'] += 1
                    results['errors'].append(f"No metadata extractor provided for: {file_path}")
                    continue
                
                # Extract metadata for this file
                if callable(metadata):
                    try:
                        file_metadata = metadata(file_path)
                    except Exception as e:
                        results['failed'] += 1
                        results['errors'].append(f"Metadata extraction failed for {file_path}: {str(e)}")
                        continue
                else:
                    # Assume metadata is a dictionary
                    file_metadata = metadata
                
                # Save metadata in the specified format
                success = False
                
                if output_format == 'csv':
                    success = self.save_csv(file_metadata, output_file)
                elif output_format == 'json':
                    success = self.save_json(file_metadata, output_file)
                elif output_format == 'txt':
                    success = self.save_text(file_metadata, output_file)
                elif output_format == 'xlsx':
                    success = self.save_excel(file_metadata, output_file)
                elif output_format == 'pdf':
                    success = self.save_pdf(file_metadata, output_file, image_path=file_path)
                elif output_format == 'html':
                    success = self.save_html(file_metadata, output_file, image_path=file_path)
                elif output_format in ('yaml', 'yml'):
                    success = self.save_yaml(file_metadata, output_file)
                else:
                    results['skipped'] += 1
                    results['errors'].append(f"Unsupported output format: {output_format}")
                    continue
                
                if success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to save metadata for: {file_path}")
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error processing {file_path}: {str(e)}")
        
        return results
    
    def validate_output_directory(self, directory: str) -> Tuple[bool, str]:
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
            except Exception as e:
                return False, f"Could not create directory: {str(e)}"
        
        # Check if it's a directory
        if not os.path.isdir(directory):
            return False, "Not a directory"
        
        # Check if it's writable
        try:
            test_file = os.path.join(directory, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True, ""
        except Exception as e:
            return False, f"Directory is not writable: {str(e)}"
    
    def get_unique_filename(self, directory: str, base_name: str, extension: str) -> str:
        """
        Get a unique filename in a directory.
        
        Args:
            directory: Directory for the file
            base_name: Base filename
            extension: File extension
            
        Returns:
            Unique filename
        """
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
    
    def save_session(self, session_data: Dict[str, Any], session_file: str) -> bool:
        """
        Save a session to a file.
        
        Args:
            session_data: Session data to save
            session_file: Path to the session file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert non-serializable objects to strings
            serializable_data = self._make_serializable(session_data)
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2)
            
            logger.info(f"Saved session to: {session_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False
    
    def load_session(self, session_file: str) -> Optional[Dict[str, Any]]:
        """
        Load a session from a file.
        
        Args:
            session_file: Path to the session file
            
        Returns:
            Session data or None if loading failed
        """
        try:
            if not os.path.exists(session_file):
                logger.error(f"Session file not found: {session_file}")
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            logger.info(f"Loaded session from: {session_file}")
            return session_data
            
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return None
    
    def get_file_hash(self, file_path: str, algorithm: str = 'sha256') -> Optional[str]:
        """
        Calculate the hash of a file.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use (md5, sha1, sha256, etc.)
            
        Returns:
            File hash or None if calculation failed
        """
        try:
            import hashlib
            
            # Get the hash algorithm
            hash_func = getattr(hashlib, algorithm)()
            
            # Calculate hash
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return None