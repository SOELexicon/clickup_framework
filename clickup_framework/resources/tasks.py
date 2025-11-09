"""
TasksAPI - High-level API for ClickUp task operations

Provides convenient methods for task operations with automatic formatting support.
"""

from typing import Dict, Any, Optional, List
from ..formatters import format_task, format_task_list


class TasksAPI:
    """
    High-level API for ClickUp task operations.

    Wraps ClickUpClient methods with automatic formatting and convenience features.

    Usage:
        from clickup_framework import ClickUpClient
        from clickup_framework.resources import TasksAPI

        client = ClickUpClient()
        tasks = TasksAPI(client)

        # Get formatted task
        task_summary = tasks.get("task_id", detail_level="summary")

        # Get raw task
        task_raw = tasks.get("task_id")

        # Update task status
        tasks.update_status("task_id", "in progress")
    """

    def __init__(self, client):
        """
        Initialize TasksAPI.

        Args:
            client: ClickUpClient instance
        """
        self.client = client

    def get(self, task_id: str, detail_level: Optional[str] = None, **params) -> Any:
        """
        Get task by ID.

        Args:
            task_id: Task ID
            detail_level: Format detail level (minimal|summary|detailed|full)
                         If None, returns raw JSON
            **params: Additional query parameters

        Returns:
            Formatted string if detail_level specified, otherwise raw dict
        """
        task = self.client.get_task(task_id, **params)

        if detail_level:
            return format_task(task, detail_level)
        return task

    def get_list_tasks(
        self,
        list_id: str,
        detail_level: Optional[str] = None,
        **params
    ) -> Any:
        """
        Get all tasks in a list.

        Args:
            list_id: List ID
            detail_level: Format detail level (minimal|summary|detailed|full)
                         If None, returns raw JSON
            **params: Additional query parameters (archived, page, order_by, etc.)

        Returns:
            Formatted string if detail_level specified, otherwise raw dict
        """
        result = self.client.get_list_tasks(list_id, **params)

        if detail_level and 'tasks' in result:
            return format_task_list(result['tasks'], detail_level)
        return result

    def get_team_tasks(
        self,
        team_id: str,
        detail_level: Optional[str] = None,
        **params
    ) -> Any:
        """
        Get all tasks in a team/workspace.

        Args:
            team_id: Team/workspace ID
            detail_level: Format detail level (minimal|summary|detailed|full)
                         If None, returns raw JSON
            **params: Additional query parameters (page, order_by, reverse, etc.)

        Returns:
            Formatted string if detail_level specified, otherwise raw dict
        """
        result = self.client.get_team_tasks(team_id, **params)

        if detail_level and 'tasks' in result:
            return format_task_list(result['tasks'], detail_level)
        return result

    def create(
        self,
        list_id: str,
        name: str,
        description: Optional[str] = None,
        assignees: Optional[List[int]] = None,
        priority: Optional[int] = None,
        status: Optional[str] = None,
        **task_data
    ) -> Dict[str, Any]:
        """
        Create a new task.

        Args:
            list_id: List ID to create task in
            name: Task name
            description: Task description
            assignees: List of user IDs to assign
            priority: Priority (1=urgent, 2=high, 3=normal, 4=low)
            status: Initial status
            **task_data: Additional task fields

        Returns:
            Created task (raw dict)
        """
        data = {"name": name, **task_data}

        if description:
            data["description"] = description
        if assignees:
            data["assignees"] = assignees
        if priority:
            data["priority"] = priority
        if status:
            data["status"] = status

        return self.client.create_task(list_id, **data)

    def update(self, task_id: str, **updates) -> Dict[str, Any]:
        """
        Update a task.

        Args:
            task_id: Task ID
            **updates: Fields to update (name, description, status, priority, etc.)

        Returns:
            Updated task (raw dict)
        """
        return self.client.update_task(task_id, **updates)

    def update_status(self, task_id: str, status: str) -> Dict[str, Any]:
        """
        Update task status (convenience method).

        Args:
            task_id: Task ID
            status: New status

        Returns:
            Updated task (raw dict)
        """
        return self.update(task_id, status=status)

    def update_priority(self, task_id: str, priority: int) -> Dict[str, Any]:
        """
        Update task priority (convenience method).

        Args:
            task_id: Task ID
            priority: Priority (1=urgent, 2=high, 3=normal, 4=low)

        Returns:
            Updated task (raw dict)
        """
        return self.update(task_id, priority=priority)

    def assign(self, task_id: str, user_ids: List[int]) -> Dict[str, Any]:
        """
        Assign task to users (convenience method).

        Args:
            task_id: Task ID
            user_ids: List of user IDs to assign

        Returns:
            Updated task (raw dict)
        """
        return self.update(task_id, assignees={"add": user_ids})

    def unassign(self, task_id: str, user_ids: List[int]) -> Dict[str, Any]:
        """
        Unassign task from users (convenience method).

        Args:
            task_id: Task ID
            user_ids: List of user IDs to unassign

        Returns:
            Updated task (raw dict)
        """
        return self.update(task_id, assignees={"rem": user_ids})

    def delete(self, task_id: str) -> Dict[str, Any]:
        """
        Delete a task.

        Args:
            task_id: Task ID

        Returns:
            Empty dict on success
        """
        return self.client.delete_task(task_id)

    # Comment operations
    def add_comment(self, task_id: str, comment_text: str) -> Dict[str, Any]:
        """
        Add comment to task.

        Args:
            task_id: Task ID
            comment_text: Comment text (plain text only, no markdown)

        Returns:
            Created comment (raw dict)
        """
        return self.client.create_task_comment(task_id, comment_text)

    def get_comments(
        self,
        task_id: str,
        detail_level: Optional[str] = None
    ) -> Any:
        """
        Get task comments.

        Args:
            task_id: Task ID
            detail_level: Format detail level (minimal|summary|detailed|full)
                         If None, returns raw JSON

        Returns:
            Formatted string if detail_level specified, otherwise raw dict
        """
        from ..formatters import format_comment_list

        result = self.client.get_task_comments(task_id)

        if detail_level and 'comments' in result:
            return format_comment_list(result['comments'], detail_level)
        return result

    # Checklist operations
    def add_checklist(self, task_id: str, name: str) -> Dict[str, Any]:
        """
        Add checklist to task.

        Args:
            task_id: Task ID
            name: Checklist name

        Returns:
            Created checklist (raw dict)
        """
        return self.client.create_checklist(task_id, name)

    def add_checklist_item(
        self,
        checklist_id: str,
        name: str,
        assignee: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add item to checklist.

        Args:
            checklist_id: Checklist ID
            name: Item name
            assignee: User ID to assign (optional)

        Returns:
            Created checklist item (raw dict)
        """
        data = {"name": name}
        if assignee:
            data["assignee"] = assignee

        return self.client.create_checklist_item(checklist_id, name, **data)

    # Custom field operations
    def set_custom_field(
        self,
        task_id: str,
        field_id: str,
        value: Any
    ) -> Dict[str, Any]:
        """
        Set custom field value.

        Args:
            task_id: Task ID
            field_id: Custom field ID
            value: Field value

        Returns:
            Updated task (raw dict)
        """
        return self.client.set_custom_field_value(task_id, field_id, value)

    def remove_custom_field(self, task_id: str, field_id: str) -> Dict[str, Any]:
        """
        Remove custom field value.

        Args:
            task_id: Task ID
            field_id: Custom field ID

        Returns:
            Updated task (raw dict)
        """
        return self.client.remove_custom_field_value(task_id, field_id)
