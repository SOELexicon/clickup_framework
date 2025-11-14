"""
Users API - Low-level API for ClickUp user endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class UsersAPI(BaseAPI):
    """Low-level API for user operations."""

    def invite_user_to_workspace(self, team_id: str, email: str, **user_data) -> Dict[str, Any]:
        """
        Invite user to workspace.

        Args:
            team_id: Workspace/team ID
            email: User email to invite
            **user_data: Additional user data (admin, custom_role_id)

        Returns:
            Invited user object
        """
        data = {"email": email, **user_data}
        return self._request("POST", f"team/{team_id}/user", json=data)

    def get_user(self, team_id: str, user_id: str) -> Dict[str, Any]:
        """Get user information in a workspace."""
        return self._request("GET", f"team/{team_id}/user/{user_id}")

    def edit_user_on_workspace(self, team_id: str, user_id: str, **updates) -> Dict[str, Any]:
        """
        Edit user on workspace.

        Args:
            team_id: Workspace/team ID
            user_id: User ID
            **updates: Fields to update (username, admin, custom_role_id)

        Returns:
            Updated user object
        """
        return self._request("PUT", f"team/{team_id}/user/{user_id}", json=updates)

    def remove_user_from_workspace(self, team_id: str, user_id: str) -> Dict[str, Any]:
        """Remove user from workspace."""
        return self._request("DELETE", f"team/{team_id}/user/{user_id}")

