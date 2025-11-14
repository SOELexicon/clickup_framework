"""
Spaces API - Low-level API for ClickUp space endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class SpacesAPI(BaseAPI):
    """Low-level API for space operations."""

    def get_space(self, space_id: str) -> Dict[str, Any]:
        """Get space by ID."""
        return self._request("GET", f"space/{space_id}")

    def get_team_spaces(self, team_id: str, archived: bool = False) -> Dict[str, Any]:
        """Get all spaces in a team."""
        params = {"archived": str(archived).lower()}
        return self._request("GET", f"team/{team_id}/space", params=params)

    def create_space(self, team_id: str, name: str, **space_data) -> Dict[str, Any]:
        """Create a new space."""
        data = {"name": name, **space_data}
        return self._request("POST", f"team/{team_id}/space", json=data)

    def update_space(self, space_id: str, **updates) -> Dict[str, Any]:
        """Update a space."""
        return self._request("PUT", f"space/{space_id}", json=updates)

    def delete_space(self, space_id: str) -> Dict[str, Any]:
        """Delete a space."""
        return self._request("DELETE", f"space/{space_id}")

