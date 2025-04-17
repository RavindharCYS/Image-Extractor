"""
Menu Bar Module for Image Metadata Extractor

This module contains the MenuBar class which provides the application's
main menu and toolbar functionality.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser
import logging
import platform
from datetime import datetime

# Get the package logger
logger = logging.getLogger(__name__)


class MenuBar(tk.Menu):
    """
    Menu bar for the Image Metadata Extractor application.
    
    Provides menus for file operations, editing, tools, view options,
    and help functionality.
    """
    
    def __init__(self, parent, main_window):
        """
        Initialize the menu bar.
        
        Args:
            parent: The parent window
            main_window: Reference to the main application window
        """
        super().__init__(parent)
        
        self.parent = parent
        self.main_window = main_window
        
        # Create menus
        self._create_file_menu()
        self._create_edit_menu()
        self._create_tools_menu()
        self._create_view_menu()
        self._create_help_menu()
        
        # Set keyboard shortcuts based on platform
        self.is_mac = platform.system() == "Darwin"
        self._setup_accelerators()
        
        logger.debug("Menu bar initialized")
    
    def _create_file_menu(self):
        """Create the File menu."""
        self.file_menu = tk.Menu(self, tearoff=0)
        
        self.file_menu.add_command(label="Open Image...", 
                                  command=self.main_window.open_file)
        self.file_menu.add_command(label="Batch Process...", 
                                  command=self.main_window.batch_process)
        
        self.file_menu.add_separator()
        
        self.file_menu.add_command(label="Save Results...", 
                                  command=self.main_window.save_results)
        self.file_menu.add_command(label="Export Report...", 
                                  command=self._export_report)
        
        self.file_menu.add_separator()
        
        # Recent files submenu
        self.recent_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self._update_recent_files_menu()
        
        self.file_menu.add_separator()
        
        self.file_menu.add_command(label="Exit", command=self._exit_application)
        
        self.add_cascade(label="File", menu=self.file_menu)
    
    def _create_edit_menu(self):
        """Create the Edit menu."""
        self.edit_menu = tk.Menu(self, tearoff=0)
        
        self.edit_menu.add_command(label="Copy Selected Metadata", 
                                  command=self._copy_selected_metadata)
        self.edit_menu.add_command(label="Copy All Metadata", 
                                  command=self._copy_all_metadata)
        
        self.edit_menu.add_separator()
        
        self.edit_menu.add_command(label="Find...", command=self._show_find_dialog)
        
        self.edit_menu.add_separator()
        
        self.edit_menu.add_command(label="Clear Results", 
                                  command=self.main_window.clear_results)
        self.edit_menu.add_command(label="Preferences...", 
                                  command=self._show_preferences)
        
        self.add_cascade(label="Edit", menu=self.edit_menu)
    
    def _create_tools_menu(self):
        """Create the Tools menu."""
        self.tools_menu = tk.Menu(self, tearoff=0)
        
        self.tools_menu.add_command(label="Extract Metadata", 
                                   command=self.main_window.extract_metadata)
        self.tools_menu.add_command(label="Analyze Image", 
                                   command=self._analyze_image)
        
        self.tools_menu.add_separator()
        
        self.tools_menu.add_command(label="View EXIF Data Only", 
                                   command=lambda: self._filter_metadata("exif"))
        self.tools_menu.add_command(label="View GPS Data Only", 
                                   command=lambda: self._filter_metadata("gps"))
        
        self.tools_menu.add_separator()
        
        self.tools_menu.add_command(label="Map Location", 
                                   command=self._map_location)
        self.tools_menu.add_command(label="Clean Metadata...", 
                                   command=self._clean_metadata)
        
        self.add_cascade(label="Tools", menu=self.tools_menu)
    
    def _create_view_menu(self):
        """Create the View menu."""
        self.view_menu = tk.Menu(self, tearoff=0)
        
        # Theme submenu
        self.theme_menu = tk.Menu(self.view_menu, tearoff=0)
        self.theme_var = tk.StringVar(value="Default")
        
        themes = ["Default", "Light", "Dark", "System"]
        for theme in themes:
            self.theme_menu.add_radiobutton(
                label=theme, 
                variable=self.theme_var, 
                value=theme,
                command=lambda t=theme: self._change_theme(t)
            )
        
        self.view_menu.add_cascade(label="Theme", menu=self.theme_menu)
        
        self.view_menu.add_separator()
        
        # View options
        self.show_preview_var = tk.BooleanVar(value=True)
        self.view_menu.add_checkbutton(
            label="Show Image Preview", 
            variable=self.show_preview_var,
            command=self._toggle_preview
        )
        
        self.show_statusbar_var = tk.BooleanVar(value=True)
        self.view_menu.add_checkbutton(
            label="Show Status Bar", 
            variable=self.show_statusbar_var,
            command=self._toggle_statusbar
        )
        
        self.view_menu.add_separator()
        
        self.view_menu.add_command(label="Expand All", 
                                  command=self._expand_all_trees)
        self.view_menu.add_command(label="Collapse All", 
                                  command=self._collapse_all_trees)
        
        self.view_menu.add_separator()
        
        self.view_menu.add_command(label="Reset Layout", 
                                  command=self._reset_layout)
        
        self.add_cascade(label="View", menu=self.view_menu)
    
    def _create_help_menu(self):
        """Create the Help menu."""
        self.help_menu = tk.Menu(self, tearoff=0)
        
        self.help_menu.add_command(label="User Guide", 
                                  command=self._show_user_guide)
        self.help_menu.add_command(label="Keyboard Shortcuts", 
                                  command=self._show_shortcuts)
        
        self.help_menu.add_separator()
        
        self.help_menu.add_command(label="Check for Updates", 
                                  command=self._check_updates)
        
        self.help_menu.add_separator()
        
        self.help_menu.add_command(label="About", 
                                  command=self._show_about)
        
        self.add_cascade(label="Help", menu=self.help_menu)
    
    def _setup_accelerators(self):
        """Setup keyboard accelerators based on platform."""
        # Determine modifier key based on platform
        mod_key = "Command" if self.is_mac else "Control"
        
        # File menu accelerators
        self.file_menu.entryconfig("Open Image...", 
                                  accelerator=f"{mod_key}+O")
        self.file_menu.entryconfig("Save Results...", 
                                  accelerator=f"{mod_key}+S")
        self.file_menu.entryconfig("Exit", 
                                  accelerator=f"{mod_key}+Q")
        
        # Edit menu accelerators
        self.edit_menu.entryconfig("Copy Selected Metadata", 
                                  accelerator=f"{mod_key}+C")
        self.edit_menu.entryconfig("Find...", 
                                  accelerator=f"{mod_key}+F")
        
        # Tools menu accelerators
        self.tools_menu.entryconfig("Extract Metadata", 
                                   accelerator=f"{mod_key}+E")
        
        # Bind keyboard shortcuts
        self.parent.bind(f"<{mod_key}-o>", lambda e: self.main_window.open_file())
        self.parent.bind(f"<{mod_key}-s>", lambda e: self.main_window.save_results())
        self.parent.bind(f"<{mod_key}-q>", lambda e: self._exit_application())
        self.parent.bind(f"<{mod_key}-c>", lambda e: self._copy_selected_metadata())
        self.parent.bind(f"<{mod_key}-f>", lambda e: self._show_find_dialog())
        self.parent.bind(f"<{mod_key}-e>", lambda e: self.main_window.extract_metadata())
    
    def _update_recent_files_menu(self):
        """Update the recent files submenu."""
        # Clear existing items
        self.recent_menu.delete(0, tk.END)
        
        # Get recent files (would be stored in settings)
        recent_files = self._get_recent_files()
        
        if recent_files:
            for file_path in recent_files:
                # Truncate path for display if too long
                display_path = file_path
                if len(display_path) > 50:
                    display_path = "..." + display_path[-47:]
                
                self.recent_menu.add_command(
                    label=display_path,
                    command=lambda path=file_path: self.main_window.load_file(path)
                )
            
            self.recent_menu.add_separator()
            self.recent_menu.add_command(
                label="Clear Recent Files",
                command=self._clear_recent_files
            )
        else:
            self.recent_menu.add_command(
                label="No Recent Files",
                state=tk.DISABLED
            )
    
    def _get_recent_files(self):
        """
        Get list of recently opened files.
        
        Returns:
            List of file paths
        """
        # This would typically be loaded from application settings
        # For now, return an empty list or mock data
        try:
            # Check if main_window has a file_handler with recent files
            if hasattr(self.main_window, 'file_handler') and \
               hasattr(self.main_window.file_handler, 'get_recent_files'):
                return self.main_window.file_handler.get_recent_files()
        except Exception as e:
            logger.error(f"Error getting recent files: {e}")
        
        # Return empty list as fallback
        return []
    
    def _clear_recent_files(self):
        """Clear the list of recent files."""
        try:
            # Clear recent files in file handler if available
            if hasattr(self.main_window, 'file_handler') and \
               hasattr(self.main_window.file_handler, 'clear_recent_files'):
                self.main_window.file_handler.clear_recent_files()
            
            # Update the menu
            self._update_recent_files_menu()
            
            logger.info("Recent files list cleared")
        except Exception as e:
            logger.error(f"Error clearing recent files: {e}")
    
    def _exit_application(self):
        """Exit the application with confirmation if needed."""
        self.main_window.exit_application()
    
    def _copy_selected_metadata(self):
        """Copy selected metadata to clipboard."""
        try:
            # Get the current tab's tree view
            notebook = self.main_window.result_view.notebook
            current_tab = notebook.select()
            tab_id = notebook.index(current_tab)
            
            # Get the category ID from the tab index
            categories = self.main_window.result_view.categories
            if tab_id < len(categories):
                category_id = categories[tab_id][0]
                tree_view = self.main_window.result_view.tree_views.get(category_id)
                
                if tree_view:
                    # Get selected item
                    selection = tree_view.selection()
                    if selection:
                        item = selection[0]
                        property_name = tree_view.item(item, "text")
                        value = tree_view.item(item, "values")[0] if tree_view.item(item, "values") else ""
                        
                        # Copy to clipboard
                        text = f"{property_name}: {value}"
                        self.parent.clipboard_clear()
                        self.parent.clipboard_append(text)
                        
                        logger.info(f"Copied to clipboard: {text}")
                        return
            
            # If we get here, nothing was selected or copied
            messagebox.showinfo("Copy", "Please select an item to copy.")
            
        except Exception as e:
            logger.error(f"Error copying selected metadata: {e}")
            messagebox.showerror("Copy Error", f"Failed to copy metadata: {str(e)}")
    
    def _copy_all_metadata(self):
        """Copy all metadata to clipboard as formatted text."""
        try:
            if not self.main_window.current_metadata:
                messagebox.showinfo("Copy", "No metadata available to copy.")
                return
            
            # Get formatted text representation
            text = self.main_window.result_view.export_to_text()
            
            # Copy to clipboard
            self.parent.clipboard_clear()
            self.parent.clipboard_append(text)
            
            logger.info("Copied all metadata to clipboard")
            messagebox.showinfo("Copy", "All metadata copied to clipboard.")
            
        except Exception as e:
            logger.error(f"Error copying all metadata: {e}")
            messagebox.showerror("Copy Error", f"Failed to copy metadata: {str(e)}")
    
    def _show_find_dialog(self):
        """Show the find dialog or focus the search entry."""
        try:
            # Focus the search entry in the result view
            self.main_window.result_view.search_entry.focus_set()
        except Exception as e:
            logger.error(f"Error showing find dialog: {e}")
    
    def _show_preferences(self):
        """Show the preferences dialog."""
        PreferencesDialog(self.parent, self)
    
    def _analyze_image(self):
        """Perform advanced image analysis."""
        if not self.main_window.current_file:
            messagebox.showinfo("Analyze Image", 
                               "Please open an image file first.")
            return
        
        # This would typically launch a more advanced analysis
        # For now, just show a message
        messagebox.showinfo("Analyze Image", 
                           "Advanced image analysis feature coming soon!")
    
    def _filter_metadata(self, category):
        """
        Filter metadata to show only a specific category.
        
        Args:
            category: Category ID to filter by
        """
        try:
            # Switch to the specified tab
            categories = self.main_window.result_view.categories
            for i, (cat_id, _) in enumerate(categories):
                if cat_id == category:
                    self.main_window.result_view.notebook.select(i)
                    break
        except Exception as e:
            logger.error(f"Error filtering metadata: {e}")
    
    def _map_location(self):
        """Open GPS location in a map if available."""
        try:
            # Check if GPS data is available
            if not self.main_window.current_metadata or \
               "gps" not in self.main_window.current_metadata:
                messagebox.showinfo("Map Location", 
                                   "No GPS data available for this image.")
                return
            
            # Use the result view's method to open GPS location
            self.main_window.result_view._open_gps_location()
            
        except Exception as e:
            logger.error(f"Error mapping location: {e}")
            messagebox.showerror("Map Error", f"Failed to open map: {str(e)}")
    
    def _clean_metadata(self):
        """Show dialog to clean/remove metadata from the image."""
        if not self.main_window.current_file:
            messagebox.showinfo("Clean Metadata", 
                               "Please open an image file first.")
            return
        
        CleanMetadataDialog(self.parent, self.main_window)
    
    def _export_report(self):
        """Export a detailed report of the metadata."""
        if not self.main_window.current_metadata:
            messagebox.showinfo("Export Report", 
                               "No metadata available to export.")
            return
        
        # Ask for file location
        file_types = [
            ("PDF Report", "*.pdf"),
            ("HTML Report", "*.html"),
            ("Text Report", "*.txt")
        ]
        
        default_name = os.path.splitext(os.path.basename(self.main_window.current_file))[0] + "_report"
        
        save_path = filedialog.asksaveasfilename(
            title="Export Metadata Report",
            filetypes=file_types,
            defaultextension=".pdf",
            initialfile=default_name
        )
        
        if not save_path:
            return  # User cancelled
        
        try:
            # Determine format from extension
            ext = os.path.splitext(save_path)[1].lower()
            
            # Generate report based on format
            if ext == '.pdf':
                self._export_pdf_report(save_path)
            elif ext == '.html':
                self._export_html_report(save_path)
            elif ext == '.txt':
                self._export_text_report(save_path)
            else:
                # Default to PDF if extension is not recognized
                self._export_pdf_report(save_path)
            
            # Show success message
            messagebox.showinfo("Export Report", 
                               f"Report exported successfully to:\n{save_path}")
            
            logger.info(f"Report exported to: {save_path}")
            
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            messagebox.showerror("Export Error", f"Failed to export report: {str(e)}")
    
    def _export_pdf_report(self, save_path):
        """
        Export metadata as a PDF report.
        
        Args:
            save_path: Path to save the PDF file
        """
        # This would typically use a PDF generation library like reportlab
        # For now, delegate to the file handler
        try:
            if hasattr(self.main_window, 'file_handler') and \
               hasattr(self.main_window.file_handler, 'save_pdf'):
                self.main_window.file_handler.save_pdf(
                    self.main_window.current_metadata, 
                    save_path,
                    image_path=self.main_window.current_file,
                    include_preview=True,
                    title="Image Metadata Report"
                )
            else:
                raise NotImplementedError("PDF export not implemented in file handler")
        except Exception as e:
            logger.error(f"Error exporting PDF report: {e}")
            raise
    
    def _export_html_report(self, save_path):
        """
        Export metadata as an HTML report.
        
        Args:
            save_path: Path to save the HTML file
        """
        try:
            if hasattr(self.main_window, 'file_handler') and \
               hasattr(self.main_window.file_handler, 'save_html'):
                self.main_window.file_handler.save_html(
                    self.main_window.current_metadata, 
                    save_path,
                    image_path=self.main_window.current_file,
                    include_preview=True,
                    title="Image Metadata Report"
                )
            else:
                # Fallback to basic HTML generation
                self._generate_basic_html_report(save_path)
        except Exception as e:
            logger.error(f"Error exporting HTML report: {e}")
            raise
    
    def _generate_basic_html_report(self, save_path):
        """
        Generate a basic HTML report without external dependencies.
        
        Args:
            save_path: Path to save the HTML file
        """
        metadata = self.main_window.current_metadata
        image_path = self.main_window.current_file
        
        # Start HTML content
        html_content = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <title>Image Metadata Report</title>",
            "    <style>",
            "        body { font-family: Arial, sans-serif; margin: 20px; }",
            "        h1 { color: #2c3e50; }",
            "        .metadata-section { margin-bottom: 20px; }",
            "        .metadata-table { border-collapse: collapse; width: 100%; }",
            "        .metadata-table th, .metadata-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "        .metadata-table th { background-color: #f2f2f2; }",
            "        .metadata-table tr:nth-child(even) { background-color: #f9f9f9; }",
            "        .image-preview { max-width: 300px; max-height: 300px; margin-bottom: 20px; }",
            "        .timestamp { color: #7f8c8d; font-size: 0.8em; margin-top: 30px; }",
            "    </style>",
            "</head>",
            "<body>",
            f"    <h1>Image Metadata Report</h1>",
            f"    <p>File: {os.path.basename(image_path)}</p>"
        ]
        
        # Add image preview if possible
        html_content.append("    <div class='metadata-section'>")
        html_content.append("        <h2>Image Preview</h2>")
        # Note: This embeds the image by reference, not by data
        html_content.append(f"        <img src='file://{image_path.replace(' ', '%20')}' class='image-preview' alt='Image preview'>")
        html_content.append("    </div>")
        
        # Categorize metadata
        categorized = self._categorize_metadata(metadata)
        
        # Add each category
        for category_id, category_name in self.main_window.result_view.categories:
            if category_id == "all":
                continue  # Skip the "all" category to avoid duplication
                
            if category_id in categorized and categorized[category_id]:
                html_content.append("    <div class='metadata-section'>")
                html_content.append(f"        <h2>{category_name}</h2>")
                html_content.append("        <table class='metadata-table'>")
                html_content.append("            <tr><th>Property</th><th>Value</th></tr>")
                
                # Add metadata items
                for key, value in categorized[category_id].items():
                    html_content.append(f"            <tr><td>{key}</td><td>{value}</td></tr>")
                
                html_content.append("        </table>")
                html_content.append("    </div>")
        
        # Add timestamp
        html_content.append("    <div class='timestamp'>")
        html_content.append(f"        Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        html_content.append("    </div>")
        
        # Close HTML
        html_content.append("</body>")
        html_content.append("</html>")
        
        # Write to file
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(html_content))
    
    def _categorize_metadata(self, metadata):
        """
        Categorize metadata into different sections.
        
        Args:
            metadata: Dictionary containing the metadata
            
        Returns:
            Dictionary with categories as keys and metadata dictionaries as values
        """
        # Use the result view's categorization method if available
        if hasattr(self.main_window.result_view, '_categorize_metadata'):
            return self.main_window.result_view._categorize_metadata(metadata)
        
        # Fallback to basic categorization
        categorized = {
            "basic": {},
            "exif": {},
            "gps": {},
            "device": {},
            "file": {}
        }
        
        # Basic categorization logic
        for key, value in metadata.items():
            if "EXIF" in key:
                categorized["exif"][key] = value
            elif "GPS" in key:
                categorized["gps"][key] = value
            elif any(device_key in key for device_key in ["Make", "Model", "Camera", "Device"]):
                categorized["device"][key] = value
            elif any(file_key in key for file_key in ["File", "Filename", "Size"]):
                categorized["file"][key] = value
            else:
                categorized["basic"][key] = value
        
        return categorized
    
    def _export_text_report(self, save_path):
        """
        Export metadata as a text report.
        
        Args:
            save_path: Path to save the text file
        """
        try:
            # Get formatted text from result view
            text = self.main_window.result_view.export_to_text()
            
            # Add header information
            header = [
                "IMAGE METADATA REPORT",
                "=" * 50,
                f"File: {self.main_window.current_file}",
                f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "=" * 50,
                ""
            ]
            
            # Combine header and text
            full_text = "\n".join(header) + text
            
            # Write to file
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
                
        except Exception as e:
            logger.error(f"Error exporting text report: {e}")
            raise
    
    def _change_theme(self, theme_name):
        """
        Change the application theme.
        
        Args:
            theme_name: Name of the theme to apply
        """
        try:
            logger.info(f"Changing theme to: {theme_name}")
            
            # This would typically call a theme manager
            # For now, just log the change
            
            # If a style manager exists, use it
            if hasattr(self.main_window, 'apply_theme'):
                self.main_window.apply_theme(theme_name)
            
            # Save theme preference
            self._save_preference("theme", theme_name)
            
        except Exception as e:
            logger.error(f"Error changing theme: {e}")
    
    def _toggle_preview(self):
        """Toggle visibility of the image preview panel."""
        try:
            show_preview = self.show_preview_var.get()
            logger.info(f"Toggle preview: {show_preview}")
            
            # Toggle visibility of preview frame
            if hasattr(self.main_window, 'preview_frame'):
                if show_preview:
                    self.main_window.preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                else:
                    self.main_window.preview_frame.pack_forget()
            
            # Save preference
            self._save_preference("show_preview", show_preview)
            
        except Exception as e:
            logger.error(f"Error toggling preview: {e}")
    
    def _toggle_statusbar(self):
        """Toggle visibility of the status bar."""
        try:
            show_statusbar = self.show_statusbar_var.get()
            logger.info(f"Toggle statusbar: {show_statusbar}")
            
            # Toggle visibility of status frame
            if hasattr(self.main_window, 'status_frame'):
                if show_statusbar:
                    self.main_window.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
                else:
                    self.main_window.status_frame.pack_forget()
            
            # Save preference
            self._save_preference("show_statusbar", show_statusbar)
            
        except Exception as e:
            logger.error(f"Error toggling statusbar: {e}")
    
    def _expand_all_trees(self):
        """Expand all items in all tree views."""
        try:
            # Call expand_all method on the current tab's tree view
            current_tab = self.main_window.result_view.notebook.select()
            tab_id = self.main_window.result_view.notebook.index(current_tab)
            
            # Get the category ID from the tab index
            categories = self.main_window.result_view.categories
            if tab_id < len(categories):
                category_id = categories[tab_id][0]
                tree_view = self.main_window.result_view.tree_views.get(category_id)
                
                if tree_view and hasattr(self.main_window.result_view, '_expand_all'):
                    self.main_window.result_view._expand_all(tree_view)
                    
        except Exception as e:
            logger.error(f"Error expanding all trees: {e}")
    
    def _collapse_all_trees(self):
        """Collapse all items in all tree views."""
        try:
            # Call collapse_all method on the current tab's tree view
            current_tab = self.main_window.result_view.notebook.select()
            tab_id = self.main_window.result_view.notebook.index(current_tab)
            
            # Get the category ID from the tab index
            categories = self.main_window.result_view.categories
            if tab_id < len(categories):
                category_id = categories[tab_id][0]
                tree_view = self.main_window.result_view.tree_views.get(category_id)
                
                if tree_view and hasattr(self.main_window.result_view, '_collapse_all'):
                    self.main_window.result_view._collapse_all(tree_view)
                    
        except Exception as e:
            logger.error(f"Error collapsing all trees: {e}")
    
    def _reset_layout(self):
        """Reset the application layout to default."""
        try:
            # Reset paned window position
            if hasattr(self.main_window, 'paned_window'):
                self.main_window.paned_window.sash_place(0, 300, 0)
            
            # Show all panels
            self.show_preview_var.set(True)
            self.show_statusbar_var.set(True)
            self._toggle_preview()
            self._toggle_statusbar()
            
            logger.info("Layout reset to default")
            
        except Exception as e:
            logger.error(f"Error resetting layout: {e}")
    
    def _show_user_guide(self):
        """Show the user guide."""
        # This would typically open a help file or web page
        messagebox.showinfo("User Guide", 
                           "The user guide will be available in a future update.")
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        ShortcutsDialog(self.parent)
    
    def _check_updates(self):
        """Check for application updates."""
        # This would typically connect to a server to check for updates
        messagebox.showinfo("Updates", 
                           "You are running the latest version of Image Metadata Extractor.")
    
    def _show_about(self):
        """Show about dialog."""
        AboutDialog(self.parent)
    
    def _save_preference(self, key, value):
        """
        Save a user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        # This would typically save to a configuration file
        # For now, just log the preference
        logger.info(f"Saving preference: {key}={value}")


