"""
CustomFieldsAPI - High-level API for ClickUp custom field operations

Provides convenient methods for accessing and managing custom fields.
"""

from typing import Dict, Any


class CustomFieldsAPI:
    """
    High-level API for ClickUp custom field operations.

    Wraps ClickUpClient methods for accessing custom fields at different
    hierarchy levels (list, folder, space, workspace).

    Usage:
        from clickup_framework import ClickUpClient
        from clickup_framework.resources import CustomFieldsAPI

        client = ClickUpClient()
        fields = CustomFieldsAPI(client)

        # Get custom fields at different levels
        list_fields = fields.get_for_list("list_id")
        folder_fields = fields.get_for_folder("folder_id")
        space_fields = fields.get_for_space("space_id")
        workspace_fields = fields.get_for_workspace("team_id")
    """

    def __init__(self, client):
        """
        Initialize CustomFieldsAPI.

        Args:
            client: ClickUpClient instance
        """
        self.client = client

    def get_for_list(self, list_id: str) -> Dict[str, Any]:
        """
        Get custom fields accessible from a list.

        Args:
            list_id: List ID

        Returns:
            Custom fields list (raw dict)

        Example:
            fields = custom_fields.get_for_list("list_id")
            for field in fields.get('fields', []):
                print(f"{field['name']}: {field['type']}")
        """
        return self.client.get_accessible_custom_fields(list_id)

    def get_for_folder(self, folder_id: str) -> Dict[str, Any]:
        """
        Get custom fields accessible from a folder.

        Args:
            folder_id: Folder ID

        Returns:
            Custom fields list (raw dict)
        """
        return self.client.get_folder_custom_fields(folder_id)

    def get_for_space(self, space_id: str) -> Dict[str, Any]:
        """
        Get custom fields accessible from a space.

        Args:
            space_id: Space ID

        Returns:
            Custom fields list (raw dict)
        """
        return self.client.get_space_custom_fields(space_id)

    def get_for_workspace(self, team_id: str) -> Dict[str, Any]:
        """
        Get all custom fields in a workspace.

        Args:
            team_id: Workspace/team ID

        Returns:
            Custom fields list (raw dict)

        Example:
            fields = custom_fields.get_for_workspace("team_id")
            for field in fields.get('fields', []):
                print(f"{field['name']} ({field['type']})")
        """
        return self.client.get_workspace_custom_fields(team_id)
