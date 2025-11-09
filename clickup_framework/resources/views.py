"""
ViewsAPI - High-level API for ClickUp view operations

Provides convenient methods for managing views across all hierarchy levels.
"""

from typing import Dict, Any, Optional


class ViewsAPI:
    """
    High-level API for ClickUp view operations.

    Wraps ClickUpClient methods for creating, updating, and managing views
    at workspace, space, folder, and list levels.

    Usage:
        from clickup_framework import ClickUpClient
        from clickup_framework.resources import ViewsAPI

        client = ClickUpClient()
        views = ViewsAPI(client)

        # Create a view at different levels
        workspace_view = views.create_for_workspace("team_id", "All Tasks", "list")
        space_view = views.create_for_space("space_id", "Sprint Board", "board")
        list_view = views.create_for_list("list_id", "Calendar", "calendar")

        # Get and update views
        view = views.get("view_id")
        views.update(view['view']['id'], name="Updated Name")
    """

    def __init__(self, client):
        """
        Initialize ViewsAPI.

        Args:
            client: ClickUpClient instance
        """
        self.client = client

    # Workspace-level views (Everything level)
    def get_for_workspace(self, team_id: str) -> Dict[str, Any]:
        """
        Get Everything level views for a workspace.

        Args:
            team_id: Workspace/team ID

        Returns:
            Views list (raw dict)
        """
        return self.client.get_workspace_views(team_id)

    def create_for_workspace(self, team_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """
        Create Everything level view for a workspace.

        Args:
            team_id: Workspace/team ID
            name: View name
            type: View type (list, board, calendar, gantt, table, timeline, workload, activity, map, etc.)
            **view_data: Additional view configuration

        Returns:
            Created view object (raw dict)

        Example:
            view = views.create_for_workspace(
                team_id="team_id",
                name="Everything View",
                type="list"
            )
        """
        return self.client.create_workspace_view(team_id, name, type, **view_data)

    # Space-level views
    def get_for_space(self, space_id: str) -> Dict[str, Any]:
        """
        Get views for a space.

        Args:
            space_id: Space ID

        Returns:
            Views list (raw dict)
        """
        return self.client.get_space_views(space_id)

    def create_for_space(self, space_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """
        Create view for a space.

        Args:
            space_id: Space ID
            name: View name
            type: View type (list, board, calendar, etc.)
            **view_data: Additional view configuration

        Returns:
            Created view object (raw dict)
        """
        return self.client.create_space_view(space_id, name, type, **view_data)

    # Folder-level views
    def get_for_folder(self, folder_id: str) -> Dict[str, Any]:
        """
        Get views for a folder.

        Args:
            folder_id: Folder ID

        Returns:
            Views list (raw dict)
        """
        return self.client.get_folder_views(folder_id)

    def create_for_folder(self, folder_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """
        Create view for a folder.

        Args:
            folder_id: Folder ID
            name: View name
            type: View type (list, board, calendar, etc.)
            **view_data: Additional view configuration

        Returns:
            Created view object (raw dict)
        """
        return self.client.create_folder_view(folder_id, name, type, **view_data)

    # List-level views
    def get_for_list(self, list_id: str) -> Dict[str, Any]:
        """
        Get views for a list.

        Args:
            list_id: List ID

        Returns:
            Views list (raw dict)
        """
        return self.client.get_list_views(list_id)

    def create_for_list(self, list_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """
        Create view for a list.

        Args:
            list_id: List ID
            name: View name
            type: View type (list, board, calendar, etc.)
            **view_data: Additional view configuration

        Returns:
            Created view object (raw dict)

        Example:
            view = views.create_for_list(
                list_id="list_id",
                name="Sprint Calendar",
                type="calendar"
            )
        """
        return self.client.create_list_view(list_id, name, type, **view_data)

    # Individual view operations
    def get(self, view_id: str) -> Dict[str, Any]:
        """
        Get view by ID.

        Args:
            view_id: View ID

        Returns:
            View object (raw dict)
        """
        return self.client.get_view(view_id)

    def update(self, view_id: str, name: Optional[str] = None, **updates) -> Dict[str, Any]:
        """
        Update a view.

        Args:
            view_id: View ID
            name: New view name
            **updates: Additional fields to update

        Returns:
            Updated view object (raw dict)

        Example:
            views.update("view_id", name="Updated View Name")
        """
        data = {**updates}

        if name is not None:
            data["name"] = name

        return self.client.update_view(view_id, **data)

    def delete(self, view_id: str) -> Dict[str, Any]:
        """
        Delete a view.

        Args:
            view_id: View ID

        Returns:
            Empty dict on success

        Example:
            views.delete("view_id")
        """
        return self.client.delete_view(view_id)

    def get_tasks(self, view_id: str, **params) -> Dict[str, Any]:
        """
        Get tasks from a view.

        Args:
            view_id: View ID
            **params: Query parameters (page, order_by, etc.)

        Returns:
            Tasks from the view (raw dict)

        Example:
            tasks = views.get_tasks("view_id", page=0)
            for task in tasks.get('tasks', []):
                print(task['name'])
        """
        return self.client.get_view_tasks(view_id, **params)