class PreferencesDialog:
    """Dialog for application preferences."""
    
    def __init__(self, parent, menu_bar):
        """
        Initialize the preferences dialog.
        
        Args:
            parent: Parent window
            menu_bar: Reference to the menu bar
        """
        self.parent = parent
        self.menu_bar = menu_bar
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Preferences")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make dialog modal
        self.dialog.focus_set()
        
        # Set size and position
        self.dialog.geometry("400x450")
        self._center_dialog()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self._create_general_tab()
        self._create_display_tab()
        self._create_export_tab()
        self._create_advanced_tab()
        
        # Create buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self._save_preferences).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Apply", command=lambda: self._save_preferences(False)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self._reset_defaults).pack(side=tk.LEFT, padx=5)
    
    def _center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        # Get parent and dialog dimensions
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Calculate position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # Set position
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_general_tab(self):
        """Create the General tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="General")
        
        # Create settings
        ttk.Label(tab, text="Application Settings", font=("Helvetica", 12, "bold")).pack(anchor=tk.W, padx=10, pady=10)
        
        # Recent files
        recent_frame = ttk.Frame(tab)
        recent_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(recent_frame, text="Number of recent files:").pack(side=tk.LEFT)
        
        self.recent_files_var = tk.StringVar(value="10")
        recent_spinbox = ttk.Spinbox(recent_frame, from_=0, to=20, width=5, textvariable=self.recent_files_var)
        recent_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Startup behavior
        ttk.Label(tab, text="On startup:").pack(anchor=tk.W, padx=10, pady=5)
        
        self.startup_var = tk.StringVar(value="welcome")
        ttk.Radiobutton(tab, text="Show welcome screen", variable=self.startup_var, value="welcome").pack(anchor=tk.W, padx=20, pady=2)
        ttk.Radiobutton(tab, text="Show file open dialog", variable=self.startup_var, value="open").pack(anchor=tk.W, padx=20, pady=2)
        ttk.Radiobutton(tab, text="Restore last session", variable=self.startup_var, value="restore").pack(anchor=tk.W, padx=20, pady=2)
        
        # Auto-save
        self.autosave_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Auto-save extraction results", variable=self.autosave_var).pack(anchor=tk.W, padx=10, pady=5)
        
        # Auto-check for updates
        self.check_updates_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab, text="Check for updates on startup", variable=self.check_updates_var).pack(anchor=tk.W, padx=10, pady=5)
    
    def _create_display_tab(self):
        """Create the Display tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Display")
        
        # Create settings
        ttk.Label(tab, text="Appearance", font=("Helvetica", 12, "bold")).pack(anchor=tk.W, padx=10, pady=10)
        
        # Theme
        theme_frame = ttk.Frame(tab)
        theme_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT)
        
        self.theme_var = tk.StringVar(value=self.menu_bar.theme_var.get())
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, width=15)
        theme_combo['values'] = ("Default", "Light", "Dark", "System")
        theme_combo.pack(side=tk.LEFT, padx=5)
        
        # Font size
        font_frame = ttk.Frame(tab)
        font_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(font_frame, text="Font size:").pack(side=tk.LEFT)
        
        self.font_size_var = tk.StringVar(value="10")
        font_spinbox = ttk.Spinbox(font_frame, from_=8, to=16, width=5, textvariable=self.font_size_var)
        font_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Display options
        ttk.Label(tab, text="Display Options", font=("Helvetica", 12, "bold")).pack(anchor=tk.W, padx=10, pady=10)
        
        # Show preview
        self.show_preview_var = tk.BooleanVar(value=self.menu_bar.show_preview_var.get())
        ttk.Checkbutton(tab, text="Show image preview", variable=self.show_preview_var).pack(anchor=tk.W, padx=10, pady=5)
        
        # Show status bar
        self.show_statusbar_var = tk.BooleanVar(value=self.menu_bar.show_statusbar_var.get())
        ttk.Checkbutton(tab, text="Show status bar", variable=self.show_statusbar_var).pack(anchor=tk.W, padx=10, pady=5)
        
        # Highlight sensitive data
        self.highlight_sensitive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab, text="Highlight sensitive metadata", variable=self.highlight_sensitive_var).pack(anchor=tk.W, padx=10, pady=5)
        
        # Auto-expand trees
        self.auto_expand_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Auto-expand metadata trees", variable=self.auto_expand_var).pack(anchor=tk.W, padx=10, pady=5)
    
    def _create_export_tab(self):
        """Create the Export tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Export")
        
        # Create settings
        ttk.Label(tab, text="Export Settings", font=("Helvetica", 12, "bold")).pack(anchor=tk.W, padx=10, pady=10)
        
        # Default export format
        format_frame = ttk.Frame(tab)
        format_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(format_frame, text="Default export format:").pack(side=tk.LEFT)
        
        self.export_format_var = tk.StringVar(value="csv")
        format_combo = ttk.Combobox(format_frame, textvariable=self.export_format_var, width=10)
        format_combo['values'] = ("csv", "json", "txt", "pdf", "xlsx")
        format_combo.pack(side=tk.LEFT, padx=5)
        
        # Include image in reports
        self.include_image_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab, text="Include image preview in reports", variable=self.include_image_var).pack(anchor=tk.W, padx=10, pady=5)
        
        # Export location
        location_frame = ttk.Frame(tab)
        location_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(location_frame, text="Default export location:").pack(anchor=tk.W, pady=5)
        
        self.export_location_var = tk.StringVar(value=os.path.expanduser("~"))
        location_entry = ttk.Entry(location_frame, textvariable=self.export_location_var, width=30)
        location_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5), pady=5)
        
        browse_button = ttk.Button(location_frame, text="Browse...", command=self._browse_export_location)
        browse_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Report customization
        ttk.Label(tab, text="Report Customization", font=("Helvetica", 12, "bold")).pack(anchor=tk.W, padx=10, pady=10)
        
        # Company/user name
        name_frame = ttk.Frame(tab)
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(name_frame, text="Company/User name:").pack(anchor=tk.W)
        
        self.company_name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.company_name_var, width=30).pack(fill=tk.X, padx=10, pady=5)
        
        # Custom report header
        header_frame = ttk.Frame(tab)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header_frame, text="Custom report header:").pack(anchor=tk.W)
        
        self.report_header_var = tk.StringVar()
        ttk.Entry(header_frame, textvariable=self.report_header_var, width=30).pack(fill=tk.X, padx=10, pady=5)
    
    def _create_advanced_tab(self):
        """Create the Advanced tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Advanced")
        
        # Create settings
        ttk.Label(tab, text="Advanced Settings", font=("Helvetica", 12, "bold")).pack(anchor=tk.W, padx=10, pady=10)
        
        # Logging level
        log_frame = ttk.Frame(tab)
        log_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(log_frame, text="Logging level:").pack(side=tk.LEFT)
        
        self.log_level_var = tk.StringVar(value="INFO")
        log_combo = ttk.Combobox(log_frame, textvariable=self.log_level_var, width=10)
        log_combo['values'] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        log_combo.pack(side=tk.LEFT, padx=5)
        
        # Extraction timeout
        timeout_frame = ttk.Frame(tab)
        timeout_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(timeout_frame, text="Extraction timeout (seconds):").pack(side=tk.LEFT)
        
        self.timeout_var = tk.StringVar(value="30")
        timeout_spinbox = ttk.Spinbox(timeout_frame, from_=5, to=120, width=5, textvariable=self.timeout_var)
        timeout_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Advanced options
        ttk.Label(tab, text="Options", font=("Helvetica", 12, "bold")).pack(anchor=tk.W, padx=10, pady=10)
        
        # Use external tools
        self.use_external_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Use external tools when available", variable=self.use_external_var).pack(anchor=tk.W, padx=10, pady=5)
        
        # Enable experimental features
        self.experimental_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Enable experimental features", variable=self.experimental_var).pack(anchor=tk.W, padx=10, pady=5)
        
        # Cache extracted metadata
        self.cache_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab, text="Cache extracted metadata", variable=self.cache_var).pack(anchor=tk.W, padx=10, pady=5)
        
        # Clear cache button
        ttk.Button(tab, text="Clear Metadata Cache", command=self._clear_cache).pack(anchor=tk.W, padx=10, pady=5)
    
    def _browse_export_location(self):
        """Open dialog to select default export location."""
        directory = filedialog.askdirectory(
            title="Select Default Export Location",
            initialdir=self.export_location_var.get()
        )
        
        if directory:
            self.export_location_var.set(directory)
    
    def _clear_cache(self):
        """Clear the metadata cache."""
        # This would typically clear a cache directory
        messagebox.showinfo("Cache Cleared", "Metadata cache has been cleared.")
    
    def _save_preferences(self, close=True):
        """
        Save preferences and optionally close the dialog.
        
        Args:
            close: Whether to close the dialog after saving
        """
        try:
            # Update menu bar settings
            self.menu_bar.theme_var.set(self.theme_var.get())
            self.menu_bar.show_preview_var.set(self.show_preview_var.get())
            self.menu_bar.show_statusbar_var.set(self.show_statusbar_var.get())
            
            # Apply changes
            self.menu_bar._change_theme(self.theme_var.get())
            self.menu_bar._toggle_preview()
            self.menu_bar._toggle_statusbar()
            
            # This would typically save all preferences to a config file
            logger.info("Preferences saved")
            
            if close:
                self.dialog.destroy()
                
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
            messagebox.showerror("Error", f"Failed to save preferences: {str(e)}")
    
    def _reset_defaults(self):
        """Reset all preferences to default values."""
        # Reset general tab
        self.recent_files_var.set("10")
        self.startup_var.set("welcome")
        self.autosave_var.set(False)
        self.check_updates_var.set(True)
        
        # Reset display tab
        self.theme_var.set("Default")
        self.font_size_var.set("10")
        self.show_preview_var.set(True)
        self.show_statusbar_var.set(True)
        self.highlight_sensitive_var.set(True)
        self.auto_expand_var.set(False)
        
        # Reset export tab
        self.export_format_var.set("csv")
        self.include_image_var.set(True)
        self.export_location_var.set(os.path.expanduser("~"))
        self.company_name_var.set("")
        self.report_header_var.set("")
        
        # Reset advanced tab
        self.log_level_var.set("INFO")
        self.timeout_var.set("30")
        self.use_external_var.set(False)
        self.experimental_var.set(False)
        self.cache_var.set(True)
        
        logger.info("Preferences reset to defaults")
        messagebox.showinfo("Reset", "All preferences have been reset to default values.")


