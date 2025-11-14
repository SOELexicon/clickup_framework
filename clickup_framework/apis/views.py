"""
Views API - Low-level API for ClickUp view endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class ViewsAPI(BaseAPI):
    """Low-level API for view operations."""

    def get_workspace_views(self, team_id: str) -> Dict[str, Any]:
        """Get Everything level views for a workspace."""
        return self._request("GET", f"team/{team_id}/view")

    def create_workspace_view(self, team_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """
        Create Everything level view for a workspace.

        Args:
            team_id: Workspace/team ID
            name: View name
            type: View type (list, board, calendar, etc.)
            **view_data: Additional view configuration

        Returns:
            Created view object
        """
        data = {"name": name, "type": type, **view_data}
        return self._request("POST", f"team/{team_id}/view", json=data)

    def get_space_views(self, space_id: str) -> Dict[str, Any]:
        """Get views for a space."""
        return self._request("GET", f"space/{space_id}/view")

    def create_space_view(self, space_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """
        Create view for a space.

        Args:
            space_id: Space ID
            name: View name
            type: View type (list, board, calendar, etc.)
            **view_data: Additional view configuration

        Returns:
            Created view object
        """
        data = {"name": name, "type": type, **view_data}
        return self._request("POST", f"space/{space_id}/view", json=data)

    def get_folder_views(self, folder_id: str) -> Dict[str, Any]:
        """Get views for a folder."""
        return self._request("GET", f"folder/{folder_id}/view")

    def create_folder_view(self, folder_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """
        Create view for a folder.

        Args:
            folder_id: Folder ID
            name: View name
            type: View type (list, board, calendar, etc.)
            **view_data: Additional view configuration

        Returns:
            Created view object
        """
        data = {"name": name, "type": type, **view_data}
        return self._request("POST", f"folder/{folder_id}/view", json=data)

    def get_list_views(self, list_id: str) -> Dict[str, Any]:
        """Get views for a list."""
        return self._request("GET", f"list/{list_id}/view")

    def create_list_view(self, list_id: str, name: str, type: str, **view_data) -> Dict[str, Any]:
        """
        Create view for a list.

        Args:
            list_id: List ID
            name: View name
            type: View type (list, board, calendar, etc.)
            **view_data: Additional view configuration

        Returns:
            Created view object
        """
        data = {"name": name, "type": type, **view_data}
        return self._request("POST", f"list/{list_id}/view", json=data)

    def get_view(self, view_id: str) -> Dict[str, Any]:
        """Get view by ID."""
        return self._request("GET", f"view/{view_id}")

    def update_view(self, view_id: str, **updates) -> Dict[str, Any]:
        """Update a view."""
        return self._request("PUT", f"view/{view_id}", json=updates)

    def delete_view(self, view_id: str) -> Dict[str, Any]:
        """Delete a view."""
        return self._request("DELETE", f"view/{view_id}")

    def get_view_tasks(self, view_id: str, **params) -> Dict[str, Any]:
        """
        Get tasks from a view.

        Args:
            view_id: View ID
            **params: Query parameters (page, order_by, etc.)

        Returns:
            Tasks from the view
        """
        return self._request("GET", f"view/{view_id}/task", params=params)

