"""
Lists API - Low-level API for ClickUp list endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class ListsAPI(BaseAPI):
    """Low-level API for list operations."""

    def get_list(self, list_id: str) -> Dict[str, Any]:
        """Get list by ID."""
        return self._request("GET", f"list/{list_id}")

    def create_list(self, folder_id: str, name: str, **list_data) -> Dict[str, Any]:
        """Create a new list."""
        data = {"name": name, **list_data}
        return self._request("POST", f"folder/{folder_id}/list", json=data)

    def get_folder_lists(self, folder_id: str, archived: bool = False) -> Dict[str, Any]:
        """Get all lists in a folder."""
        params = {"archived": str(archived).lower()}
        return self._request("GET", f"folder/{folder_id}/list", params=params)

    def get_space_lists(self, space_id: str, archived: bool = False) -> Dict[str, Any]:
        """Get folderless lists in a space."""
        params = {"archived": str(archived).lower()}
        return self._request("GET", f"space/{space_id}/list", params=params)

    def create_space_list(self, space_id: str, name: str, **list_data) -> Dict[str, Any]:
        """Create a folderless list in a space."""
        data = {"name": name, **list_data}
        return self._request("POST", f"space/{space_id}/list", json=data)

    def delete_list(self, list_id: str) -> Dict[str, Any]:
        """Delete a list."""
        return self._request("DELETE", f"list/{list_id}")

    def update_list(self, list_id: str, **updates) -> Dict[str, Any]:
        """Update a list."""
        return self._request("PUT", f"list/{list_id}", json=updates)

    def add_task_to_list(self, list_id: str, task_id: str) -> Dict[str, Any]:
        """Add a task to a list."""
        return self._request("POST", f"list/{list_id}/task/{task_id}")

    def remove_task_from_list(self, list_id: str, task_id: str) -> Dict[str, Any]:
        """Remove a task from a list."""
        return self._request("DELETE", f"list/{list_id}/task/{task_id}")

    def create_list_from_template_in_folder(self, folder_id: str, template_id: str, **list_data) -> Dict[str, Any]:
        """Create a list from a template in a folder."""
        return self._request("POST", f"folder/{folder_id}/list_template/{template_id}", json=list_data)

    def create_list_from_template_in_space(self, space_id: str, template_id: str, **list_data) -> Dict[str, Any]:
        """Create a list from a template in a space."""
        return self._request("POST", f"space/{space_id}/list_template/{template_id}", json=list_data)

