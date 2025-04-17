"""
Exporters Module

This module provides functionality for exporting metadata to various formats,
including CSV, JSON, XML, PDF, HTML, and more.
"""

import os
import csv
import json
import logging
import xml.dom.minidom
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, TextIO, BinaryIO, Tuple

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


class MetadataExporter:
    """
    A class for exporting metadata to various formats.
    
    This class provides methods to export metadata to different file formats
    such as CSV, JSON, XML, PDF, HTML, and more.
    """
    
    def __init__(self):
        """Initialize the MetadataExporter."""
        logger.debug("MetadataExporter initialized")
    
    def export_to_csv(self, metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Export metadata to a CSV file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            **kwargs: Additional options
                - delimiter: CSV delimiter (default: ',')
                - quotechar: CSV quote character (default: '"')
                - flatten: Whether to flatten nested dictionaries (default: True)
                - encoding: File encoding (default: 'utf-8')
                
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get options
            delimiter = kwargs.get('delimiter', ',')
            quotechar = kwargs.get('quotechar', '"')
            flatten = kwargs.get('flatten', True)
            encoding = kwargs.get('encoding', 'utf-8')
            
            # Flatten nested dictionaries if requested
            if flatten:
                flattened_metadata = self._flatten_dict(metadata)
            else:
                flattened_metadata = metadata
            
            with open(output_file, 'w', newline='', encoding=encoding) as f:
                writer = csv.writer(f, delimiter=delimiter, quotechar=quotechar)
                
                # Write header
                writer.writerow(['Property', 'Value'])
                
                # Write data
                for key, value in flattened_metadata.items():
                    writer.writerow([key, self._format_value(value)])
            
            logger.info(f"Exported metadata to CSV: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def export_to_json(self, metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Export metadata to a JSON file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            **kwargs: Additional options
                - indent: JSON indentation (default: 2)
                - ensure_ascii: Whether to escape non-ASCII characters (default: False)
                - encoding: File encoding (default: 'utf-8')
                
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get options
            indent = kwargs.get('indent', 2)
            ensure_ascii = kwargs.get('ensure_ascii', False)
            encoding = kwargs.get('encoding', 'utf-8')
            
            # Convert non-serializable objects to strings
            serializable_metadata = self._make_serializable(metadata)
            
            with open(output_file, 'w', encoding=encoding) as f:
                json.dump(serializable_metadata, f, indent=indent, ensure_ascii=ensure_ascii)
            
            logger.info(f"Exported metadata to JSON: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False
    
    def export_to_xml(self, metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Export metadata to an XML file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            **kwargs: Additional options
                - root_element: Name of the root element (default: 'Metadata')
                - indent: XML indentation (default: '  ')
                - encoding: File encoding (default: 'utf-8')
                
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get options
            root_element = kwargs.get('root_element', 'Metadata')
            indent = kwargs.get('indent', '  ')
            encoding = kwargs.get('encoding', 'utf-8')
            
            # Create root element
            root = ET.Element(root_element)
            
            # Add timestamp
            timestamp = ET.SubElement(root, 'Timestamp')
            timestamp.text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Add metadata
            self._dict_to_xml(metadata, root)
            
            # Create XML tree
            tree = ET.ElementTree(root)
            
            # Convert to string and pretty-print
            xml_string = ET.tostring(root, encoding=encoding)
            dom = xml.dom.minidom.parseString(xml_string)
            pretty_xml = dom.toprettyxml(indent=indent, encoding=encoding)
            
            # Write to file
            with open(output_file, 'wb') as f:
                f.write(pretty_xml)
            
            logger.info(f"Exported metadata to XML: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to XML: {e}")
            return False
    
    def export_to_text(self, metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Export metadata to a plain text file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            **kwargs: Additional options
                - flatten: Whether to flatten nested dictionaries (default: True)
                - encoding: File encoding (default: 'utf-8')
                - include_header: Whether to include a header (default: True)
                - categorize: Whether to categorize metadata (default: True)
                
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get options
            flatten = kwargs.get('flatten', True)
            encoding = kwargs.get('encoding', 'utf-8')
            include_header = kwargs.get('include_header', True)
            categorize = kwargs.get('categorize', True)
            
            with open(output_file, 'w', encoding=encoding) as f:
                # Write header
                if include_header:
                    f.write("IMAGE METADATA REPORT\n")
                    f.write("=" * 50 + "\n\n")
                    
                    # Add timestamp
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write data
                if categorize:
                    # Categorize metadata
                    categories = self._categorize_metadata(metadata)
                    
                    # Write each category
                    for category_name, category_data in categories.items():
                        f.write(f"{category_name}\n")
                        f.write("-" * len(category_name) + "\n")
                        
                        if flatten:
                            flattened_data = self._flatten_dict(category_data)
                            for key, value in flattened_data.items():
                                f.write(f"{key}: {self._format_value(value)}\n")
                        else:
                            self._write_dict_to_text(category_data, f)
                        
                        f.write("\n")
                else:
                    # Write all metadata without categorization
                    if flatten:
                        flattened_metadata = self._flatten_dict(metadata)
                        for key, value in flattened_metadata.items():
                            f.write(f"{key}: {self._format_value(value)}\n")
                    else:
                        self._write_dict_to_text(metadata, f)
            
            logger.info(f"Exported metadata to text file: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to text file: {e}")
            return False
    
    def export_to_excel(self, metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Export metadata to an Excel file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            **kwargs: Additional options
                - flatten: Whether to flatten nested dictionaries (default: True)
                - sheet_name: Name of the worksheet (default: 'Metadata')
                - categorize: Whether to create separate worksheets for categories (default: True)
                
        Returns:
            True if successful, False otherwise
        """
        if not PANDAS_AVAILABLE:
            logger.error("pandas library not available. Cannot export to Excel.")
            return False
        
        try:
            # Get options
            flatten = kwargs.get('flatten', True)
            sheet_name = kwargs.get('sheet_name', 'Metadata')
            categorize = kwargs.get('categorize', True)
            
            # Create Excel writer
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                if categorize:
                    # Categorize metadata
                    categories = self._categorize_metadata(metadata)
                    
                    # Create a worksheet for each category
                    for category_name, category_data in categories.items():
                        # Flatten if requested
                        if flatten:
                            data = self._flatten_dict(category_data)
                        else:
                            data = category_data
                        
                        # Convert to DataFrame
                        df = pd.DataFrame(list(data.items()), columns=['Property', 'Value'])
                        
                        # Write to Excel
                        sheet_name = category_name[:31]  # Excel sheet names limited to 31 chars
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        # Auto-adjust column widths
                        worksheet = writer.sheets[sheet_name]
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
                else:
                    # Flatten if requested
                    if flatten:
                        data = self._flatten_dict(metadata)
                    else:
                        data = metadata
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(list(data.items()), columns=['Property', 'Value'])
                    
                    # Write to Excel
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Auto-adjust column widths
                    worksheet = writer.sheets[sheet_name]
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
            
            logger.info(f"Exported metadata to Excel: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False
    
    def export_to_pdf(self, metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Export metadata to a PDF file.
        
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
            logger.error("reportlab library not available. Cannot export to PDF.")
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
                    import tempfile
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
            
            # Categorize metadata
            categories = self._categorize_metadata(metadata)
            
            # Add each category
            for category_name, category_data in categories.items():
                elements.append(Paragraph(category_name, heading_style))
                elements.append(Spacer(1, 0.1 * inch))
                
                # Create table data
                table_data = []
                
                # Flatten the category data
                flattened_data = self._flatten_dict(category_data)
                
                for key, value in flattened_data.items():
                    # Format value
                    formatted_value = self._format_value(value)
                    
                    table_data.append([key, formatted_value])
                
                # Create table
                if table_data:
                    col_widths = [2.5 * inch, 3 * inch]
                    table = Table(table_data, colWidths=col_widths)
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
            
            logger.info(f"Exported metadata to PDF: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            return False
    
    def export_to_html(self, metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Export metadata to an HTML file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            **kwargs: Additional options
                - image_path: Path to the image for preview
                - include_preview: Whether to include image preview (default: True)
                - title: Custom title for the report
                - company_name: Company name for the report header
                - css: Custom CSS string to include
                - template: HTML template file path
                
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get options
            image_path = kwargs.get('image_path', None)
            include_preview = kwargs.get('include_preview', True)
            title = kwargs.get('title', 'Image Metadata Report')
            company_name = kwargs.get('company_name', '')
            css = kwargs.get('css', '')
            template_file = kwargs.get('template', None)
            
            # Use template if provided
            if template_file and os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    template = f.read()
                
                # Replace placeholders in template
                html = self._fill_html_template(template, metadata, image_path, title, company_name)
            else:
                # Generate HTML from scratch
                html = self._generate_html_report(metadata, image_path, include_preview, title, company_name, css)
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            
            logger.info(f"Exported metadata to HTML: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to HTML: {e}")
            return False
    
    def export_to_yaml(self, metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Export metadata to a YAML file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            **kwargs: Additional options
                - default_flow_style: YAML flow style (default: False)
                - encoding: File encoding (default: 'utf-8')
                
        Returns:
            True if successful, False otherwise
        """
        if not YAML_AVAILABLE:
            logger.error("PyYAML library not available. Cannot export to YAML.")
            return False
        
        try:
            # Get options
            default_flow_style = kwargs.get('default_flow_style', False)
            encoding = kwargs.get('encoding', 'utf-8')
            
            # Convert non-serializable objects to strings
            serializable_metadata = self._make_serializable(metadata)
            
            with open(output_file, 'w', encoding=encoding) as f:
                yaml.dump(serializable_metadata, f, default_flow_style=default_flow_style, sort_keys=False)
            
            logger.info(f"Exported metadata to YAML: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to YAML: {e}")
            return False
    
    def export_to_markdown(self, metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Export metadata to a Markdown file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            **kwargs: Additional options
                - image_path: Path to the image for preview
                - include_preview: Whether to include image preview (default: True)
                - title: Custom title for the report
                - encoding: File encoding (default: 'utf-8')
                
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get options
            image_path = kwargs.get('image_path', None)
            include_preview = kwargs.get('include_preview', True)
            title = kwargs.get('title', 'Image Metadata Report')
            encoding = kwargs.get('encoding', 'utf-8')
            
            with open(output_file, 'w', encoding=encoding) as f:
                # Write title
                f.write(f"# {title}\n\n")
                
                # Add timestamp
                f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                
                # Add image preview if available
                if include_preview and image_path and os.path.exists(image_path):
                    # Get relative path to image
                    rel_path = os.path.relpath(image_path, os.path.dirname(output_file))
                    f.write(f"![Image Preview]({rel_path})\n\n")
                
                # Categorize metadata
                categories = self._categorize_metadata(metadata)
                
                # Write each category
                for category_name, category_data in categories.items():
                    f.write(f"## {category_name}\n\n")
                    
                    # Create table header
                    f.write("| Property | Value |\n")
                    f.write("|----------|-------|\n")
                    
                    # Flatten the category data
                    flattened_data = self._flatten_dict(category_data)
                    
                    # Write table rows
                    for key, value in flattened_data.items():
                        # Format value for Markdown
                        formatted_value = str(self._format_value(value)).replace('|', '\\|')
                        
                        # Escape pipe characters in key
                        key = key.replace('|', '\\|')
                        
                        f.write(f"| {key} | {formatted_value} |\n")
                    
                    f.write("\n")
                
                # Add privacy assessment if available
                if 'PrivacyAssessment' in metadata:
                    f.write("## Privacy Assessment\n\n")
                    
                    privacy = metadata['PrivacyAssessment']
                    
                    # Create table
                    f.write("| Property | Value |\n")
                    f.write("|----------|-------|\n")
                    
                    if 'PrivacyRisk' in privacy:
                        f.write(f"| Privacy Risk Level | {privacy['PrivacyRisk']} |\n")
                    
                    if 'SensitiveDataPresent' in privacy:
                        f.write(f"| Sensitive Data Present | {'Yes' if privacy['SensitiveDataPresent'] else 'No'} |\n")
                    
                    if 'SensitiveFields' in privacy and privacy['SensitiveFields']:
                        fields = ', '.join(privacy['SensitiveFields'])
                        f.write(f"| Sensitive Fields | {fields} |\n")
                    
                    f.write("\n")
                    
                    # Add recommendations
                    if 'Recommendations' in privacy and privacy['Recommendations']:
                        f.write("### Recommendations\n\n")
                        
                        for recommendation in privacy['Recommendations']:
                            f.write(f"* {recommendation}\n")
                        
                        f.write("\n")
                
                # Add footer
                f.write("---\n")
                f.write("*Generated by Image Metadata Extractor*\n")
            
            logger.info(f"Exported metadata to Markdown: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to Markdown: {e}")
            return False
    
    def export_to_sqlite(self, metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Export metadata to a SQLite database.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            **kwargs: Additional options
                - table_name: Name of the table (default: 'metadata')
                - flatten: Whether to flatten nested dictionaries (default: True)
                
        Returns:
            True if successful, False otherwise
        """
        try:
            import sqlite3
            
            # Get options
            table_name = kwargs.get('table_name', 'metadata')
            flatten = kwargs.get('flatten', True)
            
            # Flatten metadata if requested
            if flatten:
                data = self._flatten_dict(metadata)
            else:
                data = metadata
            
            # Connect to database
            conn = sqlite3.connect(output_file)
            cursor = conn.cursor()
            
            # Create table
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (property TEXT PRIMARY KEY, value TEXT)")
            
            # Insert data
            for key, value in data.items():
                cursor.execute(
                    f"INSERT OR REPLACE INTO {table_name} (property, value) VALUES (?, ?)",
                    (key, str(self._format_value(value)))
                )
            
            # Commit and close
            conn.commit()
            conn.close()
            
            logger.info(f"Exported metadata to SQLite database: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to SQLite: {e}")
            return False
    
    def export_to_format(self, metadata: Dict[str, Any], output_file: str, format_name: str, **kwargs) -> bool:
        """
        Export metadata to a specified format.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            format_name: Format name (csv, json, xml, etc.)
            **kwargs: Additional options for the specific format
                
        Returns:
            True if successful, False otherwise
        """
        # Map format names to export methods
        format_map = {
            'csv': self.export_to_csv,
            'json': self.export_to_json,
            'xml': self.export_to_xml,
            'txt': self.export_to_text,
            'text': self.export_to_text,
            'xlsx': self.export_to_excel,
            'excel': self.export_to_excel,
            'pdf': self.export_to_pdf,
            'html': self.export_to_html,
            'yaml': self.export_to_yaml,
            'yml': self.export_to_yaml,
            'md': self.export_to_markdown,
            'markdown': self.export_to_markdown,
            'sqlite': self.export_to_sqlite,
            'db': self.export_to_sqlite
        }
        
        # Get the export method
        export_method = format_map.get(format_name.lower())
        
        if export_method:
            return export_method(metadata, output_file, **kwargs)
        else:
            logger.error(f"Unsupported export format: {format_name}")
            return False
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """
        Get supported export formats.
        
        Returns:
            Dictionary with supported formats and their file extensions
        """
        formats = {
            'CSV': ['.csv'],
            'JSON': ['.json'],
            'XML': ['.xml'],
            'Text': ['.txt'],
            'Excel': ['.xlsx'] if PANDAS_AVAILABLE else [],
            'PDF': ['.pdf'] if REPORTLAB_AVAILABLE else [],
            'HTML': ['.html', '.htm'],
            'YAML': ['.yaml', '.yml'] if YAML_AVAILABLE else [],
            'Markdown': ['.md', '.markdown'],
            'SQLite': ['.db', '.sqlite']
        }
        
        return formats
    
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
    
    def _format_value(self, value: Any) -> str:
        """
        Format a value for display.
        
        Args:
            value: Value to format
            
        Returns:
            Formatted string representation of the value
        """
        if value is None:
            return ""
        
        if isinstance(value, (list, tuple)):
            # Format lists and tuples
            if all(isinstance(x, (int, float, str, bool)) for x in value):
                return ", ".join(str(x) for x in value)
            else:
                return str(value)
        
        if isinstance(value, dict):
            # Format dictionaries
            return str(value)
        
        if isinstance(value, datetime):
            # Format datetime objects
            return value.strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert to string
        return str(value)
    
    def _dict_to_xml(self, d: Dict[str, Any], parent: ET.Element) -> None:
        """
        Convert a dictionary to XML elements.
        
        Args:
            d: Dictionary to convert
            parent: Parent XML element
        """
        for key, value in d.items():
            # Create a valid XML element name
            element_name = ''.join(c if c.isalnum() else '_' for c in str(key))
            if element_name[0].isdigit():
                element_name = 'n' + element_name
            
            if isinstance(value, dict):
                # Nested dictionary
                child = ET.SubElement(parent, element_name)
                self._dict_to_xml(value, child)
            elif isinstance(value, (list, tuple)):
                # List or tuple
                if all(isinstance(x, dict) for x in value):
                    # List of dictionaries
                    list_element = ET.SubElement(parent, element_name)
                    for item in value:
                        item_element = ET.SubElement(list_element, 'Item')
                        self._dict_to_xml(item, item_element)
                else:
                    # List of simple values
                    list_element = ET.SubElement(parent, element_name)
                    for item in value:
                        item_element = ET.SubElement(list_element, 'Item')
                        item_element.text = str(item)
            else:
                # Simple value
                child = ET.SubElement(parent, element_name)
                child.text = str(value)
    
    def _write_dict_to_text(self, d: Dict[str, Any], file: TextIO, indent: int = 0) -> None:
        """
        Write a dictionary to a text file with indentation.
        
        Args:
            d: Dictionary to write
            file: File object to write to
            indent: Indentation level
        """
        for key, value in d.items():
            if isinstance(value, dict):
                # Nested dictionary
                file.write(f"{' ' * indent}{key}:\n")
                self._write_dict_to_text(value, file, indent + 2)
            elif isinstance(value, (list, tuple)):
                # List or tuple
                if all(isinstance(x, dict) for x in value):
                    # List of dictionaries
                    file.write(f"{' ' * indent}{key}:\n")
                    for item in value:
                        file.write(f"{' ' * (indent + 2)}- \n")
                        self._write_dict_to_text(item, file, indent + 4)
                else:
                    # List of simple values
                    file.write(f"{' ' * indent}{key}: {self._format_value(value)}\n")
            else:
                # Simple value
                file.write(f"{' ' * indent}{key}: {self._format_value(value)}\n")
    
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
            elif key.startswith('EXIF:') or key.startswith('EXIF '):
                categories['EXIF Data'][key] = value
            
            # IPTC data
            elif key.startswith('IPTC:') or key.startswith('IPTC '):
                categories['IPTC Data'][key] = value
            
            # XMP data
            elif key.startswith('XMP:') or key.startswith('XMP '):
                categories['XMP Data'][key] = value
            
            # Other metadata
            else:
                categories['Other Metadata'][key] = value
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def _generate_html_report(self, metadata: Dict[str, Any], image_path: Optional[str], include_preview: bool, title: str, company_name: str, custom_css: str) -> str:
        """
        Generate an HTML report from metadata.
        
        Args:
            metadata: Dictionary containing metadata
            image_path: Path to the image for preview
            include_preview: Whether to include image preview
            title: Report title
            company_name: Company name
            custom_css: Custom CSS string
            
        Returns:
            HTML string
        """
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
            custom_css,  # Add custom CSS if provided
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
                    preview_dir = os.path.join(os.path.dirname(os.path.abspath(image_path)), 'preview')
                    os.makedirs(preview_dir, exist_ok=True)
                    
                    # Create preview filename
                    preview_filename = os.path.join(preview_dir, f"preview_{os.path.basename(image_path)}")
                    
                    # Create preview image
                    img = Image.open(image_path)
                    img.thumbnail((500, 500), Image.LANCZOS)
                    img.save(preview_filename)
                    
                    # Add relative path to HTML
                    rel_path = os.path.relpath(preview_filename, os.path.dirname(os.path.abspath(image_path)))
                    html.append(f"        <img src='{rel_path}' class='image-preview' alt='Image preview'>")
                except Exception as e:
                    logger.warning(f"Error creating image preview for HTML: {e}")
                    # Fallback to direct reference
                    html.append(f"        <img src='file://{image_path.replace(' ', '%20')}' class='image-preview' alt='Image preview'>")
            else:
                # Direct reference if PIL is not available
                html.append(f"        <img src='file://{image_path.replace(' ', '%20')}' class='image-preview' alt='Image preview'>")
            
            html.append("    </div>")
        
        # Categorize metadata
        categories = self._categorize_metadata(metadata)
        
        # Add each category
        for category_name, category_data in categories.items():
            html.append("    <div class='metadata-section'>")
            html.append(f"        <h2>{category_name}</h2>")
            html.append("        <table class='metadata-table'>")
            
            # Flatten the category data
            flattened_data = self._flatten_dict(category_data)
            
            # Add table rows
            for key, value in flattened_data.items():
                # Format value
                formatted_value = self._format_value(value)
                
                # Escape HTML special characters
                key_html = key.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                value_html = str(formatted_value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                html.append(f"            <tr><th>{key_html}</th><td>{value_html}</td></tr>")
            
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
        
        return '\n'.join(html)
    
    def _fill_html_template(self, template: str, metadata: Dict[str, Any], image_path: Optional[str], title: str, company_name: str) -> str:
        """
        Fill an HTML template with metadata.
        
        Args:
            template: HTML template string
            metadata: Dictionary containing metadata
            image_path: Path to the image for preview
            title: Report title
            company_name: Company name
            
        Returns:
            Filled HTML string
        """
        # Categorize metadata
        categories = self._categorize_metadata(metadata)
        
        # Create HTML for each category
        categories_html = ""
        for category_name, category_data in categories.items():
            # Flatten the category data
            flattened_data = self._flatten_dict(category_data)
            
            # Create table for this category
            category_html = f"""
            <div class='metadata-section'>
                <h2>{category_name}</h2>
                <table class='metadata-table'>
            """
            
            # Add table rows
            for key, value in flattened_data.items():
                # Format value
                formatted_value = self._format_value(value)
                
                # Escape HTML special characters
                key_html = key.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                value_html = str(formatted_value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                category_html += f"    <tr><th>{key_html}</th><td>{value_html}</td></tr>\n"
            
            category_html += """
                </table>
            </div>
            """
            
            categories_html += category_html
        
        # Create privacy assessment HTML if available
        privacy_html = ""
        if 'PrivacyAssessment' in metadata:
            privacy = metadata['PrivacyAssessment']
            
            privacy_html = """
            <div class='metadata-section'>
                <h2>Privacy Assessment</h2>
                <table class='metadata-table'>
            """
            
            if 'PrivacyRisk' in privacy:
                risk_level = privacy['PrivacyRisk']
                risk_class = f"risk-{risk_level.lower()}"
                privacy_html += f"    <tr><th>Privacy Risk Level</th><td class='{risk_class}'>{risk_level}</td></tr>\n"
            
            if 'SensitiveDataPresent' in privacy:
                privacy_html += f"    <tr><th>Sensitive Data Present</th><td>{'Yes' if privacy['SensitiveDataPresent'] else 'No'}</td></tr>\n"
            
            if 'SensitiveFields' in privacy and privacy['SensitiveFields']:
                fields = ', '.join(privacy['SensitiveFields'])
                privacy_html += f"    <tr><th>Sensitive Fields</th><td>{fields}</td></tr>\n"
            
            privacy_html += """
                </table>
            """
            
            # Add recommendations
            if 'Recommendations' in privacy and privacy['Recommendations']:
                privacy_html += """
                <h3>Recommendations:</h3>
                <ul>
                """
                
                for recommendation in privacy['Recommendations']:
                    privacy_html += f"    <li>{recommendation}</li>\n"
                
                privacy_html += """
                </ul>
                """
            
            privacy_html += """
            </div>
            """
        
        # Create image preview HTML if available
        preview_html = ""
        if image_path and os.path.exists(image_path):
            preview_html = """
            <div class='metadata-section'>
                <h2>Image Preview</h2>
            """
            
            # Create a copy of the image in the same directory as the HTML file
            if PIL_AVAILABLE:
                try:
                    # Create preview directory
                    preview_dir = os.path.join(os.path.dirname(os.path.abspath(image_path)), 'preview')
                    os.makedirs(preview_dir, exist_ok=True)
                    
                    # Create preview filename
                    preview_filename = os.path.join(preview_dir, f"preview_{os.path.basename(image_path)}")
                    
                    # Create preview image
                    img = Image.open(image_path)
                    img.thumbnail((500, 500), Image.LANCZOS)
                    img.save(preview_filename)
                    
                    # Add relative path to HTML
                    rel_path = os.path.relpath(preview_filename, os.path.dirname(os.path.abspath(image_path)))
                    preview_html += f"    <img src='{rel_path}' class='image-preview' alt='Image preview'>\n"
                except Exception as e:
                    logger.warning(f"Error creating image preview for HTML: {e}")
                    # Fallback to direct reference
                    preview_html += f"    <img src='file://{image_path.replace(' ', '%20')}' class='image-preview' alt='Image preview'>\n"
            else:
                # Direct reference if PIL is not available
                preview_html += f"    <img src='file://{image_path.replace(' ', '%20')}' class='image-preview' alt='Image preview'>\n"
            
            preview_html += """
            </div>
            """
        
        # Get current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Replace placeholders in template
        html = template
        html = html.replace('{{TITLE}}', title)
        html = html.replace('{{COMPANY_NAME}}', company_name)
        html = html.replace('{{TIMESTAMP}}', timestamp)
        html = html.replace('{{IMAGE_PREVIEW}}', preview_html)
        html = html.replace('{{METADATA_CATEGORIES}}', categories_html)
        html = html.replace('{{PRIVACY_ASSESSMENT}}', privacy_html)
        
        return html


class CSVExporter:
    """
    A specialized exporter for CSV format with additional options.
    """
    
    @staticmethod
    def export(metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Export metadata to a CSV file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            **kwargs: Additional options
                - delimiter: CSV delimiter (default: ',')
                - quotechar: CSV quote character (default: '"')
                - flatten: Whether to flatten nested dictionaries (default: True)
                - encoding: File encoding (default: 'utf-8')
                - include_header: Whether to include header row (default: True)
                - transpose: Whether to transpose rows and columns (default: False)
                
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get options
            delimiter = kwargs.get('delimiter', ',')
            quotechar = kwargs.get('quotechar', '"')
            flatten = kwargs.get('flatten', True)
            encoding = kwargs.get('encoding', 'utf-8')
            include_header = kwargs.get('include_header', True)
            transpose = kwargs.get('transpose', False)
            
            # Flatten nested dictionaries if requested
            if flatten:
                flattened_metadata = MetadataExporter()._flatten_dict(metadata)
            else:
                flattened_metadata = metadata
            
            with open(output_file, 'w', newline='', encoding=encoding) as f:
                writer = csv.writer(f, delimiter=delimiter, quotechar=quotechar)
                
                if transpose:
                    # Transpose: properties as columns, single row of values
                    if include_header:
                        writer.writerow(flattened_metadata.keys())
                    writer.writerow([MetadataExporter()._format_value(v) for v in flattened_metadata.values()])
                else:
                    # Normal: properties as rows
                    if include_header:
                        writer.writerow(['Property', 'Value'])
                    
                    # Write data
                    for key, value in flattened_metadata.items():
                        writer.writerow([key, MetadataExporter()._format_value(value)])
            
            logger.info(f"Exported metadata to CSV: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False


class JSONExporter:
    """
    A specialized exporter for JSON format with additional options.
    """
    
    @staticmethod
    def export(metadata: Dict[str, Any], output_file: str, **kwargs) -> bool:
        """
        Export metadata to a JSON file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to the output file
            **kwargs: Additional options
                - indent: JSON indentation (default: 2)
                - ensure_ascii: Whether to escape non-ASCII characters (default: False)
                - encoding: File encoding (default: 'utf-8')
                - sort_keys: Whether to sort keys (default: False)
                - flatten: Whether to flatten nested dictionaries (default: False)
                
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get options
            indent = kwargs.get('indent', 2)
            ensure_ascii = kwargs.get('ensure_ascii', False)
            encoding = kwargs.get('encoding', 'utf-8')
            sort_keys = kwargs.get('sort_keys', False)
            flatten = kwargs.get('flatten', False)
            
            # Flatten if requested
            if flatten:
                data = MetadataExporter()._flatten_dict(metadata)
            else:
                data = metadata
            
            # Convert non-serializable objects to strings
            serializable_data = MetadataExporter()._make_serializable(data)
            
            with open(output_file, 'w', encoding=encoding) as f:
                json.dump(serializable_data, f, indent=indent, ensure_ascii=ensure_ascii, sort_keys=sort_keys)
            
            logger.info(f"Exported metadata to JSON: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False


# Factory function to get an appropriate exporter
def get_exporter(format_name: str) -> Any:
    """
    Get an exporter for the specified format.
    
    Args:
        format_name: Format name (csv, json, etc.)
        
    Returns:
        Exporter object or function
    """
    format_map = {
        'csv': CSVExporter,
        'json': JSONExporter,
        'default': MetadataExporter()
    }
    
    return format_map.get(format_name.lower(), format_map['default'])


# Convenience function to export metadata
def export_metadata(metadata: Dict[str, Any], output_file: str, format_name: Optional[str] = None, **kwargs) -> bool:
    """
    Export metadata to a file.
    
    Args:
        metadata: Dictionary containing metadata
        output_file: Path to the output file
        format_name: Format name (if None, determined from file extension)
        **kwargs: Additional options for the specific format
        
    Returns:
        True if successful, False otherwise
    """
    # Determine format from file extension if not specified
    if format_name is None:
        _, ext = os.path.splitext(output_file)
        format_name = ext[1:] if ext.startswith('.') else ext
    
    # Get appropriate exporter
    exporter = get_exporter(format_name)
    
    # Export using the exporter
    if hasattr(exporter, 'export'):
        return exporter.export(metadata, output_file, **kwargs)
    else:
        return exporter.export_to_format(metadata, output_file, format_name, **kwargs)