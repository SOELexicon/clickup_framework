"""
Goals API - Low-level API for ClickUp goal endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class GoalsAPI(BaseAPI):
    """Low-level API for goal operations."""

    def get_goals(self, team_id: str, **params) -> Dict[str, Any]:
        """Get goals for a workspace."""
        return self._request("GET", f"team/{team_id}/goal", params=params)

    def create_goal(self, team_id: str, **goal_data) -> Dict[str, Any]:
        """Create a goal."""
        return self._request("POST", f"team/{team_id}/goal", json=goal_data)

    def get_goal(self, goal_id: str) -> Dict[str, Any]:
        """Get a goal by ID."""
        return self._request("GET", f"goal/{goal_id}")

    def update_goal(self, goal_id: str, **updates) -> Dict[str, Any]:
        """Update a goal."""
        return self._request("PUT", f"goal/{goal_id}", json=updates)

    def delete_goal(self, goal_id: str) -> Dict[str, Any]:
        """Delete a goal."""
        return self._request("DELETE", f"goal/{goal_id}")

    def create_key_result(self, goal_id: str, **key_result_data) -> Dict[str, Any]:
        """Create a key result for a goal."""
        return self._request("POST", f"goal/{goal_id}/key_result", json=key_result_data)

    def update_key_result(self, key_result_id: str, **updates) -> Dict[str, Any]:
        """Update a key result."""
        return self._request("PUT", f"key_result/{key_result_id}", json=updates)

    def delete_key_result(self, key_result_id: str) -> Dict[str, Any]:
        """Delete a key result."""
        return self._request("DELETE", f"key_result/{key_result_id}")

