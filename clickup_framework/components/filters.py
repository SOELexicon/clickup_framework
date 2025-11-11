"""
Task Filtering Module

Provides utilities for filtering tasks by various criteria.
"""

from typing import List, Dict, Any, Optional, Callable


class TaskFilter:
    """
    Filters tasks by various criteria.

    Supports filtering by:
        - Status
        - Priority
        - Tags
        - Assignee
        - Date ranges
        - Custom fields
        - Parent tasks
    """

    @staticmethod
    def filter_by_status(tasks: List[Dict[str, Any]], status: str) -> List[Dict[str, Any]]:
        """
        Filter tasks by status.

        Args:
            tasks: List of tasks
            status: Status to filter by (case-insensitive)

        Returns:
            Filtered list of tasks
        """
        status_lower = status.lower()
        filtered = []

        for task in tasks:
            task_status = task.get('status', {})
            if isinstance(task_status, dict):
                task_status_name = task_status.get('status', '')
            else:
                task_status_name = task_status

            if str(task_status_name).lower() == status_lower:
                filtered.append(task)

        return filtered

    @staticmethod
    def filter_by_priority(tasks: List[Dict[str, Any]], priority: int) -> List[Dict[str, Any]]:
        """
        Filter tasks by priority.

        Args:
            tasks: List of tasks
            priority: Priority level (1-4, with 1 being highest)

        Returns:
            Filtered list of tasks
        """
        filtered = []

        for task in tasks:
            task_priority = task.get('priority', {})
            if isinstance(task_priority, dict):
                task_priority_val = task_priority.get('priority', 4)
            else:
                task_priority_val = task_priority

            try:
                if int(task_priority_val) == priority:
                    filtered.append(task)
            except (ValueError, TypeError):
                continue

        return filtered

    @staticmethod
    def filter_by_tags(tasks: List[Dict[str, Any]], tags: List[str]) -> List[Dict[str, Any]]:
        """
        Filter tasks that have ANY of the specified tags.

        Args:
            tasks: List of tasks
            tags: List of tag names to filter by

        Returns:
            Filtered list of tasks
        """
        tags_lower = [tag.lower() for tag in tags]
        filtered = []

        for task in tasks:
            task_tags = task.get('tags', [])
            task_tag_names = [tag.get('name', '').lower() for tag in task_tags if tag.get('name')]

            if any(tag in tags_lower for tag in task_tag_names):
                filtered.append(task)

        return filtered

    @staticmethod
    def filter_by_assignee(tasks: List[Dict[str, Any]], assignee_id: str) -> List[Dict[str, Any]]:
        """
        Filter tasks assigned to a specific user.

        Args:
            tasks: List of tasks
            assignee_id: User ID to filter by

        Returns:
            Filtered list of tasks
        """
        filtered = []

        for task in tasks:
            assignees = task.get('assignees', [])
            assignee_ids = [a.get('id') for a in assignees if a.get('id')]

            if assignee_id in assignee_ids:
                filtered.append(task)

        return filtered

    @staticmethod
    def filter_completed(tasks: List[Dict[str, Any]], include_completed: bool = False, show_closed_only: bool = False) -> List[Dict[str, Any]]:
        """
        Filter tasks by completion status.

        Args:
            tasks: List of tasks
            include_completed: Whether to include completed tasks along with open tasks
            show_closed_only: Whether to show ONLY closed tasks

        Returns:
            Filtered list of tasks
        """
        # If show_closed_only is True, return only closed tasks
        if show_closed_only:
            filtered = []
            for task in tasks:
                status = task.get('status', {})
                status_name = status.get('status') if isinstance(status, dict) else status
                is_completed = str(status_name).lower() in ('complete', 'completed', 'closed', 'done')

                if is_completed:
                    filtered.append(task)
            return filtered

        # If include_completed is True, return all tasks
        if include_completed:
            return tasks

        # Default: return only open tasks
        filtered = []
        for task in tasks:
            status = task.get('status', {})
            status_name = status.get('status') if isinstance(status, dict) else status
            is_completed = str(status_name).lower() in ('complete', 'completed', 'closed', 'done')

            if not is_completed:
                filtered.append(task)

        return filtered

    @staticmethod
    def filter_by_parent(tasks: List[Dict[str, Any]], parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Filter tasks by parent ID.

        Args:
            tasks: List of tasks
            parent_id: Parent task ID (None for root tasks)

        Returns:
            Filtered list of tasks
        """
        filtered = []

        for task in tasks:
            task_parent = task.get('parent')

            if parent_id is None:
                # Get root tasks (no parent)
                if not task_parent:
                    filtered.append(task)
            else:
                # Get tasks with specific parent
                if task_parent == parent_id:
                    filtered.append(task)

        return filtered

    @staticmethod
    def filter_by_date_range(
        tasks: List[Dict[str, Any]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        date_field: str = 'due_date'
    ) -> List[Dict[str, Any]]:
        """
        Filter tasks by date range.

        Args:
            tasks: List of tasks
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            date_field: Field to filter by ('due_date', 'date_created', 'date_updated')

        Returns:
            Filtered list of tasks
        """
        filtered = []

        for task in tasks:
            task_date = task.get(date_field)
            if not task_date:
                continue

            # Simple string comparison (assumes ISO format dates)
            if start_date and task_date < start_date:
                continue
            if end_date and task_date > end_date:
                continue

            filtered.append(task)

        return filtered

    @staticmethod
    def filter_by_custom_function(
        tasks: List[Dict[str, Any]],
        filter_fn: Callable[[Dict[str, Any]], bool]
    ) -> List[Dict[str, Any]]:
        """
        Filter tasks using a custom function.

        Args:
            tasks: List of tasks
            filter_fn: Function that returns True for tasks to keep

        Returns:
            Filtered list of tasks
        """
        return [task for task in tasks if filter_fn(task)]

    @staticmethod
    def combine_filters(
        tasks: List[Dict[str, Any]],
        filters: List[Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]]
    ) -> List[Dict[str, Any]]:
        """
        Apply multiple filters in sequence.

        Args:
            tasks: List of tasks
            filters: List of filter functions to apply

        Returns:
            Filtered list of tasks
        """
        result = tasks
        for filter_fn in filters:
            result = filter_fn(result)
        return result
