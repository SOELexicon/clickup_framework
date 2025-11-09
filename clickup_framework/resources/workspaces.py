"""
WorkspacesAPI - High-level API for ClickUp workspace operations

Provides convenient methods for workspace, space, and folder operations.
"""

from typing import Dict, Any, Optional, List


class WorkspacesAPI:
    """
    High-level API for ClickUp workspace, space, and folder operations.

    Wraps ClickUpClient methods with automatic formatting and convenience features.

    Usage:
        from clickup_framework import ClickUpClient
        from clickup_framework.resources import WorkspacesAPI

        client = ClickUpClient()
        workspaces = WorkspacesAPI(client)

        # Get workspace hierarchy
        hierarchy = workspaces.get_hierarchy(team_id="90151898946")

        # Get all spaces
        spaces = workspaces.get_spaces(team_id="90151898946")

        # Create space
        new_space = workspaces.create_space(
            team_id="90151898946",
            name="My Space"
        )

        # Create folder
        folder = workspaces.create_folder(
            space_id="space_id",
            name="My Folder"
        )
    """

    def __init__(self, client):
        """
        Initialize WorkspacesAPI.

        Args:
            client: ClickUpClient instance
        """
        self.client = client

    # Workspace operations
    def get_hierarchy(self, team_id: str) -> Dict[str, Any]:
        """
        Get complete workspace hierarchy.

        Returns all spaces, folders, and lists in the workspace.

        Args:
            team_id: Team/workspace ID

        Returns:
            Complete workspace hierarchy (raw dict)
        """
        return self.client.get_workspace_hierarchy(team_id)

    # Space operations
    def get_space(self, space_id: str) -> Dict[str, Any]:
        """
        Get space by ID.

        Args:
            space_id: Space ID

        Returns:
            Space data (raw dict)
        """
        return self.client.get_space(space_id)

    def get_spaces(
        self,
        team_id: str,
        archived: bool = False
    ) -> Dict[str, Any]:
        """
        Get all spaces in a workspace.

        Args:
            team_id: Team/workspace ID
            archived: Include archived spaces

        Returns:
            Spaces data (raw dict)
        """
        return self.client.get_team_spaces(team_id, archived=archived)

    def create_space(
        self,
        team_id: str,
        name: str,
        multiple_assignees: bool = True,
        features: Optional[Dict[str, Any]] = None,
        **space_data
    ) -> Dict[str, Any]:
        """
        Create a new space.

        Args:
            team_id: Team/workspace ID
            name: Space name
            multiple_assignees: Allow multiple assignees per task
            features: Space features configuration
            **space_data: Additional space fields

        Returns:
            Created space (raw dict)
        """
        data = {
            "multiple_assignees": multiple_assignees,
            **space_data
        }

        if features:
            data["features"] = features

        return self.client.create_space(team_id, name, **data)

    def update_space(self, space_id: str, **updates) -> Dict[str, Any]:
        """
        Update a space.

        Args:
            space_id: Space ID
            **updates: Fields to update

        Returns:
            Updated space (raw dict)
        """
        return self.client.update_space(space_id, **updates)

    def delete_space(self, space_id: str) -> Dict[str, Any]:
        """
        Delete a space.

        Args:
            space_id: Space ID

        Returns:
            Empty dict on success
        """
        return self.client.delete_space(space_id)

    # Tag operations
    def get_tags(self, space_id: str) -> Dict[str, Any]:
        """
        Get all tags in a space.

        Args:
            space_id: Space ID

        Returns:
            Tags data (raw dict)
        """
        return self.client.get_space_tags(space_id)

    def create_tag(
        self,
        space_id: str,
        name: str,
        fg_color: str = "#000000",
        bg_color: str = "#FFFFFF"
    ) -> Dict[str, Any]:
        """
        Create a tag in a space.

        Args:
            space_id: Space ID
            name: Tag name
            fg_color: Foreground/text color (hex)
            bg_color: Background color (hex)

        Returns:
            Created tag (raw dict)
        """
        return self.client.create_space_tag(space_id, name, fg_color, bg_color)

    # Folder operations
    def get_folder(self, folder_id: str) -> Dict[str, Any]:
        """
        Get folder by ID.

        Args:
            folder_id: Folder ID

        Returns:
            Folder data (raw dict)
        """
        return self.client.get_folder(folder_id)

    def create_folder(self, space_id: str, name: str) -> Dict[str, Any]:
        """
        Create a new folder.

        Args:
            space_id: Space ID to create folder in
            name: Folder name

        Returns:
            Created folder (raw dict)
        """
        return self.client.create_folder(space_id, name)

    def update_folder(self, folder_id: str, **updates) -> Dict[str, Any]:
        """
        Update a folder.

        Args:
            folder_id: Folder ID
            **updates: Fields to update

        Returns:
            Updated folder (raw dict)
        """
        return self.client.update_folder(folder_id, **updates)

    # Search operations
    def search(
        self,
        team_id: str,
        query: str,
        **filters
    ) -> Dict[str, Any]:
        """
        Search across the workspace.

        Args:
            team_id: Team/workspace ID
            query: Search query
            **filters: Additional filters (space_ids, list_ids, etc.)

        Returns:
            Search results (raw dict)
        """
        return self.client.search(team_id, query, **filters)

    # Workspace info and management
    def get_all_authorized(self) -> Dict[str, Any]:
        """
        Get all authorized workspaces/teams for the current user.

        Returns:
            Workspaces list (raw dict)

        Example:
            workspaces_list = workspaces.get_all_authorized()
            for workspace in workspaces_list.get('teams', []):
                print(f"{workspace['name']} (ID: {workspace['id']})")
        """
        return self.client.get_authorized_workspaces()

    def get_seats(self, team_id: str) -> Dict[str, Any]:
        """
        Get workspace seat information.

        Args:
            team_id: Team/workspace ID

        Returns:
            Seat information (raw dict)

        Example:
            seats = workspaces.get_seats("team_id")
            print(f"Seats: {seats['seats']['total']} total, {seats['seats']['used']} used")
        """
        return self.client.get_workspace_seats(team_id)

    def get_plan(self, team_id: str) -> Dict[str, Any]:
        """
        Get workspace plan details.

        Args:
            team_id: Team/workspace ID

        Returns:
            Plan information (raw dict)

        Example:
            plan = workspaces.get_plan("team_id")
            print(f"Plan: {plan['plan']['name']}")
        """
        return self.client.get_workspace_plan(team_id)

    # Custom Task Types
    def get_custom_task_types(self, team_id: str) -> Dict[str, Any]:
        """
        Get custom task types for a workspace.

        Args:
            team_id: Team/workspace ID

        Returns:
            Custom task types list (raw dict)

        Example:
            types = workspaces.get_custom_task_types("team_id")
            for task_type in types.get('custom_items', []):
                print(f"{task_type['name']}: {task_type['id']}")
        """
        return self.client.get_custom_task_types(team_id)
