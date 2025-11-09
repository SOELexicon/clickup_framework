"""
Display Manager Module

Provides a high-level interface for displaying tasks in various formats.
"""

from typing import List, Dict, Any, Optional
from clickup_framework.client import ClickUpClient
from clickup_framework.components.options import FormatOptions
from clickup_framework.components.hierarchy import TaskHierarchyFormatter
from clickup_framework.components.container import ContainerHierarchyFormatter
from clickup_framework.components.task_formatter import RichTaskFormatter
from clickup_framework.components.detail_view import TaskDetailFormatter
from clickup_framework.components.filters import TaskFilter


class DisplayManager:
    """
    High-level manager for displaying ClickUp data.

    Combines filtering, organizing, and rendering into a simple interface.

    Example Usage:
        ```python
        from clickup_framework import ClickUpClient
        from clickup_framework.components import DisplayManager, FormatOptions

        client = ClickUpClient()
        display = DisplayManager(client)

        # Display tasks in hierarchical view
        tasks = client.get_list_tasks("list_id")
        print(display.hierarchy_view(tasks))

        # Display with custom options
        options = FormatOptions.detailed()
        print(display.container_view(tasks, options))
        ```
    """

    def __init__(self, client: Optional[ClickUpClient] = None):
        """
        Initialize the display manager.

        Args:
            client: ClickUp client instance (optional)
        """
        self.client = client
        self.task_formatter = RichTaskFormatter()
        self.hierarchy_formatter = TaskHierarchyFormatter(self.task_formatter)
        self.container_formatter = ContainerHierarchyFormatter(self.task_formatter)
        self.detail_formatter = TaskDetailFormatter()
        self.filter = TaskFilter()

    def hierarchy_view(
        self,
        tasks: List[Dict[str, Any]],
        options: Optional[FormatOptions] = None,
        header: Optional[str] = None
    ) -> str:
        """
        Display tasks in hierarchical parent-child view.

        Args:
            tasks: List of tasks
            options: Format options
            header: Optional header text

        Returns:
            Formatted hierarchy string
        """
        return self.hierarchy_formatter.format_hierarchy(tasks, options, header)

    def container_view(
        self,
        tasks: List[Dict[str, Any]],
        options: Optional[FormatOptions] = None
    ) -> str:
        """
        Display tasks organized by container hierarchy.

        Args:
            tasks: List of tasks
            options: Format options

        Returns:
            Formatted container hierarchy string
        """
        return self.container_formatter.format_container_hierarchy(tasks, options)

    def flat_view(
        self,
        tasks: List[Dict[str, Any]],
        options: Optional[FormatOptions] = None,
        header: Optional[str] = None
    ) -> str:
        """
        Display tasks in a flat list.

        Args:
            tasks: List of tasks
            options: Format options
            header: Optional header text

        Returns:
            Formatted list string
        """
        if options is None:
            options = FormatOptions()

        lines = []

        if header:
            lines.append(header)
            lines.append("")

        for task in tasks:
            formatted = self.task_formatter.format_task(task, options)
            lines.append(formatted)

        return "\n".join(lines)

    def filtered_view(
        self,
        tasks: List[Dict[str, Any]],
        status: Optional[str] = None,
        priority: Optional[int] = None,
        tags: Optional[List[str]] = None,
        assignee_id: Optional[str] = None,
        include_completed: bool = False,
        options: Optional[FormatOptions] = None,
        view_mode: str = 'hierarchy'
    ) -> str:
        """
        Display filtered tasks.

        Args:
            tasks: List of tasks
            status: Filter by status
            priority: Filter by priority
            tags: Filter by tags
            assignee_id: Filter by assignee
            include_completed: Include completed tasks
            options: Format options
            view_mode: Display mode ('hierarchy', 'container', 'flat')

        Returns:
            Formatted filtered view
        """
        # Apply filters
        filtered_tasks = tasks

        if status:
            filtered_tasks = self.filter.filter_by_status(filtered_tasks, status)

        if priority:
            filtered_tasks = self.filter.filter_by_priority(filtered_tasks, priority)

        if tags:
            filtered_tasks = self.filter.filter_by_tags(filtered_tasks, tags)

        if assignee_id:
            filtered_tasks = self.filter.filter_by_assignee(filtered_tasks, assignee_id)

        if not include_completed:
            filtered_tasks = self.filter.filter_completed(filtered_tasks, include_completed)

        # Display based on view mode
        if view_mode == 'hierarchy':
            return self.hierarchy_view(filtered_tasks, options)
        elif view_mode == 'container':
            return self.container_view(filtered_tasks, options)
        else:
            return self.flat_view(filtered_tasks, options)

    def get_list_tasks_display(
        self,
        list_id: str,
        options: Optional[FormatOptions] = None,
        view_mode: str = 'hierarchy'
    ) -> str:
        """
        Fetch and display tasks from a list.

        Args:
            list_id: List ID
            options: Format options
            view_mode: Display mode

        Returns:
            Formatted task display

        Raises:
            ValueError: If client is not configured
        """
        if not self.client:
            raise ValueError("ClickUpClient must be configured to fetch tasks")

        result = self.client.get_list_tasks(list_id)
        # Handle both dict response {'tasks': [...]} and direct list response
        tasks = result if isinstance(result, list) else result.get('tasks', [])

        if view_mode == 'hierarchy':
            return self.hierarchy_view(tasks, options)
        elif view_mode == 'container':
            return self.container_view(tasks, options)
        else:
            return self.flat_view(tasks, options)

    def get_team_tasks_display(
        self,
        team_id: str,
        options: Optional[FormatOptions] = None,
        view_mode: str = 'container'
    ) -> str:
        """
        Fetch and display tasks from a team.

        Args:
            team_id: Team/workspace ID
            options: Format options
            view_mode: Display mode

        Returns:
            Formatted task display

        Raises:
            ValueError: If client is not configured
        """
        if not self.client:
            raise ValueError("ClickUpClient must be configured to fetch tasks")

        result = self.client.get_team_tasks(team_id)
        # Handle both dict response {'tasks': [...]} and direct list response
        tasks = result if isinstance(result, list) else result.get('tasks', [])

        if view_mode == 'hierarchy':
            return self.hierarchy_view(tasks, options)
        elif view_mode == 'container':
            return self.container_view(tasks, options)
        else:
            return self.flat_view(tasks, options)

    def detail_view(
        self,
        task: Dict[str, Any],
        all_tasks: Optional[List[Dict[str, Any]]] = None,
        options: Optional[FormatOptions] = None
    ) -> str:
        """
        Display comprehensive details of a single task with relationship tree.

        Shows the task with its full context including parent chain, siblings,
        children (subtasks), and dependencies in a tree view.

        Args:
            task: The task to display
            all_tasks: All tasks (for resolving relationships)
            options: Format options

        Returns:
            Formatted detailed task view with relationships

        Example:
            ```python
            # Show a task with its full relationship context
            task = client.get_task("task_id")
            all_tasks = client.get_list_tasks("list_id")

            output = display.detail_view(task, all_tasks, FormatOptions.detailed())
            print(output)
            ```
        """
        if all_tasks:
            return self.detail_formatter.format_with_context(task, all_tasks, options)
        else:
            return self.detail_formatter.format_detail(task, options)

    def summary_stats(self, tasks: List[Dict[str, Any]]) -> str:
        """
        Get summary statistics for tasks.

        Args:
            tasks: List of tasks

        Returns:
            Formatted summary string
        """
        counts = self.hierarchy_formatter.get_task_count(tasks)

        lines = [
            "Task Summary:",
            f"  Total: {counts['total']}",
            f"  Completed: {counts['completed']}",
            f"  In Progress: {counts['in_progress']}",
            f"  Blocked: {counts['blocked']}",
            f"  To Do: {counts['todo']}"
        ]

        return "\n".join(lines)
