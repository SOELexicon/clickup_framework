"""
Custom Fields API - Low-level API for ClickUp custom field endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class CustomFieldsAPI(BaseAPI):
    """Low-level API for custom field operations."""

    def get_accessible_custom_fields(self, list_id: str) -> Dict[str, Any]:
        """Get custom fields accessible from a list."""
        return self._request("GET", f"list/{list_id}/field")

    def get_folder_custom_fields(self, folder_id: str) -> Dict[str, Any]:
        """Get custom fields accessible from a folder."""
        return self._request("GET", f"folder/{folder_id}/field")

    def get_space_custom_fields(self, space_id: str) -> Dict[str, Any]:
        """Get custom fields accessible from a space."""
        return self._request("GET", f"space/{space_id}/field")

    def get_workspace_custom_fields(self, team_id: str) -> Dict[str, Any]:
        """Get all custom fields in a workspace."""
        return self._request("GET", f"team/{team_id}/field")

    def set_custom_field_value(self, task_id: str, field_id: str, value: Any) -> Dict[str, Any]:
        """Set custom field value on a task."""
        return self._request("POST", f"task/{task_id}/field/{field_id}", json={"value": value})

    def remove_custom_field_value(self, task_id: str, field_id: str) -> Dict[str, Any]:
        """Remove custom field value from a task."""
        return self._request("DELETE", f"task/{task_id}/field/{field_id}")

