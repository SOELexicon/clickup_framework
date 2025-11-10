"""
TasksAPI - High-level API for ClickUp task operations

Provides convenient methods for task operations with automatic formatting support.
"""

from typing import Dict, Any, Optional, List
from difflib import SequenceMatcher
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

    def __init__(self, client, duplicate_threshold: float = 0.95):
        """
        Initialize TasksAPI.

        Args:
            client: ClickUpClient instance
            duplicate_threshold: Similarity threshold for duplicate detection (0.0-1.0)
                                Default is 0.95 (95% similar)
        """
        self.client = client
        self.duplicate_threshold = duplicate_threshold

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using SequenceMatcher.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def _check_duplicate_task(
        self,
        list_id: str,
        name: str,
        description: Optional[str] = None,
        parent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a similar task already exists in the list.

        Args:
            list_id: List ID to search in
            name: Task name to check
            description: Task description to check (optional)
            parent: Parent task ID (optional)

        Returns:
            Matching task dict if found, None otherwise
        """
        # Get all tasks in the list
        result = self.client.get_list_tasks(list_id, include_closed=False)
        existing_tasks = result.get('tasks', [])

        # Check each task for similarity
        for task in existing_tasks:
            # Check if parent matches (if specified)
            if parent is not None:
                task_parent = task.get('parent')
                if task_parent != parent:
                    continue

            # Check name similarity
            task_name = task.get('name', '')
            name_similarity = self._calculate_similarity(name, task_name)

            if name_similarity >= self.duplicate_threshold:
                # If description provided, check description similarity too
                if description:
                    task_description = task.get('description', '')
                    desc_similarity = self._calculate_similarity(description, task_description)

                    # Both name and description must be similar
                    if desc_similarity >= self.duplicate_threshold:
                        return task
                else:
                    # Only name needs to match if no description provided
                    return task

        return None

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
        skip_duplicate_check: bool = False,
        **task_data
    ) -> Dict[str, Any]:
        """
        Create a new task with automatic duplicate detection.

        Before creating, checks for existing tasks with similar name and description
        to prevent accidental duplicates.

        Args:
            list_id: List ID to create task in
            name: Task name
            description: Task description
            assignees: List of user IDs to assign
            priority: Priority (1=urgent, 2=high, 3=normal, 4=low)
            status: Initial status
            skip_duplicate_check: Skip duplicate detection (default: False)
            **task_data: Additional task fields (including 'parent' for subtasks)

        Returns:
            Created task (raw dict)

        Raises:
            ValueError: If a similar task already exists
        """
        # Check for duplicates unless explicitly skipped
        if not skip_duplicate_check:
            parent_id = task_data.get('parent')
            duplicate = self._check_duplicate_task(
                list_id=list_id,
                name=name,
                description=description,
                parent=parent_id
            )

            if duplicate:
                task_id = duplicate.get('id')
                task_name = duplicate.get('name')
                raise ValueError(
                    f"Task already exists with similar name, description, and parent. "
                    f"Please review existing task [{task_id}]: \"{task_name}\". "
                    f"Use skip_duplicate_check=True to force creation."
                )

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

    def update(self, task: Dict[str, Any], **updates) -> Dict[str, Any]:
        """
        Update a task (requires task to be viewed/fetched first).

        This method requires the task object (fetched via get() or get_task())
        to ensure you're aware of the current state before making modifications.

        Args:
            task: Task object (dict) fetched via get() or client.get_task()
            **updates: Fields to update (name, description, status, priority, etc.)

        Returns:
            Updated task (raw dict)

        Raises:
            ValueError: If task is not a valid task object

        Example:
            # Correct usage - view task first
            task = tasks.get("task_id")
            updated = tasks.update(task, status="in progress")

            # Incorrect usage - will raise ValueError
            tasks.update("task_id", status="done")  # ❌ Wrong!
        """
        # Validate that task is a dict with an 'id' field
        if not isinstance(task, dict) or 'id' not in task:
            raise ValueError(
                "Task must be viewed/fetched before updating. "
                "Use tasks.get(task_id) to fetch the task first, then pass the task object to update()."
            )

        task_id = task['id']
        return self.client.update_task(task_id, **updates)

    def update_status(self, task: Dict[str, Any], status: str) -> Dict[str, Any]:
        """
        Update task status (convenience method, requires task to be viewed first).

        Args:
            task: Task object (dict) fetched via get() or client.get_task()
            status: New status

        Returns:
            Updated task (raw dict)

        Example:
            task = tasks.get("task_id")
            tasks.update_status(task, "in progress")
        """
        return self.update(task, status=status)

    def update_priority(self, task: Dict[str, Any], priority: int) -> Dict[str, Any]:
        """
        Update task priority (convenience method, requires task to be viewed first).

        Args:
            task: Task object (dict) fetched via get() or client.get_task()
            priority: Priority (1=urgent, 2=high, 3=normal, 4=low)

        Returns:
            Updated task (raw dict)

        Example:
            task = tasks.get("task_id")
            tasks.update_priority(task, 1)
        """
        return self.update(task, priority=priority)

    def assign(self, task: Dict[str, Any], user_ids: List[int]) -> Dict[str, Any]:
        """
        Assign task to users (convenience method, requires task to be viewed first).

        Args:
            task: Task object (dict) fetched via get() or client.get_task()
            user_ids: List of user IDs to assign

        Returns:
            Updated task (raw dict)

        Example:
            task = tasks.get("task_id")
            tasks.assign(task, [123456])
        """
        return self.update(task, assignees={"add": user_ids})

    def unassign(self, task: Dict[str, Any], user_ids: List[int]) -> Dict[str, Any]:
        """
        Unassign task from users (convenience method, requires task to be viewed first).

        Args:
            task: Task object (dict) fetched via get() or client.get_task()
            user_ids: List of user IDs to unassign

        Returns:
            Updated task (raw dict)

        Example:
            task = tasks.get("task_id")
            tasks.unassign(task, [123456])
        """
        return self.update(task, assignees={"rem": user_ids})

    def delete(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete a task (requires task to be viewed/fetched first).

        This method requires the task object (fetched via get() or get_task())
        to ensure you're aware of what you're deleting.

        Args:
            task: Task object (dict) fetched via get() or client.get_task()

        Returns:
            Empty dict on success

        Raises:
            ValueError: If task is not a valid task object

        Example:
            # Correct usage - view task first
            task = tasks.get("task_id")
            tasks.delete(task)

            # Incorrect usage - will raise ValueError
            tasks.delete("task_id")  # ❌ Wrong!
        """
        # Validate that task is a dict with an 'id' field
        if not isinstance(task, dict) or 'id' not in task:
            raise ValueError(
                "Task must be viewed/fetched before deleting. "
                "Use tasks.get(task_id) to fetch the task first, then pass the task object to delete()."
            )

        task_id = task['id']
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
        data = {}
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

    # Task Relationship operations - Dependencies
    def add_dependency_waiting_on(
        self,
        task_id: str,
        depends_on_task_id: str,
        **params
    ) -> Dict[str, Any]:
        """
        Make this task wait on another task (dependency relationship).

        This creates a "waiting on" relationship where task_id cannot be completed
        until depends_on_task_id is completed.

        Args:
            task_id: The task that will wait
            depends_on_task_id: The task that must be completed first
            **params: Additional query parameters (custom_task_ids, team_id)

        Returns:
            Empty dict on success

        Example:
            # Task B waits for Task A to be completed first
            tasks.add_dependency_waiting_on("task_b_id", "task_a_id")
        """
        return self.client.add_task_dependency(
            task_id,
            depends_on=depends_on_task_id,
            **params
        )

    def add_dependency_blocking(
        self,
        task_id: str,
        blocked_task_id: str,
        **params
    ) -> Dict[str, Any]:
        """
        Make this task block another task (dependency relationship).

        This creates a "blocking" relationship where blocked_task_id cannot be
        completed until task_id is completed.

        Args:
            task_id: The task that blocks
            blocked_task_id: The task that is blocked
            **params: Additional query parameters (custom_task_ids, team_id)

        Returns:
            Empty dict on success

        Example:
            # Task A blocks Task B from being completed
            tasks.add_dependency_blocking("task_a_id", "task_b_id")
        """
        return self.client.add_task_dependency(
            task_id,
            dependency_of=blocked_task_id,
            **params
        )

    def remove_dependency(
        self,
        task_id: str,
        depends_on: Optional[str] = None,
        dependency_of: Optional[str] = None,
        **params
    ) -> Dict[str, Any]:
        """
        Remove a dependency relationship.

        Args:
            task_id: Task ID
            depends_on: Task ID to remove from "waiting on" list
            dependency_of: Task ID to remove from "blocking" list
            **params: Additional query parameters (custom_task_ids, team_id)

        Returns:
            Empty dict on success

        Note:
            Provide either depends_on or dependency_of, not both.
        """
        return self.client.delete_task_dependency(
            task_id,
            depends_on=depends_on,
            dependency_of=dependency_of,
            **params
        )

    # Task Relationship operations - Links
    def add_link(
        self,
        task_id: str,
        links_to: str,
        **params
    ) -> Dict[str, Any]:
        """
        Link two tasks together (simple relationship).

        This creates a simple, bidirectional link between two tasks for quick
        reference without enforcing any dependency rules.

        Args:
            task_id: The task to link from
            links_to: The task to link to
            **params: Additional query parameters (custom_task_ids, team_id)

        Returns:
            Updated task object with linked_tasks field

        Example:
            # Link related tasks together
            tasks.add_link("task_a_id", "task_b_id")
        """
        return self.client.add_task_link(task_id, links_to, **params)

    def remove_link(
        self,
        task_id: str,
        links_to: str,
        **params
    ) -> Dict[str, Any]:
        """
        Remove a link between two tasks.

        Args:
            task_id: The task to unlink from
            links_to: The task to unlink
            **params: Additional query parameters (custom_task_ids, team_id)

        Returns:
            Updated task object with linked_tasks field
        """
        return self.client.delete_task_link(task_id, links_to, **params)

    # Custom Relationship operations
    def set_relationship_field(
        self,
        task_id: str,
        field_id: str,
        add_task_ids: Optional[List[str]] = None,
        remove_task_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Set a custom relationship field value.

        Custom relationship fields allow you to link tasks from one list to tasks
        in another list, creating structured relationships (e.g., Projects -> Clients).

        Args:
            task_id: Task ID
            field_id: Custom relationship field ID
            add_task_ids: List of task IDs to add to the relationship
            remove_task_ids: List of task IDs to remove from the relationship

        Returns:
            Updated task (raw dict)

        Example:
            # Link a project to a client
            tasks.set_relationship_field(
                "project_task_id",
                "client_field_id",
                add_task_ids=["client_task_id"]
            )
        """
        value = {}
        if add_task_ids:
            value["add"] = add_task_ids
        if remove_task_ids:
            value["rem"] = remove_task_ids

        return self.client.set_custom_field_value(task_id, field_id, value)
