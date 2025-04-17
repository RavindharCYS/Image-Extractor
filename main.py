#!/usr/bin/env python3
"""
Image Metadata Extractor - Main Application

A cybersecurity tool for extracting and analyzing metadata from images.
This file serves as the entry point for the application.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure the src package is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.gui.main_window import MainWindow
    from src.utils.logger import setup_exception_logging
except ImportError as e:
    logger.critical(f"Failed to import required modules: {e}")
    messagebox.showerror("Import Error", 
                         f"Failed to load required modules: {e}\n\n"
                         "Please ensure all dependencies are installed.")
    sys.exit(1)


class ImageMetadataExtractorApp:
    """Main application class for the Image Metadata Extractor."""
    
    def __init__(self):
        """Initialize the application."""
        self.root = tk.Tk()
        self.root.title("Image Metadata Extractor")
        
        # Set minimum window size
        self.root.minsize(900, 600)
        
        # Set window icon if available
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            try:
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
            except Exception as e:
                logger.warning(f"Could not load application icon: {e}")
        
        # Apply theme
        self._setup_theme()
        
        # Setup exception handling
        setup_exception_logging()
        
        # Create main window
        self.main_window = MainWindow(self.root)
        
        # Center window on screen
        self._center_window()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        logger.info("Application initialized successfully")

    def _setup_theme(self):
        """Setup the application theme."""
        try:
            # Try to import and use ttkthemes for better looking UI
            from ttkthemes import ThemedStyle
            style = ThemedStyle(self.root)
            style.set_theme("arc")  # Use a modern theme
        except ImportError:
            # Fall back to default style if ttkthemes is not available
            logger.info("ttkthemes not available, using default theme")
            style = ttk.Style()
            style.theme_use('clam' if 'clam' in style.theme_names() else 'default')
        
        # Configure common styles
        style.configure('TButton', font=('Helvetica', 10))
        style.configure('TLabel', font=('Helvetica', 10))
        style.configure('TFrame', background='#f0f0f0')

    def _center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _on_close(self):
        """Handle window close event."""
        # Check if there are any unsaved changes
        if hasattr(self.main_window, 'has_unsaved_changes') and self.main_window.has_unsaved_changes():
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Would you like to save before exiting?"
            )
            
            if response is None:  # Cancel was clicked
                return
            elif response:  # Yes was clicked
                # Call save method if it exists
                if hasattr(self.main_window, 'save_results'):
                    if not self.main_window.save_results():
                        return  # Don't close if save was cancelled
        
        logger.info("Application shutting down")
        self.root.destroy()

    def run(self):
        """Run the application main loop."""
        try:
            # Display a splash screen or welcome message
            self.main_window.show_welcome_message()
            
            # Start the main event loop
            self.root.mainloop()
        except Exception as e:
            logger.critical(f"Unhandled exception in main loop: {e}", exc_info=True)
            messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}")
        finally:
            # Cleanup resources if needed
            logger.info("Application terminated")


def main():
    """Application entry point."""
    try:
        # Check Python version
        if sys.version_info < (3, 6):
            messagebox.showerror(
                "Unsupported Python Version",
                "This application requires Python 3.6 or higher."
            )
            sys.exit(1)
            
        # Check for required dependencies
        try:
            import PIL
            import exifread
        except ImportError as e:
            messagebox.showerror(
                "Missing Dependencies",
                f"Required dependency not found: {e}\n\n"
                "Please install all required dependencies using:\n"
                "pip install -r requirements.txt"
            )
            sys.exit(1)
            
        # Start the application
        app = ImageMetadataExtractorApp()
        app.run()
        
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        messagebox.showerror(
            "Startup Error",
            f"Failed to start the application:\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()