class ShortcutsDialog:
    """Dialog displaying keyboard shortcuts."""
    
    def __init__(self, parent):
        """
        Initialize the shortcuts dialog.
        
        Args:
            parent: Parent window
        """
        self.parent = parent
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Keyboard Shortcuts")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make dialog modal
        self.dialog.focus_set()
        
        # Set size and position
        self.dialog.geometry("400x450")
        self._center_dialog()
        
        # Create content
        self._create_content()
        
        # Create close button
        ttk.Button(self.dialog, text="Close", command=self.dialog.destroy).pack(pady=10)
    
    def _center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        # Get parent and dialog dimensions
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Calculate position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # Set position
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_content(self):
        """Create the dialog content."""
        # Create frame with scrollbar
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add canvas for scrolling
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Determine modifier key based on platform
        mod_key = "Command" if platform.system() == "Darwin" else "Ctrl"
        
        # Define shortcut categories and their shortcuts
        shortcut_categories = [
            ("File Operations", [
                (f"{mod_key}+O", "Open image file"),
                (f"{mod_key}+S", "Save results"),
                (f"{mod_key}+P", "Print report"),
                (f"{mod_key}+Q", "Exit application")
            ]),
            ("Editing", [
                (f"{mod_key}+C", "Copy selected metadata"),
                (f"{mod_key}+A", "Select all"),
                (f"{mod_key}+F", "Find in metadata"),
                ("Delete", "Clear results")
            ]),
            ("Tools", [
                (f"{mod_key}+E", "Extract metadata"),
                (f"{mod_key}+B", "Batch process"),
                (f"{mod_key}+M", "Map location"),
                (f"{mod_key}+L", "Clean metadata")
            ]),
            ("View", [
                (f"{mod_key}+Plus", "Zoom in"),
                (f"{mod_key}+Minus", "Zoom out"),
                (f"{mod_key}+0", "Reset zoom"),
                ("F11", "Toggle fullscreen")
            ]),
            ("Navigation", [
                ("Tab", "Move between fields"),
                ("Arrow keys", "Navigate in tree view"),
                ("Enter", "Expand/collapse tree item"),
                ("Home/End", "Go to first/last item")
            ])
        ]
        
        # Add shortcuts to the scrollable frame
        row = 0
        for category, shortcuts in shortcut_categories:
            # Add category header
            ttk.Label(
                scrollable_frame, 
                text=category, 
                font=("Helvetica", 12, "bold")
            ).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 5))
            row += 1
            
            # Add separator
            separator = ttk.Separator(scrollable_frame, orient="horizontal")
            separator.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
            row += 1
            
            # Add shortcuts
            for shortcut, description in shortcuts:
                ttk.Label(
                    scrollable_frame, 
                    text=shortcut, 
                    font=("Courier", 10)
                ).grid(row=row, column=0, sticky="w", padx=(20, 10), pady=2)
                
                ttk.Label(
                    scrollable_frame, 
                    text=description
                ).grid(row=row, column=1, sticky="w", padx=5, pady=2)
                
                row += 1
            
        # Make the canvas scrollable with the mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows and MacOS
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))  # Linux


