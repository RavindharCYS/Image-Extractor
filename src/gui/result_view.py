"""
Result View Module for Image Metadata Extractor

This module contains the ResultView class which displays
the extracted metadata in a structured, tabbed interface.
"""

import tkinter as tk
from tkinter import ttk
import logging
import json
from datetime import datetime
import re
import webbrowser

# Get the package logger
logger = logging.getLogger(__name__)


class ResultView(ttk.Frame):
    """
    A widget for displaying image metadata results in a structured format.
    
    Displays metadata in categorized tabs with a tree view for hierarchical data
    and provides features like searching, copying, and linking GPS coordinates.
    """
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the ResultView widget.
        
        Args:
            parent: The parent widget
            **kwargs: Additional keyword arguments for the Frame
        """
        super().__init__(parent, **kwargs)
        
        # Initialize state
        self.metadata = None
        self.search_results = []
        self.current_search_index = -1
        
        # Create widgets
        self._create_widgets()
        self._setup_layout()
        
        logger.debug("ResultView initialized")
    
    def _create_widgets(self):
        """Create all widgets for the result view."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        
        # Create search frame
        self.search_frame = ttk.Frame(self)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_button = ttk.Button(self.search_frame, text="Search", 
                                       command=self._search_metadata)
        self.search_prev = ttk.Button(self.search_frame, text="↑", width=2, 
                                     command=lambda: self._navigate_search(-1))
        self.search_next = ttk.Button(self.search_frame, text="↓", width=2, 
                                     command=lambda: self._navigate_search(1))
        self.search_result_label = ttk.Label(self.search_frame, text="")
        
        # Create tabs for different metadata categories
        self.tabs = {}
        self.tree_views = {}
        
        # Standard metadata categories
        self.categories = [
            ("basic", "Basic Information"),
            ("exif", "EXIF Data"),
            ("gps", "GPS Location"),
            ("device", "Device Information"),
            ("file", "File Information"),
            ("all", "All Metadata")
        ]
        
        # Create each tab with a tree view
        for category_id, category_name in self.categories:
            tab = ttk.Frame(self.notebook)
            self.tabs[category_id] = tab
            
            # Create tree view with scrollbars
            tree_frame = ttk.Frame(tab)
            tree_view = ttk.Treeview(tree_frame, columns=("value"), show="tree headings")
            tree_view.heading("#0", text="Property")
            tree_view.heading("value", text="Value")
            tree_view.column("#0", width=200, stretch=tk.YES)
            tree_view.column("value", width=300, stretch=tk.YES)
            
            # Add scrollbars
            vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_view.yview)
            hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree_view.xview)
            tree_view.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            
            # Store tree view reference
            self.tree_views[category_id] = tree_view
            
            # Add context menu
            self._add_context_menu(tree_view)
            
            # Add to notebook
            self.notebook.add(tab, text=category_name)
            
            # Layout tree view and scrollbars
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            vsb.pack(side=tk.RIGHT, fill=tk.Y)
            hsb.pack(side=tk.BOTTOM, fill=tk.X)
            tree_view.pack(fill=tk.BOTH, expand=True)
            
            # Add double-click handler for GPS coordinates
            tree_view.bind("<Double-1>", self._on_tree_double_click)
    
    def _setup_layout(self):
        """Arrange widgets using pack layout manager."""
        # Search frame at the top
        self.search_frame.pack(fill=tk.X, padx=5, pady=5)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.search_button.pack(side=tk.LEFT, padx=2)
        self.search_prev.pack(side=tk.LEFT, padx=2)
        self.search_next.pack(side=tk.LEFT, padx=2)
        self.search_result_label.pack(side=tk.RIGHT, padx=5)
        
        # Notebook fills the rest of the space
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Bind search entry to Enter key
        self.search_entry.bind("<Return>", lambda e: self._search_metadata())
    
    def _add_context_menu(self, tree_view):
        """Add a context menu to the tree view."""
        context_menu = tk.Menu(tree_view, tearoff=0)
        
        context_menu.add_command(label="Copy Value", 
                                command=lambda: self._copy_selected_value(tree_view))
        context_menu.add_command(label="Copy Property", 
                                command=lambda: self._copy_selected_property(tree_view))
        context_menu.add_command(label="Copy Both", 
                                command=lambda: self._copy_selected_both(tree_view))
        context_menu.add_separator()
        context_menu.add_command(label="Expand All", 
                                command=lambda: self._expand_all(tree_view))
        context_menu.add_command(label="Collapse All", 
                                command=lambda: self._collapse_all(tree_view))
        
        # Bind right-click to show context menu
        tree_view.bind("<Button-3>", lambda e: self._show_context_menu(e, context_menu))
    
    def _show_context_menu(self, event, menu):
        """Show the context menu at the current mouse position."""
        try:
            # Select the item under the mouse
            item = event.widget.identify_row(event.y)
            if item:
                event.widget.selection_set(item)
            
            # Display the menu
            menu.post(event.x_root, event.y_root)
        finally:
            # Make sure to grab the release event
            menu.grab_release()
    
    def _copy_selected_value(self, tree_view):
        """Copy the value of the selected item to the clipboard."""
        selection = tree_view.selection()
        if selection:
            item = selection[0]
            value = tree_view.item(item, "values")[0]
            self.clipboard_clear()
            self.clipboard_append(value)
            logger.debug(f"Copied value to clipboard: {value}")
    
    def _copy_selected_property(self, tree_view):
        """Copy the property name of the selected item to the clipboard."""
        selection = tree_view.selection()
        if selection:
            item = selection[0]
            property_name = tree_view.item(item, "text")
            self.clipboard_clear()
            self.clipboard_append(property_name)
            logger.debug(f"Copied property to clipboard: {property_name}")
    
    def _copy_selected_both(self, tree_view):
        """Copy both property and value to the clipboard."""
        selection = tree_view.selection()
        if selection:
            item = selection[0]
            property_name = tree_view.item(item, "text")
            value = tree_view.item(item, "values")[0]
            text = f"{property_name}: {value}"
            self.clipboard_clear()
            self.clipboard_append(text)
            logger.debug(f"Copied to clipboard: {text}")
    
    def _expand_all(self, tree_view):
        """Expand all items in the tree view."""
        def expand_children(item):
            children = tree_view.get_children(item)
            for child in children:
                tree_view.item(child, open=True)
                expand_children(child)
        
        # Start with root items
        root_items = tree_view.get_children()
        for item in root_items:
            tree_view.item(item, open=True)
            expand_children(item)
    
    def _collapse_all(self, tree_view):
        """Collapse all items in the tree view."""
        def collapse_children(item):
            children = tree_view.get_children(item)
            for child in children:
                tree_view.item(child, open=False)
                collapse_children(child)
        
        # Start with root items
        root_items = tree_view.get_children()
        for item in root_items:
            tree_view.item(item, open=False)
            collapse_children(item)
    
    def _on_tree_double_click(self, event):
        """Handle double-click on tree items, especially for GPS coordinates."""
        tree_view = event.widget
        selection = tree_view.selection()
        
        if not selection:
            return
        
        item = selection[0]
        property_name = tree_view.item(item, "text")
        value = tree_view.item(item, "values")[0] if tree_view.item(item, "values") else ""
        
        # Check if this is a GPS coordinate
        if ("GPS" in property_name and ("Latitude" in property_name or "Longitude" in property_name)) or \
           ("Location" in property_name and re.match(r"^\s*-?\d+\.\d+,\s*-?\d+\.\d+\s*$", value)):
            self._open_gps_location()
    
    def _open_gps_location(self):
        """Open GPS coordinates in a map service."""
        if not self.metadata or "gps" not in self.metadata:
            return
        
        gps_data = self.metadata.get("gps", {})
        
        # Try to find latitude and longitude
        latitude = gps_data.get("GPS Latitude", gps_data.get("Latitude"))
        longitude = gps_data.get("GPS Longitude", gps_data.get("Longitude"))
        
        # If we have a location string, parse it
        location = gps_data.get("Location")
        if location and not (latitude and longitude):
            match = re.match(r"^\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)\s*$", location)
            if match:
                latitude, longitude = match.groups()
        
        if latitude and longitude:
            # Clean up the values
            if isinstance(latitude, str):
                latitude = latitude.strip()
            if isinstance(longitude, str):
                longitude = longitude.strip()
            
            # Open in Google Maps
            url = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
            webbrowser.open(url)
            logger.info(f"Opened GPS location in browser: {latitude}, {longitude}")
        else:
            logger.warning("No valid GPS coordinates found to open")
    
    def _search_metadata(self):
        """Search for text in the metadata."""
        search_text = self.search_var.get().lower()
        
        if not search_text or not self.metadata:
            self.search_result_label.config(text="")
            return
        
        # Reset search results
        self.search_results = []
        self.current_search_index = -1
        
        # Search in all tree views
        for category, tree_view in self.tree_views.items():
            self._search_tree(tree_view, "", search_text, category)
        
        # Update search result label
        if self.search_results:
            self.search_result_label.config(
                text=f"Found {len(self.search_results)} matches"
            )
            # Navigate to the first result
            self._navigate_search(1)
        else:
            self.search_result_label.config(text="No matches found")
    
    def _search_tree(self, tree_view, parent_item, search_text, category):
        """
        Recursively search the tree view for matching text.
        
        Args:
            tree_view: The tree view to search
            parent_item: The parent item ID to search under ("" for root)
            search_text: The text to search for (lowercase)
            category: The category ID of the tree view
        """
        items = tree_view.get_children(parent_item)
        
        for item in items:
            # Get item text and value
            item_text = tree_view.item(item, "text").lower()
            item_values = tree_view.item(item, "values")
            item_value = item_values[0].lower() if item_values else ""
            
            # Check if the text matches
            if search_text in item_text or search_text in item_value:
                self.search_results.append((category, item))
            
            # Search children
            self._search_tree(tree_view, item, search_text, category)
    
    def _navigate_search(self, direction):
        """
        Navigate through search results.
        
        Args:
            direction: 1 for next, -1 for previous
        """
        if not self.search_results:
            return
        
        # Update current index
        self.current_search_index += direction
        
        # Wrap around
        if self.current_search_index >= len(self.search_results):
            self.current_search_index = 0
        elif self.current_search_index < 0:
            self.current_search_index = len(self.search_results) - 1
        
        # Get the current result
        category, item = self.search_results[self.current_search_index]
        
        # Switch to the appropriate tab
        tab_index = next((i for i, (cat_id, _) in enumerate(self.categories) 
                         if cat_id == category), 0)
        self.notebook.select(tab_index)
        
        # Select and show the item
        tree_view = self.tree_views[category]
        tree_view.selection_set(item)
        tree_view.focus(item)
        tree_view.see(item)
        
        # Ensure parent items are expanded
        parent = tree_view.parent(item)
        while parent:
            tree_view.item(parent, open=True)
            parent = tree_view.parent(parent)
        
        # Update search result label
        self.search_result_label.config(
            text=f"Result {self.current_search_index + 1} of {len(self.search_results)}"
        )
    
    def display_metadata(self, metadata):
        """
        Display metadata in the tree views.
        
        Args:
            metadata: Dictionary containing the metadata
        """
        if not metadata:
            logger.warning("No metadata to display")
            return
        
        # Store metadata
        self.metadata = metadata
        
        # Clear all tree views
        for tree_view in self.tree_views.values():
            for item in tree_view.get_children():
                tree_view.delete(item)
        
        # Categorize metadata
        categorized = self._categorize_metadata(metadata)
        
        # Populate tree views
        for category, data in categorized.items():
            if category in self.tree_views:
                self._populate_tree(self.tree_views[category], "", data)
        
        # Populate "All Metadata" tab
        self._populate_tree(self.tree_views["all"], "", metadata)
        
        # Switch to the first tab with data
        for category_id, _ in self.categories:
            if category_id in categorized and categorized[category_id]:
                tab_index = next((i for i, (cat_id, _) in enumerate(self.categories) 
                                 if cat_id == category_id), 0)
                self.notebook.select(tab_index)
                break
        
        logger.info("Metadata displayed in result view")
    
    def _categorize_metadata(self, metadata):
        """
        Categorize metadata into different tabs.
        
        Args:
            metadata: Dictionary containing the metadata
            
        Returns:
            Dictionary with categories as keys and metadata dictionaries as values
        """
        categorized = {
            "basic": {},
            "exif": {},
            "gps": {},
            "device": {},
            "file": {}
        }
        
        # Basic information
        basic_keys = [
            "Image Size", "Width", "Height", "Format", "Mode", "Bits", "Channels",
            "ColorSpace", "Compression", "Created", "Modified", "Filename"
        ]
        
        # EXIF information
        exif_prefixes = [
            "EXIF", "Image", "Photo", "Thumbnail", "Interoperability"
        ]
        
        # GPS information
        gps_prefixes = ["GPS"]
        
        # Device information
        device_keys = [
            "Make", "Model", "Software", "CameraModel", "CameraSerialNumber",
            "LensMake", "LensModel", "LensSerialNumber", "DeviceManufacturer",
            "DeviceModel", "DeviceSerialNumber"
        ]
        
        # File information
        file_keys = [
            "FileName", "FileSize", "FileType", "FileTypeExtension", "MIMEType",
            "FileModifyDate", "FileAccessDate", "FileCreateDate", "FilePermissions"
        ]
        
        # Categorize each metadata item
        for key, value in metadata.items():
            # Skip empty values
            if value is None or value == "":
                continue
                
            # Basic information
            if any(basic_key in key for basic_key in basic_keys):
                categorized["basic"][key] = value
            
            # EXIF information
            if any(key.startswith(prefix) for prefix in exif_prefixes):
                categorized["exif"][key] = value
            
            # GPS information
            if any(key.startswith(prefix) for prefix in gps_prefixes) or "GPS" in key or "Location" in key:
                categorized["gps"][key] = value
            
            # Device information
            if any(device_key in key for device_key in device_keys):
                categorized["device"][key] = value
            
            # File information
            if any(file_key in key for file_key in file_keys) or "File" in key:
                categorized["file"][key] = value
        
        return categorized
    
    def _populate_tree(self, tree_view, parent, data, prefix=""):
        """
        Recursively populate a tree view with metadata.
        
        Args:
            tree_view: The tree view to populate
            parent: The parent item ID ("" for root)
            data: The data to display (dict, list, or value)
            prefix: Prefix for nested keys
        """
        if isinstance(data, dict):
            # Sort keys for consistent display
            sorted_keys = sorted(data.keys())
            
            for key in sorted_keys:
                value = data[key]
                display_key = key
                
                # Add prefix for nested keys
                if prefix:
                    display_key = f"{prefix}.{key}"
                
                # Handle nested dictionaries and lists
                if isinstance(value, dict) and value:
                    # Create parent item
                    item = tree_view.insert(parent, "end", text=display_key, values=("",))
                    # Recursively add children
                    self._populate_tree(tree_view, item, value)
                elif isinstance(value, list) and value:
                    # Create parent item
                    item = tree_view.insert(parent, "end", text=display_key, values=("",))
                    # Recursively add children
                    self._populate_tree(tree_view, item, value)
                else:
                    # Format the value for display
                    display_value = self._format_value(value)
                    # Add leaf item
                    tree_view.insert(parent, "end", text=display_key, values=(display_value,))
        
        elif isinstance(data, list):
            # Handle lists
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)) and item:
                    # Create parent item for complex list items
                    list_item = tree_view.insert(parent, "end", text=f"Item {i+1}", values=("",))
                    # Recursively add children
                    self._populate_tree(tree_view, list_item, item)
                else:
                    # Format the value for display
                    display_value = self._format_value(item)
                    # Add leaf item
                    tree_view.insert(parent, "end", text=f"Item {i+1}", values=(display_value,))
        
        else:
            # Handle simple values (shouldn't normally get here)
            display_value = self._format_value(data)
            tree_view.insert(parent, "end", text=prefix or "Value", values=(display_value,))
    
    def _format_value(self, value):
        """
        Format a value for display in the tree view.
        
        Args:
            value: The value to format
            
        Returns:
            Formatted string representation of the value
        """
        if value is None:
            return ""
        
        if isinstance(value, (int, float)):
            return str(value)
        
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        
        if isinstance(value, (list, tuple)):
            # Format simple lists for display
            if all(isinstance(x, (int, float, str)) for x in value):
                return ", ".join(str(x) for x in value)
            else:
                return f"[Complex list with {len(value)} items]"
        
        if isinstance(value, dict):
            return f"[Dictionary with {len(value)} items]"
        
        # Convert to string and limit length
        str_value = str(value)
        if len(str_value) > 1000:
            return str_value[:1000] + "..."
        
        return str_value
    
    def clear(self):
        """Clear all displayed metadata."""
        self.metadata = None
        self.search_results = []
        self.current_search_index = -1
        self.search_var.set("")
        self.search_result_label.config(text="")
        
        # Clear all tree views
        for tree_view in self.tree_views.values():
            for item in tree_view.get_children():
                tree_view.delete(item)
        
        logger.debug("Result view cleared")
    
    def get_metadata(self):
        """
        Get the currently displayed metadata.
        
        Returns:
            The metadata dictionary or None if no metadata is displayed
        """
        return self.metadata
    
    def highlight_important_metadata(self):
        """Highlight important or sensitive metadata items."""
        if not self.metadata:
            return
        
        # Define important or sensitive metadata keys
        important_keys = [
            "GPS", "Location", "Latitude", "Longitude",
            "Make", "Model", "SerialNumber",
            "Software", "OwnerName", "Author",
            "Copyright", "CameraID", "DeviceID"
        ]
        
        # Highlight in all tree views
        for category, tree_view in self.tree_views.items():
            self._highlight_items(tree_view, "", important_keys)
    
    def _highlight_items(self, tree_view, parent, important_keys):
        """
        Recursively highlight important items in the tree view.
        
        Args:
            tree_view: The tree view to search
            parent: The parent item ID ("" for root)
            important_keys: List of important key substrings to highlight
        """
        items = tree_view.get_children(parent)
        
        for item in items:
            # Get item text
            item_text = tree_view.item(item, "text")
            
            # Check if this is an important item
            is_important = any(key in item_text for key in important_keys)
            
            # Highlight if important
            if is_important:
                tree_view.item(item, tags=("important",))
                tree_view.tag_configure("important", background="#ffe0e0")
            
            # Process children
            self._highlight_items(tree_view, item, important_keys)
    
    def export_to_text(self):
        """
        Export the displayed metadata to a formatted text string.
        
        Returns:
            Formatted text representation of the metadata
        """
        if not self.metadata:
            return ""
        
        lines = ["Image Metadata Export", "=" * 20, ""]
        
        # Add timestamp
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Add metadata by category
        for category_id, category_name in self.categories:
            if category_id == "all":
                continue  # Skip the "all" category to avoid duplication
                
            tree_view = self.tree_views[category_id]
            if tree_view.get_children():
                lines.append(f"{category_name}")
                lines.append("-" * len(category_name))
                self._export_tree_items(tree_view, "", lines)
                lines.append("")
        
        return "\n".join(lines)
    
    def _export_tree_items(self, tree_view, parent, lines, indent=0):
        """
        Recursively export tree items to text lines.
        
        Args:
            tree_view: The tree view to export
            parent: The parent item ID ("" for root)
            lines: List to append text lines to
            indent: Current indentation level
        """
        items = tree_view.get_children(parent)
        
        for item in items:
            # Get item text and value
            item_text = tree_view.item(item, "text")
            item_values = tree_view.item(item, "values")
            item_value = item_values[0] if item_values else ""
            
            # Add to lines with proper indentation
            if item_value:
                lines.append(f"{' ' * indent}{item_text}: {item_value}")
            else:
                lines.append(f"{' ' * indent}{item_text}:")
            
            # Process children with increased indentation
            self._export_tree_items(tree_view, item, lines, indent + 2)