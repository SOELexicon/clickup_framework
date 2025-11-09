"""Saved Searches Storage module

This module provides functionality for storing and retrieving saved search queries.
It uses a JSON file to persist search queries and provides methods to:
- Save a new search query
- Load a saved search query
- List all saved search queries
- Delete a saved search query
- Track search history
- Create and use search templates with variables
"""

import os
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from collections import deque

from refactor.storage.providers.json_storage_provider import JsonStorageProvider
from refactor.core.exceptions import (
    StorageError,
    FileOperationError
)
from refactor.common.json_utils import NewlineEncoderDecoder


class SavedSearch:
    """
    Represents a saved search query with metadata.
    """
    
    # Regular expression to find variable placeholders like ${variable_name}
    VARIABLE_PATTERN = re.compile(r'\$\{([a-zA-Z0-9_]+)\}')
    
    def __init__(self, name: str, query: str, description: str = "", 
                 tags: List[str] = None, category: str = "general", 
                 is_template: bool = False, variables: List[str] = None,
                 is_favorite: bool = False):
        self.name = name
        self.query = query
        self.description = description
        self.tags = tags or []
        self.category = category
        self.is_template = is_template
        self.is_favorite = is_favorite
        
        # Initialize variables based on the provided list or extract from query
        if is_template:
            if variables:
                self.variables = variables
            else:
                # Extract variable names from the query
                self.variables = self._extract_variables(query)
        else:
            self.variables = []
            
        # Track creation time and usage statistics
        self.created_at = time.time()
        self.last_used_at = None
        self.use_count = 0
    
    def _extract_variables(self, query: str) -> List[str]:
        """Extract variable names from a query string."""
        matches = self.VARIABLE_PATTERN.findall(query)
        return list(set(matches))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "query": self.query,
            "description": self.description,
            "tags": self.tags,
            "category": self.category,
            "is_template": self.is_template,
            "variables": self.variables,
            "is_favorite": self.is_favorite,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "use_count": self.use_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SavedSearch':
        """Create a SavedSearch instance from a dictionary."""
        saved_search = cls(
            name=data["name"],
            query=data["query"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            category=data.get("category", "general"),
            is_template=data.get("is_template", False),
            variables=data.get("variables", []),
            is_favorite=data.get("is_favorite", False)
        )
        saved_search.created_at = data.get("created_at", time.time())
        saved_search.last_used_at = data.get("last_used_at")
        saved_search.use_count = data.get("use_count", 0)
        return saved_search
    
    def mark_used(self):
        """Update usage statistics when the search is used."""
        self.last_used_at = time.time()
        self.use_count += 1
    
    def substitute_variables(self, variables: Dict[str, str]) -> str:
        """Replace variable placeholders in the query with provided values."""
        if not self.is_template:
            return self.query
            
        result = self.query
        
        for var_name in self.variables:
            placeholder = f"${{{var_name}}}"
            
            if var_name not in variables:
                raise ValueError(f"Missing value for template variable '{var_name}'")
                
            result = result.replace(placeholder, variables[var_name])
            
        return result
    
    def get_required_variables(self) -> List[str]:
        """Get the list of variables required by this template."""
        return self.variables


class SearchHistoryEntry:
    """
    Represents an entry in the search history.
    """
    
    def __init__(self, query: str, saved_search_name: Optional[str] = None,
                 template_variables: Optional[Dict[str, str]] = None):
        self.query = query
        self.saved_search_name = saved_search_name
        self.template_variables = template_variables or {}
        self.executed_at = time.time()
        self.result_count = 0
    
    def set_result_count(self, count: int):
        """Set the number of results returned by this search."""
        self.result_count = count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query,
            "saved_search_name": self.saved_search_name,
            "template_variables": self.template_variables,
            "executed_at": self.executed_at,
            "result_count": self.result_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchHistoryEntry':
        """Create a SearchHistoryEntry instance from a dictionary."""
        entry = cls(
            query=data["query"],
            saved_search_name=data.get("saved_search_name"),
            template_variables=data.get("template_variables", {})
        )
        entry.executed_at = data.get("executed_at", time.time())
        entry.result_count = data.get("result_count", 0)
        return entry


class SavedSearchesManager:
    """
    Manages saved searches with persistence using JSON storage.
    """
    
    # Maximum number of entries to keep in the search history
    DEFAULT_HISTORY_LIMIT = 50
    
    def __init__(
        self,
        storage_file: Optional[str] = None,
        storage_dir: Optional[str] = None,
        history_limit: int = 100
    ):
        """
        Initialize a new saved searches manager.
        
        Args:
            storage_file: Path to the storage file
            storage_dir: Optional directory for storing the file (takes precedence over storage_file)
            history_limit: Maximum number of history entries to keep
        """
        self.searches = {}
        self.history = []
        self.history_limit = history_limit
        
        # Set default storage file if not provided
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)
            self.storage_file = os.path.join(storage_dir, "saved_searches.json")
        elif storage_file:
            self.storage_file = storage_file
        else:
            default_dir = os.path.join(os.path.expanduser("~"), ".clickup_json_manager")
            os.makedirs(default_dir, exist_ok=True)
            self.storage_file = os.path.join(default_dir, "saved_searches.json")
        
        # Load searches from storage
        self._load_searches()
    
    def _get_storage_path(self, storage_dir: Optional[str] = None) -> str:
        """Get the path to the storage file."""
        if storage_dir:
            storage_path = os.path.join(storage_dir, "saved_searches.json")
        else:
            config_dir = self._get_config_dir()
            storage_path = os.path.join(config_dir, "saved_searches.json")
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        return storage_path
    
    def _get_config_dir(self) -> str:
        """Get the configuration directory based on the platform."""
        home_dir = os.path.expanduser("~")
        
        if os.name == "nt":  # Windows
            config_dir = os.path.join(home_dir, "AppData", "Local", "ClickUpJsonManager")
        else:  # Unix/Linux/MacOS
            config_dir = os.path.join(home_dir, ".config", "clickup_json_manager")
            
        os.makedirs(config_dir, exist_ok=True)
        
        return config_dir
    
    def _load_searches(self) -> None:
        """Load saved searches from the storage file."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    
                # Load saved searches
                if "searches" in data:
                    for search_data in data["searches"]:
                        search = SavedSearch.from_dict(search_data)
                        self.searches[search.name] = search
                        
                # Load search history
                if "history" in data:
                    for history_data in data["history"]:
                        entry = SearchHistoryEntry.from_dict(history_data)
                        self.history.append(entry)
        except Exception as e:
            # Handle errors gracefully, starting with empty collections if needed
            print(f"Error loading saved searches: {str(e)}")
            self.searches = {}
            self.history = []
    
    def _save_searches(self) -> None:
        """Save the searches to the storage file."""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            data = {
                "searches": {name: search.to_dict() for name, search in self.searches.items()},
                "history": [entry.to_dict() for entry in self.history]
            }
            
            # Use the write_to_file method instead of direct json.dump
            NewlineEncoderDecoder.write_to_file(data, self.storage_file, indent=2)
        except Exception as e:
            # Create a more descriptive error message
            error_message = f"Failed to save searches: {str(e)}"
            raise FileOperationError(self.storage_file, "save", error_message) from e
    
    def save_search(self, name: str, query: str, description: str = "", 
                  tags: List[str] = None, category: str = "general",
                  is_template: bool = False, variables: List[str] = None,
                  is_favorite: bool = False) -> SavedSearch:
        """Save a search query."""
        # Check if a search with this name already exists
        if name in self.searches:
            raise ValueError(f"A saved search with name '{name}' already exists")
            
        # Create the saved search
        search = SavedSearch(
            name=name,
            query=query,
            description=description,
            tags=tags,
            category=category,
            is_template=is_template,
            variables=variables,
            is_favorite=is_favorite
        )
        
        # Add to the collection
        self.searches[name] = search
        
        # Save changes
        self._save_searches()
        
        return search
        
    def get_search(self, name: str) -> SavedSearch:
        """Get a saved search by name."""
        if name not in self.searches:
            raise KeyError(f"No saved search found with name '{name}'")
            
        return self.searches[name]
        
    def delete_search(self, name: str) -> None:
        """Delete a saved search."""
        if name not in self.searches:
            raise KeyError(f"No saved search found with name '{name}'")
            
        # Remove from the collection
        del self.searches[name]
        
        # Save changes
        self._save_searches()
        
    def update_search(self, name: str, **kwargs) -> SavedSearch:
        """Update a saved search."""
        if name not in self.searches:
            raise KeyError(f"No saved search found with name '{name}'")
            
        search = self.searches[name]
        
        # Update fields
        if "query" in kwargs:
            search.query = kwargs["query"]
            # If this is a template, update variables
            if search.is_template:
                search.variables = search._extract_variables(search.query)
                
        if "description" in kwargs:
            search.description = kwargs["description"]
            
        if "tags" in kwargs:
            search.tags = kwargs["tags"]
            
        if "category" in kwargs:
            search.category = kwargs["category"]
            
        if "is_template" in kwargs:
            search.is_template = kwargs["is_template"]
            if search.is_template:
                search.variables = search._extract_variables(search.query)
            else:
                search.variables = []
                
        if "is_favorite" in kwargs:
            search.is_favorite = kwargs["is_favorite"]
            
        # Save changes
        self._save_searches()
        
        return search
        
    def list_searches(self, category: Optional[str] = None, 
                     tag: Optional[str] = None, 
                     is_template: Optional[bool] = None,
                     is_favorite: Optional[bool] = None) -> List[SavedSearch]:
        """List saved searches, optionally filtered by criteria."""
        # Start with all searches
        result = list(self.searches.values())
        
        # Apply filters
        if category is not None:
            result = [s for s in result if s.category == category]
            
        if tag is not None:
            result = [s for s in result if tag in s.tags]
            
        if is_template is not None:
            result = [s for s in result if s.is_template == is_template]
            
        if is_favorite is not None:
            result = [s for s in result if s.is_favorite == is_favorite]
            
        return result
        
    def list_categories(self) -> List[str]:
        """Get a list of all categories used in saved searches."""
        return list(set(search.category for search in self.searches.values()))
        
    def list_tags(self) -> List[str]:
        """Get a list of all tags used in saved searches."""
        all_tags = []
        for search in self.searches.values():
            all_tags.extend(search.tags)
            
        return list(set(all_tags))
        
    def execute_search(self, name: str, variables: Dict[str, str] = None) -> str:
        """Execute a saved search, processing template variables if needed."""
        # Get the saved search
        search = self.get_search(name)
        
        # Process template variables if needed
        variables = variables or {}
        query = search.substitute_variables(variables) if search.is_template else search.query
        
        # Record the usage
        search.mark_used()
        
        # Add to search history
        history_entry = SearchHistoryEntry(
            query=query,
            saved_search_name=name,
            template_variables=variables if search.is_template else None
        )
        self.history.append(history_entry)
        
        # Save changes (to update usage stats)
        self._save_searches()
        
        return query
        
    def add_to_history(self, query: str, saved_search_name: Optional[str] = None, result_count: Optional[int] = None) -> None:
        """
        Add a search query to history.
        
        Args:
            query: The search query
            saved_search_name: Name of the saved search if any
            result_count: Number of results from the search
        """
        entry = SearchHistoryEntry(query, saved_search_name)
        if result_count is not None:
            entry.set_result_count(result_count)
        
        # Add to history (newest first)
        self.history.insert(0, entry)
        
        # Limit history size
        if len(self.history) > self.history_limit:
            self.history = self.history[:self.history_limit]
        
        # Save to storage
        self._save_searches()
        
    def get_history(self, limit: Optional[int] = None, query_contains: Optional[str] = None) -> List[SearchHistoryEntry]:
        """
        Get search history entries, newest first.
        
        Args:
            limit: Maximum number of entries to return
            query_contains: Filter entries containing this string in the query
            
        Returns:
            List of history entries
        """
        # Filter by query if needed
        if query_contains:
            filtered = [entry for entry in self.history if query_contains.lower() in entry.query.lower()]
        else:
            filtered = self.history[:]
        
        # Apply limit if needed
        if limit is not None and limit > 0:
            filtered = filtered[:limit]
        
        return filtered

    def clear_history(self) -> int:
        """
        Clear all search history.
        
        Returns:
            Number of entries that were cleared
        """
        count = len(self.history)
        self.history = []
        self._save_searches()
        return count

    def delete_history_entry(self, timestamp: float) -> bool:
        """
        Delete a specific history entry by timestamp.
        
        Args:
            timestamp: The timestamp of the entry to delete
            
        Returns:
            True if the entry was found and deleted, False otherwise
        """
        original_count = len(self.history)
        
        # Filter out the entry with the matching timestamp
        self.history = [entry for entry in self.history if entry.executed_at != timestamp]
        
        # Check if any entry was removed
        if len(self.history) < original_count:
            self._save_searches()
            return True
        
        return False
        
    def save_template(self, name: str, query: str, variables: List[str] = None, 
                     description: str = "", tags: List[str] = None, 
                     category: str = "templates", is_favorite: bool = False) -> SavedSearch:
        """
        Save a search query as a template with variables.
        
        Args:
            name: Unique name for the template
            query: The search query string with variables in ${variable} format
            variables: List of variable names
            description: Optional description of the template
            tags: Optional list of tags for categorization
            category: Optional category for organizing templates
            is_favorite: Whether this template should be marked as a favorite
            
        Returns:
            The saved template object
        """
        return self.save_search(
            name=name,
            query=query,
            description=description,
            tags=tags,
            category=category,
            is_template=True,
            variables=variables,
            is_favorite=is_favorite
        )
        
    def add_to_favorites(self, name_or_names: Union[str, List[str]]) -> Union[bool, Tuple[int, List[str]]]:
        """
        Add one or more searches to favorites.
        
        Args:
            name_or_names: Name of the search or list of search names
            
        Returns:
            If a single name, returns True if successful or False if not found
            If a list of names, returns (success_count, failed_names)
        """
        if isinstance(name_or_names, list):
            success_count = 0
            failed_names = []
            
            for name in name_or_names:
                try:
                    search = self.get_search(name)
                    search.is_favorite = True
                    success_count += 1
                except KeyError:
                    failed_names.append(name)
            
            self._save_searches()
            return success_count, failed_names
        else:
            try:
                search = self.get_search(name_or_names)
                search.is_favorite = True
                self._save_searches()
                return True
            except KeyError:
                return False
        
    def remove_from_favorites(self, name_or_names: Union[str, List[str]]) -> Union[bool, Tuple[int, List[str]]]:
        """
        Remove one or more searches from favorites.
        
        Args:
            name_or_names: Name of the search or list of search names
            
        Returns:
            If a single name, returns True if successful or False if not found
            If a list of names, returns (success_count, failed_names)
        """
        if isinstance(name_or_names, list):
            success_count = 0
            failed_names = []
            
            for name in name_or_names:
                try:
                    search = self.get_search(name)
                    search.is_favorite = False
                    success_count += 1
                except KeyError:
                    failed_names.append(name)
            
            self._save_searches()
            return success_count, failed_names
        else:
            try:
                search = self.get_search(name_or_names)
                search.is_favorite = False
                self._save_searches()
                return True
            except KeyError:
                return False
                
    def list_favorites(self, category: Optional[str] = None, 
                      tag: Optional[str] = None,
                      name_contains: Optional[str] = None) -> List[SavedSearch]:
        """
        List favorite searches, optionally filtered by criteria.
        
        Args:
            category: Filter by category
            tag: Filter by tag
            name_contains: Filter by name containing this string
            
        Returns:
            List of favorite searches matching the criteria
        """
        # Start with all searches
        favorites = [s for s in self.searches.values() if s.is_favorite]
        
        # Apply filters
        if category is not None:
            favorites = [s for s in favorites if s.category == category]
            
        if tag is not None:
            favorites = [s for s in favorites if tag in s.tags]
            
        if name_contains is not None:
            favorites = [s for s in favorites if name_contains.lower() in s.name.lower()]
            
        return favorites
        
    def toggle_favorite(self, name: str) -> bool:
        """
        Toggle the favorite status of a search.
        
        Args:
            name: Name of the search
            
        Returns:
            New favorite status or False if the search doesn't exist
        """
        search = self.searches.get(name)
        if not search:
            return False
        
        # Toggle the status
        search.is_favorite = not search.is_favorite
        self._save_searches()
        
        # Return the new status
        return search.is_favorite
            
    # Batch operations
    
    def batch_delete(self, names: List[str]) -> Tuple[int, List[str]]:
        """
        Delete multiple searches at once.
        
        Args:
            names: List of search names to delete
            
        Returns:
            Tuple of (success_count, failed_names)
        """
        if not names:
            return 0, []
            
        success_count = 0
        failed_names = []
        
        for name in names:
            try:
                self.delete_search(name)
                success_count += 1
            except KeyError:
                failed_names.append(name)
                
        return success_count, failed_names
        
    def batch_categorize(self, names: List[str], category: str) -> Tuple[int, List[str]]:
        """
        Set category for multiple searches at once.
        
        Args:
            names: List of search names to update
            category: New category to set
            
        Returns:
            Tuple of (success_count, failed_names)
        """
        if not names:
            return 0, []
            
        success_count = 0
        failed_names = []
        
        for name in names:
            try:
                search = self.get_search(name)
                search.category = category
                success_count += 1
            except KeyError:
                failed_names.append(name)
                
        if success_count > 0:
            self._save_searches()
                
        return success_count, failed_names
        
    def batch_add_tags(self, names: List[str], tags: List[str]) -> Tuple[int, List[str]]:
        """
        Add tags to multiple searches at once.
        
        Args:
            names: List of search names to update
            tags: Tags to add to each search
            
        Returns:
            Tuple of (success_count, failed_names)
        """
        if not names or not tags:
            return 0, []
            
        success_count = 0
        failed_names = []
        
        for name in names:
            try:
                search = self.get_search(name)
                for tag in tags:
                    if tag not in search.tags:
                        search.tags.append(tag)
                success_count += 1
            except KeyError:
                failed_names.append(name)
                
        if success_count > 0:
            self._save_searches()
                
        return success_count, failed_names
        
    def batch_remove_tags(self, names: List[str], tags: List[str]) -> Tuple[int, List[str]]:
        """
        Remove tags from multiple searches at once.
        
        Args:
            names: List of search names to update
            tags: Tags to remove from each search
            
        Returns:
            Tuple of (success_count, failed_names)
        """
        if not names or not tags:
            return 0, []
            
        success_count = 0
        failed_names = []
        
        for name in names:
            try:
                search = self.get_search(name)
                search.tags = [t for t in search.tags if t not in tags]
                success_count += 1
            except KeyError:
                failed_names.append(name)
                
        if success_count > 0:
            self._save_searches()
                
        return success_count, failed_names
        
    def batch_toggle_favorite(self, names: List[str], favorite_status: bool) -> Tuple[int, List[str]]:
        """
        Set favorite status for multiple searches at once.
        
        Args:
            names: List of search names to update
            favorite_status: True to mark as favorite, False to unmark
            
        Returns:
            Tuple of (success_count, failed_names)
        """
        if not names:
            return 0, []
            
        success_count = 0
        failed_names = []
        
        for name in names:
            try:
                search = self.get_search(name)
                search.is_favorite = favorite_status
                success_count += 1
            except KeyError:
                failed_names.append(name)
                
        if success_count > 0:
            self._save_searches()
                
        return success_count, failed_names
        
    # Alias methods for backward compatibility
    
    def delete_searches(self, names: List[str]) -> Tuple[int, List[str]]:
        """Alias for batch_delete."""
        return self.batch_delete(names)
        
    def categorize_searches(self, names: List[str], category: str) -> Tuple[int, List[str]]:
        """Alias for batch_categorize."""
        return self.batch_categorize(names, category)
        
    def tag_searches(self, names: List[str], tags: List[str]) -> Tuple[int, List[str]]:
        """Alias for batch_add_tags."""
        return self.batch_add_tags(names, tags)
        
    def untag_searches(self, names: List[str], tags: List[str]) -> Tuple[int, List[str]]:
        """Alias for batch_remove_tags."""
        return self.batch_remove_tags(names, tags)

    def list_templates(self, category: Optional[str] = None) -> List[SavedSearch]:
        """
        List all search templates.
        
        Args:
            category: Optional category to filter by
            
        Returns:
            List of search templates
        """
        # Filter templates
        templates = [search for search in self.searches.values() if search.is_template]
        
        # Apply category filter if provided
        if category:
            templates = [t for t in templates if t.category == category]
        
        return templates

    def _extract_template_variables(self, query: str) -> List[str]:
        """
        Extract variable names from a template query.
        
        Args:
            query: The template query string
            
        Returns:
            List of variable names
        """
        import re
        
        # Pattern for ${variable_name}
        var_pattern = r'\${([a-zA-Z0-9_]+)}'
        
        # Find all matches
        matches = re.findall(var_pattern, query)
        
        # Return unique variable names
        return list(set(matches))

    def _substitute_variables(self, template_query: str, variables: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
        """
        Replace variables in a template query with their values.
        
        Args:
            template_query: The template query string
            variables: Dictionary of variable names to values
            
        Returns:
            Tuple of (substituted query string, used variables)
            
        Raises:
            ValueError: If a required variable is missing
        """
        # Extract variables from the template
        template_vars = self._extract_template_variables(template_query)
        
        # Check that all required variables are provided
        used_vars = {}
        for var_name in template_vars:
            if var_name not in variables:
                raise ValueError(f"Missing value for template variable '{var_name}'")
            used_vars[var_name] = variables[var_name]
        
        # Perform substitution
        result_query = template_query
        for var_name, value in used_vars.items():
            placeholder = f"${{{var_name}}}"
            # Determine if the value should be quoted
            # If the value is already a number, don't add quotes
            try:
                float(value)  # Check if it's a number
                result_query = result_query.replace(placeholder, value)
            except ValueError:
                # Not a number, use the value as is (it might already have quotes)
                result_query = result_query.replace(placeholder, value)
        
        return result_query, used_vars

    def execute_search_template(self, name: str, variables: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
        """
        Execute a search template by substituting variables.
        
        Args:
            name: Name of the template
            variables: Dictionary of variable values
            
        Returns:
            Tuple of (result query, used variables)
            
        Raises:
            ValueError: If the search is not a template or a variable is missing
        """
        # Get the template
        search = self.get_search(name)
        
        # Check if it's actually a template
        if not search.is_template:
            raise ValueError(f"Search '{name}' is not a template")
        
        # Substitute variables
        return self._substitute_variables(search.query, variables)
