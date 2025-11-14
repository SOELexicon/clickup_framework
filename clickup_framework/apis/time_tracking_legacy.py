"""
Time Tracking Legacy API - Low-level API for ClickUp legacy time tracking endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class TimeTrackingLegacyAPI(BaseAPI):
    """Low-level API for legacy time tracking operations."""

    def get_task_time(self, task_id: str, **params) -> Dict[str, Any]:
        """Get tracked time for a task (legacy)."""
        return self._request("GET", f"task/{task_id}/time", params=params)

    def track_task_time(self, task_id: str, **time_data) -> Dict[str, Any]:
        """Track time on a task (legacy)."""
        return self._request("POST", f"task/{task_id}/time", json=time_data)

    def update_task_time_entry(self, task_id: str, interval_id: str, **updates) -> Dict[str, Any]:
        """
        Update a time entry (legacy).

        Args:
            task_id: Task ID
            interval_id: Time entry interval ID
            **updates: Fields to update (start, end, duration, description, etc.)

        Returns:
            Updated time entry
        """
        return self._request("PUT", f"task/{task_id}/time/{interval_id}", json=updates)

    def delete_task_time_entry(self, task_id: str, interval_id: str) -> Dict[str, Any]:
        """Delete a time entry (legacy)."""
        return self._request("DELETE", f"task/{task_id}/time/{interval_id}")

