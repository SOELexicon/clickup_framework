"""
Guests API - Low-level API for ClickUp guest endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class GuestsAPI(BaseAPI):
    """Low-level API for guest operations."""

    def invite_guest_to_workspace(self, team_id: str, **guest_data) -> Dict[str, Any]:
        """Invite a guest to workspace."""
        return self._request("POST", f"team/{team_id}/guest", json=guest_data)

    def get_guest(self, team_id: str, guest_id: str) -> Dict[str, Any]:
        """Get a guest."""
        return self._request("GET", f"team/{team_id}/guest/{guest_id}")

    def update_guest(self, team_id: str, guest_id: str, **updates) -> Dict[str, Any]:
        """Edit a guest on workspace."""
        return self._request("PUT", f"team/{team_id}/guest/{guest_id}", json=updates)

    def remove_guest_from_workspace(self, team_id: str, guest_id: str) -> Dict[str, Any]:
        """Remove a guest from workspace."""
        return self._request("DELETE", f"team/{team_id}/guest/{guest_id}")

    def add_guest_to_task(self, task_id: str, guest_id: str, **params) -> Dict[str, Any]:
        """Add a guest to a task."""
        return self._request("POST", f"task/{task_id}/guest/{guest_id}", params=params)

    def remove_guest_from_task(self, task_id: str, guest_id: str, **params) -> Dict[str, Any]:
        """Remove a guest from a task."""
        return self._request("DELETE", f"task/{task_id}/guest/{guest_id}", params=params)

    def add_guest_to_list(self, list_id: str, guest_id: str) -> Dict[str, Any]:
        """Add a guest to a list."""
        return self._request("POST", f"list/{list_id}/guest/{guest_id}")

    def remove_guest_from_list(self, list_id: str, guest_id: str) -> Dict[str, Any]:
        """Remove a guest from a list."""
        return self._request("DELETE", f"list/{list_id}/guest/{guest_id}")

    def add_guest_to_folder(self, folder_id: str, guest_id: str) -> Dict[str, Any]:
        """Add a guest to a folder."""
        return self._request("POST", f"folder/{folder_id}/guest/{guest_id}")

    def remove_guest_from_folder(self, folder_id: str, guest_id: str) -> Dict[str, Any]:
        """Remove a guest from a folder."""
        return self._request("DELETE", f"folder/{folder_id}/guest/{guest_id}")

