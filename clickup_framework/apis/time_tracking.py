"""
Time Tracking API - Low-level API for ClickUp time tracking endpoints (new API).
"""

from typing import Dict, Any
from .base import BaseAPI


class TimeTrackingAPI(BaseAPI):
    """Low-level API for time tracking operations (new API)."""

    def get_time_entries(self, team_id: str, **params) -> Dict[str, Any]:
        """Get time entries."""
        return self._request("GET", f"team/{team_id}/time_entries", params=params)

    def create_time_entry(self, team_id: str, **entry_data) -> Dict[str, Any]:
        """Create a time entry."""
        return self._request("POST", f"team/{team_id}/time_entries", json=entry_data)

    def get_time_entry(self, team_id: str, timer_id: str) -> Dict[str, Any]:
        """Get a singular time entry."""
        return self._request("GET", f"team/{team_id}/time_entries/{timer_id}")

    def update_time_entry(self, team_id: str, timer_id: str, **updates) -> Dict[str, Any]:
        """Update a time entry."""
        return self._request("PUT", f"team/{team_id}/time_entries/{timer_id}", json=updates)

    def delete_time_entry(self, team_id: str, timer_id: str) -> Dict[str, Any]:
        """Delete a time entry."""
        return self._request("DELETE", f"team/{team_id}/time_entries/{timer_id}")

    def get_time_entry_history(self, team_id: str, timer_id: str) -> Dict[str, Any]:
        """Get time entry history."""
        return self._request("GET", f"team/{team_id}/time_entries/{timer_id}/history")

    def get_current_time_entry(self, team_id: str) -> Dict[str, Any]:
        """Get running time entry."""
        return self._request("GET", f"team/{team_id}/time_entries/current")

    def get_time_entry_tags(self, team_id: str) -> Dict[str, Any]:
        """Get all tags from time entries."""
        return self._request("GET", f"team/{team_id}/time_entries/tags")

    def add_time_entry_tags(self, team_id: str, **tag_data) -> Dict[str, Any]:
        """Add tags from time entries."""
        return self._request("POST", f"team/{team_id}/time_entries/tags", json=tag_data)

    def update_time_entry_tags(self, team_id: str, **tag_data) -> Dict[str, Any]:
        """Change tag names from time entries."""
        return self._request("PUT", f"team/{team_id}/time_entries/tags", json=tag_data)

    def delete_time_entry_tags(self, team_id: str, **params) -> Dict[str, Any]:
        """Remove tags from time entries."""
        return self._request("DELETE", f"team/{team_id}/time_entries/tags", params=params)

    def start_time_entry(self, team_id: str, **entry_data) -> Dict[str, Any]:
        """Start a time entry."""
        return self._request("POST", f"team/{team_id}/time_entries/start", json=entry_data)

    def stop_time_entry(self, team_id: str, **params) -> Dict[str, Any]:
        """Stop a time entry."""
        return self._request("POST", f"team/{team_id}/time_entries/stop", json=params)