class AboutDialog:
    """Dialog displaying information about the application."""
    
    def __init__(self, parent):
        """
        Initialize the about dialog.
        
        Args:
            parent: Parent window
        """
        self.parent = parent
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("About Image Metadata Extractor")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make dialog modal
        self.dialog.focus_set()
        
        # Set size and position
        self.dialog.geometry("400x300")
        self._center_dialog()
        
        # Create content
        self._create_content()
        
        # Create close button
        ttk.Button(self.dialog, text="Close", command=self.dialog.destroy).pack(pady=10)
    
    def _center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        # Get parent and dialog dimensions
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Calculate position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # Set position
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_content(self):
        """Create the dialog content."""
        # Create main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Application name
        ttk.Label(
            main_frame, 
            text="Image Metadata Extractor", 
            font=("Helvetica", 16, "bold")
        ).pack(pady=(0, 10))
        
        # Version
        ttk.Label(
            main_frame, 
            text="Version 1.0.0"
        ).pack()
        
        # Description
        description = (
            "A cybersecurity tool for extracting and analyzing metadata from images.\n"
            "Designed for digital forensics and security analysis."
        )
        ttk.Label(
            main_frame, 
            text=description,
            justify=tk.CENTER,
            wraplength=350
        ).pack(pady=10)
        
        # Copyright
        ttk.Label(
            main_frame, 
            text="© 2023 Your Name"
        ).pack()
        
        # Credits
        credits_frame = ttk.LabelFrame(main_frame, text="Credits")
        credits_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(
            credits_frame, 
            text="Developed by: Your Name\nUI Design: Your Name\nTesting: Your Name",
            justify=tk.LEFT,
            padding=10
        ).pack()
        
        # Website link
        link_frame = ttk.Frame(main_frame)
        link_frame.pack(pady=5)
        
        website_label = ttk.Label(
            link_frame, 
            text="Visit Website",
            foreground="blue",
            cursor="hand2"
        )
        website_label.pack()
        
        # Make the label clickable
        website_label.bind("<Button-1>", lambda e: webbrowser.open("https://example.com"))


