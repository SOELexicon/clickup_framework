"""
Folders API - Low-level API for ClickUp folder endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class FoldersAPI(BaseAPI):
    """Low-level API for folder operations."""

    def get_folder(self, folder_id: str) -> Dict[str, Any]:
        """Get folder by ID."""
        return self._request("GET", f"folder/{folder_id}")

    def create_folder(self, space_id: str, name: str) -> Dict[str, Any]:
        """Create a new folder."""
        return self._request("POST", f"space/{space_id}/folder", json={"name": name})

    def update_folder(self, folder_id: str, **updates) -> Dict[str, Any]:
        """Update a folder."""
        return self._request("PUT", f"folder/{folder_id}", json=updates)

    def get_space_folders(self, space_id: str, archived: bool = False) -> Dict[str, Any]:
        """Get all folders in a space."""
        params = {"archived": str(archived).lower()}
        return self._request("GET", f"space/{space_id}/folder", params=params)

    def delete_folder(self, folder_id: str) -> Dict[str, Any]:
        """Delete a folder."""
        return self._request("DELETE", f"folder/{folder_id}")

    def create_folder_from_template(self, space_id: str, template_id: str, **folder_data) -> Dict[str, Any]:
        """Create a folder from a template."""
        return self._request("POST", f"space/{space_id}/folder_template/{template_id}", json=folder_data)

