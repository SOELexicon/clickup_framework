"""
UsersAPI - High-level API for ClickUp user management operations

Provides convenient methods for managing users within workspaces.
"""

from typing import Dict, Any, Optional


class UsersAPI:
    """
    High-level API for ClickUp user management operations.

    Wraps ClickUpClient methods for inviting, updating, and managing
    users within workspaces.

    Usage:
        from clickup_framework import ClickUpClient
        from clickup_framework.resources import UsersAPI

        client = ClickUpClient()
        users = UsersAPI(client)

        # Invite a user
        user = users.invite("team_id", "user@example.com", admin=False)

        # Get user info
        user_info = users.get("team_id", "user_id")

        # Update user permissions
        users.update("team_id", "user_id", admin=True)
    """

    def __init__(self, client):
        """
        Initialize UsersAPI.

        Args:
            client: ClickUpClient instance
        """
        self.client = client

    def invite(self, team_id: str, email: str, admin: bool = False, **user_data) -> Dict[str, Any]:
        """
        Invite a user to workspace.

        Args:
            team_id: Workspace/team ID
            email: User email to invite
            admin: Grant admin privileges (default: False)
            **user_data: Additional user data (custom_role_id, etc.)

        Returns:
            Invited user object (raw dict)

        Example:
            # Invite as regular member
            user = users.invite("team_id", "user@example.com")

            # Invite as admin
            admin_user = users.invite(
                team_id="team_id",
                email="admin@example.com",
                admin=True
            )
        """
        return self.client.invite_user_to_workspace(team_id, email, admin=admin, **user_data)

    def get(self, team_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get user information in a workspace.

        Args:
            team_id: Workspace/team ID
            user_id: User ID

        Returns:
            User object (raw dict)

        Example:
            user = users.get("team_id", "user_id")
            print(f"User: {user['user']['username']} ({user['user']['email']})")
        """
        return self.client.get_user(team_id, user_id)

    def update(
        self,
        team_id: str,
        user_id: str,
        username: Optional[str] = None,
        admin: Optional[bool] = None,
        custom_role_id: Optional[int] = None,
        **updates
    ) -> Dict[str, Any]:
        """
        Edit user on workspace.

        Args:
            team_id: Workspace/team ID
            user_id: User ID
            username: New username
            admin: Admin status
            custom_role_id: Custom role ID
            **updates: Additional fields to update

        Returns:
            Updated user object (raw dict)

        Example:
            # Make user an admin
            users.update("team_id", "user_id", admin=True)

            # Change username
            users.update("team_id", "user_id", username="new_name")

            # Assign custom role
            users.update("team_id", "user_id", custom_role_id=123)
        """
        data = {**updates}

        if username is not None:
            data["username"] = username
        if admin is not None:
            data["admin"] = admin
        if custom_role_id is not None:
            data["custom_role_id"] = custom_role_id

        return self.client.edit_user_on_workspace(team_id, user_id, **data)

    def remove(self, team_id: str, user_id: str) -> Dict[str, Any]:
        """
        Remove user from workspace.

        Args:
            team_id: Workspace/team ID
            user_id: User ID

        Returns:
            Empty dict on success

        Example:
            users.remove("team_id", "user_id")
        """
        return self.client.remove_user_from_workspace(team_id, user_id)
