"""
ListsAPI - High-level API for ClickUp list operations

Provides convenient methods for list operations with automatic formatting support.
"""

from typing import Dict, Any, Optional


class ListsAPI:
    """
    High-level API for ClickUp list operations.

    Wraps ClickUpClient methods with automatic formatting and convenience features.

    Usage:
        from clickup_framework import ClickUpClient
        from clickup_framework.resources import ListsAPI

        client = ClickUpClient()
        lists = ListsAPI(client)

        # Get list
        list_data = lists.get("list_id")

        # Create list
        new_list = lists.create(
            folder_id="folder_id",
            name="My List",
            content="List description"
        )

        # Update list
        lists.update("list_id", name="Updated Name")
    """

    def __init__(self, client):
        """
        Initialize ListsAPI.

        Args:
            client: ClickUpClient instance
        """
        self.client = client

    def get(self, list_id: str) -> Dict[str, Any]:
        """
        Get list by ID.

        Args:
            list_id: List ID

        Returns:
            List data (raw dict)
        """
        return self.client.get_list(list_id)

    def create(
        self,
        folder_id: str,
        name: str,
        content: Optional[str] = None,
        due_date: Optional[int] = None,
        priority: Optional[int] = None,
        status: Optional[str] = None,
        **list_data
    ) -> Dict[str, Any]:
        """
        Create a new list.

        Args:
            folder_id: Folder ID to create list in
            name: List name
            content: List description/content
            due_date: Due date (Unix timestamp in milliseconds)
            priority: Priority (1=urgent, 2=high, 3=normal, 4=low)
            status: Initial status
            **list_data: Additional list fields

        Returns:
            Created list (raw dict)
        """
        data = {**list_data}

        if content:
            data["content"] = content
        if due_date:
            data["due_date"] = due_date
        if priority:
            data["priority"] = priority
        if status:
            data["status"] = status

        return self.client.create_list(folder_id, name, **data)

    def update(self, list_id: str, **updates) -> Dict[str, Any]:
        """
        Update a list.

        Args:
            list_id: List ID
            **updates: Fields to update (name, content, priority, etc.)

        Returns:
            Updated list (raw dict)
        """
        return self.client.update_list(list_id, **updates)

    def get_tasks(
        self,
        list_id: str,
        archived: bool = False,
        include_closed: bool = True,
        **params
    ) -> Dict[str, Any]:
        """
        Get all tasks in a list.

        Args:
            list_id: List ID
            archived: Include archived tasks
            include_closed: Include closed tasks
            **params: Additional query parameters

        Returns:
            Tasks dict with 'tasks' key containing list of tasks
        """
        params_combined = {
            "archived": str(archived).lower(),
            "include_closed": str(include_closed).lower(),
            **params
        }
        return self.client.get_list_tasks(list_id, **params_combined)

    def get_custom_fields(self, list_id: str) -> Dict[str, Any]:
        """
        Get custom fields accessible from this list.

        Args:
            list_id: List ID

        Returns:
            Custom fields data (raw dict)
        """
        return self.client.get_accessible_custom_fields(list_id)
