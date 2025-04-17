# ImageMetadataExtractor

A powerful desktop application for extracting, viewing, and analyzing metadata from image files. This tool helps photographers, digital forensics specialists, and privacy-conscious users to examine the hidden information stored in their images.

## Features

- **Comprehensive Metadata Extraction**: Extract EXIF, IPTC, XMP, and other metadata from various image formats
- **GPS Data Visualization**: Parse and display GPS coordinates with map integration
- **Device Identification**: Identify camera, smartphone, or other devices used to capture images
- **Batch Processing**: Process multiple images at once
- **Export Options**: Save results in various formats (CSV, JSON, TXT)
- **User-Friendly Interface**: Clean and intuitive GUI built with Tkinter

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/RavindharCYS/Image-Extractor.git
cd ImageMetadataExtractor
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application
```bash
python main.py
```

### How to Use the Tool

#### Basic Usage
1. Launch the application: Run `python main.py`
2. Open an image file:
   - Click the "Open File" button in the toolbar
   - Or use the menu: File → Open
   - Or use the keyboard shortcut: Ctrl+O (Cmd+O on Mac)
3. View metadata: Once an image is loaded, the metadata will be displayed in the main panel
4. Navigate metadata categories: Use the tabs to switch between different metadata categories (EXIF, IPTC, XMP, etc.)

#### Working with GPS Data
- View GPS coordinates: If the image contains GPS data, it will be displayed in the "Location" tab
- View on map: Click the "Show on Map" button to open the coordinates in an interactive map
- Copy coordinates: Use the copy button next to the coordinates to copy them to clipboard
- Export location data: Use the "Export GPS Data" option in the Export menu

#### Batch Processing
1. Select multiple files:
   - Use the menu: File → Batch Process
   - Or use the keyboard shortcut: Ctrl+B (Cmd+B on Mac)
2. Choose processing options:
   - Select which metadata to extract
   - Choose export format and location
3. Start processing: Click "Process Files" to begin extraction
4. View results: Results will be saved to the specified location and a summary will be displayed

#### Exporting Data
- Export current file metadata:
  - Use the menu: File → Export → [Format]
  - Or use the toolbar export button
- Available export formats:
  - JSON: Comprehensive metadata in structured format
  - CSV: Tabular format suitable for spreadsheets
  - TXT: Simple text format for easy reading
  - HTML: Formatted report with categories and sections
- Custom export: Use File → Export → Custom to select specific metadata fields to export

#### Advanced Features
- Metadata comparison:
  - Open two images and use Tools → Compare Metadata
  - Differences will be highlighted for easy identification
- Metadata editing (when available):
  - Select a metadata field and click the edit icon
  - Enter new value and save changes
  - Note: Some metadata fields cannot be modified
- Privacy check:
  - Use Tools → Privacy Check to identify personal information in metadata
  - Option to remove sensitive data with Tools → Remove Personal Info

### Command Line Usage

The application also supports command-line operation:

```bash
# Extract metadata from a single file
python main.py --file path/to/image.jpg

# Export metadata to a specific format
python main.py --file path/to/image.jpg --export path/to/output.json

# Batch process multiple files
python main.py --batch "folder/with/images/*.jpg" --export output_folder

# Extract only specific metadata tags
python main.py --file image.jpg --tags "Make,Model,DateTimeOriginal"

# Remove personal information
python main.py --file image.jpg --remove-personal --save
```

## Project Structure

```
ImageMetadataExtractor/
│
├── main.py                  # Entry point for the application
├── requirements.txt         # Dependencies
│
├── src/
│   ├── __init__.py
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py   # Main Tkinter window
│   │   ├── result_view.py   # Results display component
│   │   ├── menu_bar.py      # Application menu
│   │   └── styles.py        # UI styles and themes
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── metadata_extractor.py  # Core extraction functionality
│   │   ├── gps_parser.py          # GPS data parsing and conversion
│   │   ├── device_identifier.py   # Device identification logic
│   │   └── file_handler.py        # File operations
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py        # Logging functionality
│       ├── validators.py    # Input validation
│       └── exporters.py     # Export results to different formats
│
└── resources/
    ├── icons/              # Application icons
    └── sample_images/      # Sample images for testing
```

## Troubleshooting

### Common Issues

- **Application won't start**:
  - Ensure all dependencies are installed: `pip install -r requirements.txt`
  - Check Python version: `python --version` (should be 3.7+)

- **No metadata displayed**:
  - Verify the image format is supported
  - Some images may not contain metadata
  - Try the sample images in the resources folder

- **GPS data not showing**:
  - Not all images contain GPS information
  - Check if location services were enabled when the photo was taken

- **Export fails**:
  - Ensure you have write permissions to the destination folder
  - Check disk space availability

### Getting Help

If you encounter issues not covered here:
- Check the Issues page
- Submit a new issue with detailed information about your problem
- Contact the maintainer at your.email@example.com

## Development

### Running Tests
```bash
python -m unittest discover tests
```

### Adding New Features
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Dependencies

- **Pillow**: Image processing
- **ExifTool**: Advanced metadata extraction
- **TkInter**: GUI framework
- **Folium**: Map visualization (for GPS data)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Phil Harvey for ExifTool
- The Python Pillow team
- All contributors who have helped improve this tool

## Screenshots

### Main Application Window
Main application interface showing extracted metadata

### GPS Data Visualization
GPS data visualization on an interactive map

## Contact

Your Name - ravindhar.upm@gmail.com

Project Link: https://github.com/RavindharCYS/Image-Extractor.git