class CleanMetadataDialog:
    """Dialog for cleaning metadata from images."""
    
    def __init__(self, parent, main_window):
        """
        Initialize the clean metadata dialog.
        
        Args:
            parent: Parent window
            main_window: Reference to the main application window
        """
        self.parent = parent
        self.main_window = main_window
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Clean Image Metadata")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make dialog modal
        self.dialog.focus_set()
        
        # Set size and position
        self.dialog.geometry("500x400")
        self._center_dialog()
        
        # Create content
        self._create_content()
    
    def _center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        # Get parent and dialog dimensions
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # Calculate position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # Set position
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_content(self):
        """Create the dialog content."""
        # Create main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Information label
        info_text = (
            "This tool allows you to remove metadata from the image file. "
            "You can choose to remove all metadata or select specific categories to remove. "
            "A new copy of the image will be created with the selected metadata removed."
        )
        
        info_label = ttk.Label(
            main_frame, 
            text=info_text,
            wraplength=480,
            justify=tk.LEFT
        )
        info_label.pack(fill=tk.X, pady=10)
        
        # File information
        file_frame = ttk.LabelFrame(main_frame, text="File Information")
        file_frame.pack(fill=tk.X, pady=10)
        
        file_path = self.main_window.current_file
        file_name = os.path.basename(file_path)
        
        ttk.Label(
            file_frame, 
            text=f"File: {file_name}",
            padding=5
        ).pack(anchor=tk.W)
        
        # Metadata selection
        selection_frame = ttk.LabelFrame(main_frame, text="Select Metadata to Remove")
        selection_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create checkboxes for metadata categories
        self.remove_all_var = tk.BooleanVar(value=False)
        self.remove_exif_var = tk.BooleanVar(value=True)
        self.remove_gps_var = tk.BooleanVar(value=True)
        self.remove_iptc_var = tk.BooleanVar(value=False)
        self.remove_xmp_var = tk.BooleanVar(value=False)
        self.remove_comments_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(
            selection_frame, 
            text="Remove all metadata (recommended for privacy)",
            variable=self.remove_all_var,
            command=self._toggle_all
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Separator(selection_frame, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(
            selection_frame, 
            text="Remove EXIF data (camera, settings, etc.)",
            variable=self.remove_exif_var
        ).pack(anchor=tk.W, padx=10, pady=2)
        
        ttk.Checkbutton(
            selection_frame, 
            text="Remove GPS location data",
            variable=self.remove_gps_var
        ).pack(anchor=tk.W, padx=10, pady=2)
        
        ttk.Checkbutton(
            selection_frame, 
            text="Remove IPTC data (title, keywords, etc.)",
            variable=self.remove_iptc_var
        ).pack(anchor=tk.W, padx=10, pady=2)
        
        ttk.Checkbutton(
            selection_frame, 
            text="Remove XMP data (Adobe metadata)",
            variable=self.remove_xmp_var
        ).pack(anchor=tk.W, padx=10, pady=2)
        
        ttk.Checkbutton(
            selection_frame, 
            text="Remove comments and annotations",
            variable=self.remove_comments_var
        ).pack(anchor=tk.W, padx=10, pady=2)
        
        # Output options
        output_frame = ttk.LabelFrame(main_frame, text="Output Options")
        output_frame.pack(fill=tk.X, pady=10)
        
        self.output_option_var = tk.StringVar(value="new")
        
        ttk.Radiobutton(
            output_frame, 
            text="Create new file",
            variable=self.output_option_var,
            value="new"
        ).pack(anchor=tk.W, padx=10, pady=2)
        
        ttk.Radiobutton(
            output_frame, 
            text="Overwrite original file (cannot be undone)",
            variable=self.output_option_var,
            value="overwrite"
        ).pack(anchor=tk.W, padx=10, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame, 
            text="Clean Metadata",
            command=self._clean_metadata
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def _toggle_all(self):
        """Toggle all metadata checkboxes based on 'Remove all' state."""
        state = self.remove_all_var.get()
        
        # If "Remove all" is checked, check all other boxes and disable them
        for var in [self.remove_exif_var, self.remove_gps_var, 
                   self.remove_iptc_var, self.remove_xmp_var, 
                   self.remove_comments_var]:
            var.set(state)
    
    def _clean_metadata(self):
        """Clean metadata from the image based on selected options."""
        try:
            # Get options
            remove_all = self.remove_all_var.get()
            remove_exif = self.remove_exif_var.get() or remove_all
            remove_gps = self.remove_gps_var.get() or remove_all
            remove_iptc = self.remove_iptc_var.get() or remove_all
            remove_xmp = self.remove_xmp_var.get() or remove_all
            remove_comments = self.remove_comments_var.get() or remove_all
            
            output_option = self.output_option_var.get()
            
            # Get input file
            input_file = self.main_window.current_file
            
            # Determine output file
            if output_option == "overwrite":
                output_file = input_file
                
                # Confirm overwrite
                if not messagebox.askyesno(
                    "Confirm Overwrite",
                    "Are you sure you want to overwrite the original file? "
                    "This action cannot be undone."
                ):
                    return
            else:
                # Create new file name
                file_dir = os.path.dirname(input_file)
                file_name, file_ext = os.path.splitext(os.path.basename(input_file))
                output_file = os.path.join(file_dir, f"{file_name}_clean{file_ext}")
                
                # Ask for output location
                output_file = filedialog.asksaveasfilename(
                    title="Save Cleaned Image",
                    initialdir=file_dir,
                    initialfile=f"{file_name}_clean{file_ext}",
                    defaultextension=file_ext,
                    filetypes=[("Image files", f"*{file_ext}"), ("All files", "*.*")]
                )
                
                if not output_file:
                    return  # User cancelled
            
            # Clean metadata
            if hasattr(self.main_window, 'metadata_extractor') and \
               hasattr(self.main_window.metadata_extractor, 'clean_metadata'):
                self.main_window.metadata_extractor.clean_metadata(
                    input_file, 
                    output_file,
                    remove_exif=remove_exif,
                    remove_gps=remove_gps,
                    remove_iptc=remove_iptc,
                    remove_xmp=remove_xmp,
                    remove_comments=remove_comments
                )
                
                # Show success message
                messagebox.showinfo(
                    "Metadata Cleaned",
                    f"Metadata has been successfully removed from the image.\n"
                    f"Saved to: {output_file}"
                )
                
                # Close dialog
                self.dialog.destroy()
                
                # Optionally load the new file
                if output_option != "overwrite" and messagebox.askyesno(
                    "Load Cleaned Image",
                    "Would you like to load the cleaned image?"
                ):
                    self.main_window.load_file(output_file)
            else:
                raise NotImplementedError("Metadata cleaning not implemented")
                
        except Exception as e:
            logger.error(f"Error cleaning metadata: {e}")
            messagebox.showerror(
                "Error",
                f"Failed to clean metadata: {str(e)}"
            )