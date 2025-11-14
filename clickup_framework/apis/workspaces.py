"""
Workspaces API - Low-level API for ClickUp workspace endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class WorkspacesAPI(BaseAPI):
    """Low-level API for workspace operations."""

    def get_workspace_hierarchy(self, team_id: str) -> Dict[str, Any]:
        """Get complete workspace hierarchy."""
        return self._request("GET", f"team/{team_id}")

    def get_authorized_workspaces(self) -> Dict[str, Any]:
        """Get all authorized workspaces/teams for the current user."""
        return self._request("GET", "team")

    def get_workspace_seats(self, team_id: str) -> Dict[str, Any]:
        """Get workspace seat information."""
        return self._request("GET", f"team/{team_id}/seats")

    def get_workspace_plan(self, team_id: str) -> Dict[str, Any]:
        """Get workspace plan details."""
        return self._request("GET", f"team/{team_id}/plan")

    def get_shared_hierarchy(self, team_id: str) -> Dict[str, Any]:
        """Get shared hierarchy."""
        return self._request("GET", f"team/{team_id}/shared")

