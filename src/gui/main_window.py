"""
Main Window Module for Image Metadata Extractor

This module contains the MainWindow class which serves as the primary
controller and view for the application.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from PIL import Image, ImageTk
import traceback

# Get the package logger
logger = logging.getLogger(__name__)

# Import from other modules
try:
    from ..core.metadata_extractor import MetadataExtractor
    from ..core.file_handler import FileHandler
    from ..utils.validators import is_valid_image
    from .result_view import ResultView
    from .menu_bar import MenuBar
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    raise ImportError(f"Failed to import required modules: {e}")


class MainWindow:
    """Main window for the Image Metadata Extractor application."""
    
    def __init__(self, root):
        """
        Initialize the main window.
        
        Args:
            root: The tkinter root window
        """
        self.root = root
        self.root.title("Image Metadata Extractor")
        
        # Initialize core components
        self.file_handler = FileHandler()
        self.metadata_extractor = MetadataExtractor()
        
        # Track state
        self.current_file = None
        self.current_metadata = None
        self.processing = False
        self._unsaved_changes = False
        
        # Setup UI
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()
        
        # Create menu bar
        self.menu_bar = MenuBar(self.root, self)
        self.root.config(menu=self.menu_bar)
        
        logger.info("Main window initialized")
    
    def _create_widgets(self):
        """Create all widgets for the main window."""
        # Create main frame with padding
        self.main_frame = ttk.Frame(self.root, padding="10")
        
        # Create paned window for resizable sections
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        
        # Left panel - File browser and image preview
        self.left_panel = ttk.Frame(self.paned_window)
        
        # File browser section
        self.file_frame = ttk.LabelFrame(self.left_panel, text="Image Files")
        
        # File browser buttons
        self.file_buttons_frame = ttk.Frame(self.file_frame)
        self.open_button = ttk.Button(self.file_buttons_frame, text="Open Image", 
                                     command=self.open_file)
        self.batch_button = ttk.Button(self.file_buttons_frame, text="Batch Process", 
                                      command=self.batch_process)
        
        # Drag and drop area
        self.drop_frame = ttk.Frame(self.file_frame, borderwidth=2, relief="groove", 
                                   padding=20, width=200, height=100)
        self.drop_label = ttk.Label(self.drop_frame, 
                                   text="Drag and drop image files here\nor click to select")
        self.drop_label.bind("<Button-1>", lambda e: self.open_file())
        
        # Image preview section
        self.preview_frame = ttk.LabelFrame(self.left_panel, text="Image Preview")
        self.preview_canvas = tk.Canvas(self.preview_frame, bg="white", 
                                       width=300, height=300)
        self.preview_info = ttk.Label(self.preview_frame, text="No image loaded", 
                                     justify=tk.CENTER)
        
        # Right panel - Results
        self.right_panel = ttk.Frame(self.paned_window)
        
        # Results section
        self.results_frame = ttk.LabelFrame(self.right_panel, text="Metadata Results")
        self.result_view = ResultView(self.results_frame)
        
        # Status bar
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.progress_bar = ttk.Progressbar(self.status_frame, mode="indeterminate", 
                                           length=200)
        
        # Action buttons
        self.button_frame = ttk.Frame(self.right_panel)
        self.extract_button = ttk.Button(self.button_frame, text="Extract Metadata", 
                                        command=self.extract_metadata)
        self.save_button = ttk.Button(self.button_frame, text="Save Results", 
                                     command=self.save_results, state=tk.DISABLED)
        self.clear_button = ttk.Button(self.button_frame, text="Clear", 
                                      command=self.clear_results)
    
    def _setup_layout(self):
        """Arrange widgets using grid layout manager."""
        # Main frame fills the window
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Paned window for resizable sections
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Add panels to paned window
        self.paned_window.add(self.left_panel, weight=1)
        self.paned_window.add(self.right_panel, weight=2)
        
        # Left panel layout
        self.file_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # File browser buttons
        self.file_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        self.open_button.pack(side=tk.LEFT, padx=5)
        self.batch_button.pack(side=tk.LEFT, padx=5)
        
        # Drag and drop area
        self.drop_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.drop_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Image preview
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.preview_info.pack(fill=tk.X, padx=5, pady=5)
        
        # Right panel layout
        self.button_frame.pack(fill=tk.X, padx=5, pady=5)
        self.extract_button.pack(side=tk.LEFT, padx=5)
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.result_view.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.status_label.pack(side=tk.LEFT, padx=5)
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
    
    def _setup_bindings(self):
        """Setup event bindings for widgets."""
        # Drag and drop bindings
        try:
            # Try to use TkinterDnD2 if available
            self.root.tk.eval('package require tkdnd')
            
            from tkdnd import DND_FILES
            
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self._on_drop)
            self.drop_frame.dnd_bind('<<DragEnter>>', lambda e: self.drop_frame.state(["active"]))
            self.drop_frame.dnd_bind('<<DragLeave>>', lambda e: self.drop_frame.state(["!active"]))
            
            logger.info("TkinterDnD2 drag and drop enabled")
        except Exception as e:
            # TkDND might not be available, use alternative method or disable
            logger.warning(f"TkDND not available, drag and drop disabled: {e}")
            self.drop_label.configure(text="Click to select image files\n(Drag & drop not available)")
    
    def _on_drop(self, event):
        """Handle file drop events."""
        self.drop_frame.state(["!active"])
        
        # Get the dropped file path
        file_path = event.data
        
        # Clean up the path (handle platform differences and quotes)
        if file_path.startswith("{") and file_path.endswith("}"):
            file_path = file_path[1:-1]
        if file_path.startswith("'") and file_path.endswith("'"):
            file_path = file_path[1:-1]
        
        # Process the file
        if os.path.isfile(file_path) and is_valid_image(file_path):
            self.load_file(file_path)
        else:
            messagebox.showerror("Invalid File", 
                                "The dropped file is not a valid image file.")
    
    def open_file(self):
        """Open file dialog to select an image file."""
        file_types = [
            ("Image files", "*.jpg *.jpeg *.png *.tiff *.tif *.bmp *.gif *.webp"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("TIFF files", "*.tiff *.tif"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=file_types
        )
        
        if file_path:
            self.load_file(file_path)
    
    def load_file(self, file_path):
        """Load an image file and update the UI."""
        try:
            # Check if the file is valid
            if not is_valid_image(file_path):
                messagebox.showerror("Invalid File", 
                                    "The selected file is not a valid image file.")
                return
            
            # Update current file
            self.current_file = file_path
            
            # Update status
            self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}")
            
            # Load and display the image preview
            self._display_image_preview(file_path)
            
            # Enable extract button
            self.extract_button.config(state=tk.NORMAL)
            
            # Clear previous results
            self.clear_results()
            
            logger.info(f"Loaded file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def _display_image_preview(self, file_path):
        """Display image preview in the canvas."""
        try:
            # Open the image
            image = Image.open(file_path)
            
            # Get image info
            width, height = image.size
            format_info = image.format
            mode_info = image.mode
            
            # Update info label
            self.preview_info.config(
                text=f"Size: {width}x{height} | Format: {format_info} | Mode: {mode_info}"
            )
            
            # Resize for preview (maintain aspect ratio)
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            # Use a minimum size if the canvas hasn't been drawn yet
            if canvas_width <= 1:
                canvas_width = 300
            if canvas_height <= 1:
                canvas_height = 300
            
            # Calculate scaling factor
            scale_w = canvas_width / width
            scale_h = canvas_height / height
            scale = min(scale_w, scale_h)
            
            # Resize image for preview
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Resize using high-quality resampling
            resized_image = image.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(resized_image)
            
            # Clear previous image and display new one
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                canvas_width // 2, canvas_height // 2, 
                image=photo, anchor=tk.CENTER
            )
            
            # Keep a reference to prevent garbage collection
            self.preview_canvas.image = photo
            
        except Exception as e:
            logger.error(f"Error displaying image preview: {e}")
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                150, 150, text="Preview not available", fill="gray"
            )
            self.preview_info.config(text="Error loading preview")
    
    def extract_metadata(self):
        """Extract metadata from the current image file."""
        if not self.current_file:
            messagebox.showinfo("No File Selected", 
                               "Please select an image file first.")
            return
        
        if self.processing:
            return
        
        # Start processing
        self.processing = True
        self._unsaved_changes = True
        self.progress_bar.start(10)
        self.status_label.config(text="Extracting metadata...")
        self.extract_button.config(state=tk.DISABLED)
        
        # Run extraction in a separate thread to keep UI responsive
        threading.Thread(target=self._extract_metadata_thread, daemon=True).start()
    
    def _extract_metadata_thread(self):
        """Background thread for metadata extraction."""
        try:
            # Extract metadata
            metadata = self.metadata_extractor.extract(self.current_file)
            
            # Store the results
            self.current_metadata = metadata
            
            # Update UI in the main thread
            self.root.after(0, self._update_results_ui, metadata)
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            logger.error(traceback.format_exc())
            
            # Update UI in the main thread
            self.root.after(0, self._show_extraction_error, str(e))
        
        finally:
            # Update UI state in the main thread
            self.root.after(0, self._finish_extraction)
    
    def _update_results_ui(self, metadata):
        """Update the UI with extraction results."""
        # Display the results
        self.result_view.display_metadata(metadata)
        
        # Enable save button
        self.save_button.config(state=tk.NORMAL)
    
    def _show_extraction_error(self, error_message):
        """Show error message for failed extraction."""
        messagebox.showerror("Extraction Error", 
                            f"Failed to extract metadata: {error_message}")
    
    def _finish_extraction(self):
        """Update UI state after extraction completes."""
        self.processing = False
        self.progress_bar.stop()
        self.status_label.config(text="Extraction complete")
        self.extract_button.config(state=tk.NORMAL)
    
    def save_results(self):
        """Save the extracted metadata to a file."""
        if not self.current_metadata:
            messagebox.showinfo("No Data", "No metadata to save.")
            return False
        
        # Ask for file type and location
        file_types = [
            ("CSV files", "*.csv"),
            ("JSON files", "*.json"),
            ("Text files", "*.txt"),
            ("PDF Report", "*.pdf"),
            ("Excel files", "*.xlsx")
        ]
        
        default_name = os.path.splitext(os.path.basename(self.current_file))[0] + "_metadata"
        
        save_path = filedialog.asksaveasfilename(
            title="Save Metadata",
            filetypes=file_types,
            defaultextension=".csv",
            initialfile=default_name
        )
        
        if not save_path:
            return False  # User cancelled
        
        try:
            # Determine format from extension
            ext = os.path.splitext(save_path)[1].lower()
            
            # Save based on format
            if ext == '.csv':
                self.file_handler.save_csv(self.current_metadata, save_path)
            elif ext == '.json':
                self.file_handler.save_json(self.current_metadata, save_path)
            elif ext == '.txt':
                self.file_handler.save_text(self.current_metadata, save_path)
            elif ext == '.pdf':
                self.file_handler.save_pdf(self.current_metadata, save_path, 
                                          image_path=self.current_file)
            elif ext == '.xlsx':
                self.file_handler.save_excel(self.current_metadata, save_path)
            else:
                # Default to CSV if extension is not recognized
                self.file_handler.save_csv(self.current_metadata, save_path)
            
            # Update status
            self.status_label.config(text=f"Saved to: {os.path.basename(save_path)}")
            self._unsaved_changes = False
            
            logger.info(f"Saved results to: {save_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            messagebox.showerror("Save Error", f"Failed to save results: {str(e)}")
            return False
    
    def clear_results(self):
        """Clear the current results."""
        self.result_view.clear()
        self.current_metadata = None
        self.save_button.config(state=tk.DISABLED)
        self._unsaved_changes = False
        self.status_label.config(text="Ready")
    
    def batch_process(self):
        """Process multiple image files in batch."""
        file_types = [
            ("Image files", "*.jpg *.jpeg *.png *.tiff *.tif *.bmp *.gif *.webp"),
            ("All files", "*.*")
        ]
        
        file_paths = filedialog.askopenfilenames(
            title="Select Image Files for Batch Processing",
            filetypes=file_types
        )
        
        if not file_paths:
            return  # User cancelled
        
        # Ask for output directory
        output_dir = filedialog.askdirectory(
            title="Select Output Directory for Batch Results"
        )
        
        if not output_dir:
            return  # User cancelled
        
        # Ask for output format
        formats = [
            ("CSV", ".csv"),
            ("JSON", ".json"),
            ("Text", ".txt"),
            ("PDF", ".pdf"),
            ("Excel", ".xlsx")
        ]
        
        BatchFormatDialog(self.root, formats, self._start_batch_process, 
                         file_paths, output_dir)
    
    def _start_batch_process(self, file_paths, output_dir, format_ext):
        """Start the batch processing with the selected format."""
        if self.processing:
            return
        
        # Start processing
        self.processing = True
        self.progress_bar.start(10)
        self.status_label.config(text=f"Batch processing {len(file_paths)} files...")
        
        # Disable buttons during processing
        self.extract_button.config(state=tk.DISABLED)
        self.batch_button.config(state=tk.DISABLED)
        self.open_button.config(state=tk.DISABLED)
        
        # Run batch processing in a separate thread
        threading.Thread(
            target=self._batch_process_thread,
            args=(file_paths, output_dir, format_ext),
            daemon=True
        ).start()
    
    def _batch_process_thread(self, file_paths, output_dir, format_ext):
        """Background thread for batch processing."""
        results = []
        errors = []
        
        try:
            total_files = len(file_paths)
            
            for i, file_path in enumerate(file_paths):
                try:
                    # Update status in the main thread
                    self.root.after(0, self.status_label.config, 
                                   {"text": f"Processing file {i+1}/{total_files}..."})
                    
                    # Check if file is valid
                    if not is_valid_image(file_path):
                        errors.append((file_path, "Not a valid image file"))
                        continue
                    
                    # Extract metadata
                    metadata = self.metadata_extractor.extract(file_path)
                    
                    # Create output filename
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    output_file = os.path.join(output_dir, f"{base_name}_metadata{format_ext}")
                    
                    # Save based on format
                    if format_ext == '.csv':
                        self.file_handler.save_csv(metadata, output_file)
                    elif format_ext == '.json':
                        self.file_handler.save_json(metadata, output_file)
                    elif format_ext == '.txt':
                        self.file_handler.save_text(metadata, output_file)
                    elif format_ext == '.pdf':
                        self.file_handler.save_pdf(metadata, output_file, image_path=file_path)
                    elif format_ext == '.xlsx':
                        self.file_handler.save_excel(metadata, output_file)
                    
                    # Add to successful results
                    results.append(file_path)
                    
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    errors.append((file_path, str(e)))
            
            # Show batch results in the main thread
            self.root.after(0, self._show_batch_results, results, errors)
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            logger.error(traceback.format_exc())
            
            # Show error in the main thread
            self.root.after(0, messagebox.showerror, "Batch Processing Error", 
                           f"An error occurred during batch processing: {str(e)}")
        
        finally:
            # Update UI state in the main thread
            self.root.after(0, self._finish_batch_processing)
    
    def _show_batch_results(self, results, errors):
        """Show the results of batch processing."""
        if errors:
            error_message = "\n".join([f"{os.path.basename(path)}: {error}" 
                                      for path, error in errors[:10]])
            if len(errors) > 10:
                error_message += f"\n... and {len(errors) - 10} more errors"
            
            messagebox.showwarning(
                "Batch Processing Completed with Errors",
                f"Processed {len(results)} files successfully.\n"
                f"Encountered {len(errors)} errors:\n\n{error_message}"
            )
        else:
            messagebox.showinfo(
                "Batch Processing Completed",
                f"Successfully processed all {len(results)} files."
            )
    
    def _finish_batch_processing(self):
        """Update UI state after batch processing completes."""
        self.processing = False
        self.progress_bar.stop()
        self.status_label.config(text="Batch processing complete")
        
        # Re-enable buttons
        self.extract_button.config(state=tk.NORMAL)
        self.batch_button.config(state=tk.NORMAL)
        self.open_button.config(state=tk.NORMAL)
    
    def show_welcome_message(self):
        """Show welcome message when the application starts."""
        self.status_label.config(text="Welcome to Image Metadata Extractor")
        
        # Create a welcome message on the canvas
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(
            150, 120, 
            text="Welcome to\nImage Metadata Extractor", 
            font=("Helvetica", 14, "bold"),
            fill="#3498db",
            justify=tk.CENTER
        )
        self.preview_canvas.create_text(
            150, 180, 
            text="Open an image file to begin\nor drag and drop an image here", 
            fill="#7f8c8d",
            justify=tk.CENTER
        )
    
    def has_unsaved_changes(self):
        """Check if there are unsaved changes."""
        return self._unsaved_changes and self.current_metadata is not None
    
    def exit_application(self):
        """Exit the application."""
        if self.has_unsaved_changes():
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Would you like to save before exiting?"
            )
            
            if response is None:  # Cancel was clicked
                return
            elif response:  # Yes was clicked
                if not self.save_results():
                    return  # Don't exit if save was cancelled or failed
        
        self.root.quit()


class BatchFormatDialog:
    """Dialog for selecting batch processing format."""
    
    def __init__(self, parent, formats, callback, file_paths, output_dir):
        """
        Initialize the batch format dialog.
        
        Args:
            parent: Parent window
            formats: List of format tuples (name, extension)
            callback: Function to call with selected format
            file_paths: List of file paths to process
            output_dir: Output directory for results
        """
        self.parent = parent
        self.formats = formats
        self.callback = callback
        self.file_paths = file_paths
        self.output_dir = output_dir
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Output Format")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make dialog modal
        self.dialog.focus_set()
        
        # Center dialog on parent
        x = parent.winfo_x() + parent.winfo_width() // 2 - 150
        y = parent.winfo_y() + parent.winfo_height() // 2 - 100
        self.dialog.geometry(f"300x200+{x}+{y}")
        
        # Create widgets
        ttk.Label(self.dialog, text="Select output format for batch processing:",
                 padding=10).pack(fill=tk.X)
        
        # Format selection
        self.format_var = tk.StringVar(value=formats[0][1])  # Default to first format
        
        format_frame = ttk.Frame(self.dialog, padding=10)
        format_frame.pack(fill=tk.BOTH, expand=True)
        
        for name, ext in formats:
            ttk.Radiobutton(format_frame, text=name, value=ext,
                           variable=self.format_var).pack(anchor=tk.W, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, padding=10)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Process", 
                  command=self._on_process).pack(side=tk.RIGHT, padx=5)
    
    def _on_process(self):
        """Handle process button click."""
        selected_format = self.format_var.get()
        self.dialog.destroy()
        
        # Call the callback with the selected format
        self.callback(self.file_paths, self.output_dir, selected_format)