"""
Export controller for the saved searches system.

This module provides functionality for exporting saved searches with 
various filtering options, including favorites-only export.
"""

import os
import json
from typing import Dict, List, Any, Optional, Set, Union

from refactor.storage.saved_searches import SavedSearchesManager, SavedSearch
from refactor.common.json_utils import NewlineEncoderDecoder


class SearchExportController:
    """
    Controller for exporting saved searches with various options.
    
    This class provides methods for exporting saved searches with filters
    for favorites, categories, tags, and other criteria.
    """
    
    def __init__(self, manager: SavedSearchesManager):
        """
        Initialize the export controller.
        
        Args:
            manager: The SavedSearchesManager instance to use for accessing searches
        """
        self.manager = manager
    
    def export_searches(self, 
                         output_path: Optional[str] = None,
                         favorites_only: bool = False,
                         include_templates: bool = False,
                         templates_only: bool = False,
                         category: Optional[str] = None,
                         tag: Optional[str] = None) -> str:
        """
        Export saved searches based on specified criteria.
        
        Args:
            output_path: Optional path to write the export to
            favorites_only: If True, only export favorite searches
            include_templates: If True, include templates in the export
            templates_only: If True, only export templates
            category: Optional category to filter by
            tag: Optional tag to filter by
            
        Returns:
            JSON string of the exported searches
        """
        # Get the base list of searches based on filters
        searches = self._get_filtered_searches(
            favorites_only=favorites_only,
            include_templates=include_templates,
            templates_only=templates_only,
            category=category,
            tag=tag
        )
        
        # Convert to export format
        export_data = self._create_export_data(searches)
        
        # Serialize to JSON
        json_data = NewlineEncoderDecoder.encode(export_data, indent=2)
        
        # Write to file if output path provided
        if output_path:
            with open(output_path, 'w') as f:
                f.write(json_data)
        
        return json_data
    
    def _get_filtered_searches(self, 
                               favorites_only: bool = False,
                               include_templates: bool = True,
                               templates_only: bool = False,
                               category: Optional[str] = None,
                               tag: Optional[str] = None) -> List[SavedSearch]:
        """
        Get searches filtered by the specified criteria.
        
        Args:
            favorites_only: If True, only include favorite searches
            include_templates: If True, include templates
            templates_only: If True, only include templates
            category: Optional category to filter by
            tag: Optional tag to filter by
            
        Returns:
            List of SavedSearch objects matching the criteria
        """
        # Start with the appropriate base list
        if favorites_only:
            # Get favorites with any additional filters
            searches = self.manager.list_favorites(
                category=category,
                tag=tag
            )
        else:
            # Get all searches with any additional filters
            searches = self.manager.list_searches(
                category=category,
                tag=tag
            )
        
        # Filter based on template status
        if templates_only:
            searches = [s for s in searches if s.is_template]
        elif not include_templates:
            searches = [s for s in searches if not s.is_template]
        
        return searches
    
    def _create_export_data(self, searches: List[SavedSearch]) -> Dict[str, Any]:
        """
        Create the export data structure from a list of searches.
        
        Args:
            searches: List of SavedSearch objects to export
            
        Returns:
            Dictionary with export data
        """
        # Convert searches to dictionary format for export
        search_dicts = [search.to_dict() for search in searches]
        
        # Create the export data structure
        export_data = {
            "format_version": "1.0",
            "count": len(search_dicts),
            "searches": search_dicts
        }
        
        return export_data
    
    def import_searches(self, 
                         import_path: str,
                         mode: str = "skip") -> Dict[str, Any]:
        """
        Import searches from a file.
        
        Args:
            import_path: Path to the file to import
            mode: Import mode - "skip" (default), "replace", or "rename"
            
        Returns:
            Dict with import statistics
        """
        # Read the import file
        with open(import_path, 'r') as f:
            json_data = f.read()
        
        # Parse the JSON
        import_data = NewlineEncoderDecoder.decode(json_data)
        
        # Validate format
        if not isinstance(import_data, dict) or "searches" not in import_data:
            raise ValueError("Invalid import file format")
        
        # Import the searches
        search_list = import_data.get("searches", [])
        
        # Statistics
        stats = {
            "total": len(search_list),
            "imported": 0,
            "skipped": 0,
            "replaced": 0,
            "renamed": 0,
            "errors": 0
        }
        
        # Process each search
        for search_data in search_list:
            try:
                self._import_single_search(search_data, mode, stats)
            except Exception as e:
                stats["errors"] += 1
        
        return stats
    
    def _import_single_search(self, 
                              search_data: Dict[str, Any],
                              mode: str,
                              stats: Dict[str, int]) -> None:
        """
        Import a single search.
        
        Args:
            search_data: Dictionary with search data
            mode: Import mode ("skip", "replace", or "rename")
            stats: Dictionary to update with import statistics
        """
        name = search_data.get("name", "")
        if not name:
            stats["errors"] += 1
            return
        
        # Check if search already exists
        existing_search = self.manager.get_search(name)
        
        if existing_search:
            if mode == "skip":
                stats["skipped"] += 1
                return
            elif mode == "replace":
                self.manager.delete_search(name)
                stats["replaced"] += 1
            elif mode == "rename":
                # Find a new unique name
                counter = 1
                new_name = f"{name}_import_{counter}"
                while self.manager.get_search(new_name):
                    counter += 1
                    new_name = f"{name}_import_{counter}"
                
                # Update the name in the data
                search_data["name"] = new_name
                stats["renamed"] += 1
        
        # Create the search
        if search_data.get("is_template", False):
            # Create as template
            variables = search_data.get("variables", [])
            result = self.manager.save_template(
                name=search_data["name"],
                query=search_data["query"],
                variables=variables,
                description=search_data.get("description", ""),
                tags=search_data.get("tags", []),
                category=search_data.get("category", "general")
            )
        else:
            # Create as regular search
            result = self.manager.save_search(
                name=search_data["name"],
                query=search_data["query"],
                description=search_data.get("description", ""),
                tags=search_data.get("tags", []),
                category=search_data.get("category", "general")
            )
        
        # Set favorite status if needed
        if search_data.get("is_favorite", False):
            self.manager.add_to_favorites(search_data["name"])
        
        stats["imported"] += 1 