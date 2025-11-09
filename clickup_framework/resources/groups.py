"""
GroupsAPI - High-level API for ClickUp user group operations

Provides convenient methods for managing user groups within workspaces.
"""

from typing import Dict, Any, Optional, List


class GroupsAPI:
    """
    High-level API for ClickUp user group operations.

    Wraps ClickUpClient methods for creating, updating, and managing
    user groups within workspaces.

    Usage:
        from clickup_framework import ClickUpClient
        from clickup_framework.resources import GroupsAPI

        client = ClickUpClient()
        groups = GroupsAPI(client)

        # Create a group
        group = groups.create("team_id", "Developers", member_ids=[123, 456])

        # Update a group
        groups.update(group['group']['id'], name="Senior Developers")

        # Delete a group
        groups.delete(group['group']['id'])
    """

    def __init__(self, client):
        """
        Initialize GroupsAPI.

        Args:
            client: ClickUpClient instance
        """
        self.client = client

    def create(self, team_id: str, name: str, member_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Create a user group in a workspace.

        Args:
            team_id: Workspace/team ID
            name: Group name
            member_ids: List of user IDs to add to the group

        Returns:
            Created group object (raw dict)

        Example:
            group = groups.create(
                team_id="123",
                name="Design Team",
                member_ids=[456, 789]
            )
            print(f"Created group: {group['group']['name']}")
        """
        return self.client.create_user_group(team_id, name, member_ids)

    def update(self, group_id: str, name: Optional[str] = None, members: Optional[Dict] = None, **updates) -> Dict[str, Any]:
        """
        Update a user group.

        Args:
            group_id: Group ID
            name: New group name
            members: Members to add/remove (e.g., {"add": [123], "rem": [456]})
            **updates: Additional fields to update

        Returns:
            Updated group object (raw dict)

        Example:
            # Rename group
            groups.update(group_id="group_id", name="Senior Design Team")

            # Add/remove members
            groups.update(
                group_id="group_id",
                members={"add": [111], "rem": [222]}
            )
        """
        data = {**updates}

        if name is not None:
            data["name"] = name
        if members is not None:
            data["members"] = members

        return self.client.update_user_group(group_id, **data)

    def delete(self, group_id: str) -> Dict[str, Any]:
        """
        Delete a user group.

        Args:
            group_id: Group ID

        Returns:
            Empty dict on success

        Example:
            groups.delete("group_id")
        """
        return self.client.delete_user_group(group_id)

    def get(self, team_id: Optional[str] = None, group_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get user groups.

        Args:
            team_id: Filter by workspace/team ID
            group_ids: Filter by specific group IDs

        Returns:
            Groups list (raw dict)

        Example:
            # Get all groups in workspace
            all_groups = groups.get(team_id="team_id")

            # Get specific groups
            specific = groups.get(group_ids=["group1", "group2"])
        """
        params = {}
        if team_id:
            params["team_id"] = team_id
        if group_ids:
            params["group_ids"] = group_ids

        return self.client.get_user_groups(**params)
