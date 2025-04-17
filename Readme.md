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
├── tests/                   # Unit tests
│   ├── __init__.py
│   ├── test_metadata_extractor.py
│   ├── test_gps_parser.py
│   └── test_device_identifier.py
│
└── resources/
    ├── icons/              # Application icons
    └── sample_images/      # Sample images for testing