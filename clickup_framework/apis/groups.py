"""
Groups API - Low-level API for ClickUp user group endpoints.
"""

from typing import Dict, Any, Optional, List
from .base import BaseAPI


class GroupsAPI(BaseAPI):
    """Low-level API for user group operations."""

    def create_user_group(self, team_id: str, name: str, member_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Create a user group in a workspace.

        Args:
            team_id: Workspace/team ID
            name: Group name
            member_ids: List of user IDs to add to the group

        Returns:
            Created group object
        """
        data = {"name": name}
        if member_ids:
            data["members"] = member_ids
        return self._request("POST", f"team/{team_id}/group", json=data)

    def update_user_group(self, group_id: str, **updates) -> Dict[str, Any]:
        """
        Update a user group.

        Args:
            group_id: Group ID
            **updates: Fields to update (name, members, etc.)

        Returns:
            Updated group object
        """
        return self._request("PUT", f"group/{group_id}", json=updates)

    def delete_user_group(self, group_id: str) -> Dict[str, Any]:
        """Delete a user group."""
        return self._request("DELETE", f"group/{group_id}")

    def get_user_groups(self, **params) -> Dict[str, Any]:
        """
        Get user groups.

        Args:
            **params: Query parameters (team_id, group_ids)

        Returns:
            Groups list
        """
        return self._request("GET", "group", params=params)

