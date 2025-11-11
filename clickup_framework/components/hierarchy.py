"""
Task Hierarchy Organization Module

Provides utilities for organizing tasks by parent-child relationships.
"""

from typing import List, Dict, Any, Set, Optional
from clickup_framework.components.options import FormatOptions
from clickup_framework.components.task_formatter import RichTaskFormatter
from clickup_framework.components.tree import TreeFormatter


class TaskHierarchyFormatter:
    """
    Organizes and formats tasks in hierarchical structures.

    Supports:
        - Parent-child task relationships
        - Dependency-based organization
        - Orphaned task detection
    """

    def __init__(self, formatter: Optional[RichTaskFormatter] = None):
        """
        Initialize the hierarchy formatter.

        Args:
            formatter: Task formatter to use (creates default if not provided)
        """
        self.formatter = formatter or RichTaskFormatter()

    def organize_by_parent_child(
        self,
        tasks: List[Dict[str, Any]],
        include_orphaned: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Organize tasks into a parent-child hierarchy.

        Args:
            tasks: Flat list of tasks
            include_orphaned: Whether to include orphaned tasks

        Returns:
            List of root tasks with nested children
        """
        # Build task map
        task_map = {task['id']: task for task in tasks if task.get('id')}

        # Find root tasks (no parent or parent not in list)
        root_tasks = []
        for task in tasks:
            parent_id = task.get('parent')
            if not parent_id or parent_id not in task_map:
                if include_orphaned or not parent_id:
                    root_tasks.append(task)

        # Build children lists for each task
        for task in tasks:
            task['_children'] = []

        for task in tasks:
            parent_id = task.get('parent')
            if parent_id and parent_id in task_map:
                task_map[parent_id]['_children'].append(task)

        # Sort root tasks by priority and name
        root_tasks.sort(key=lambda t: (
            self._get_priority_value(t),
            t.get('name', '').lower()
        ))

        return root_tasks

    def format_hierarchy(
        self,
        tasks: List[Dict[str, Any]],
        options: Optional[FormatOptions] = None,
        header: Optional[str] = None
    ) -> str:
        """
        Format tasks in a hierarchical tree view.

        Args:
            tasks: List of tasks
            options: Format options
            header: Optional header text

        Returns:
            Formatted hierarchy string
        """
        if options is None:
            options = FormatOptions()

        # Organize tasks into hierarchy
        root_tasks = self.organize_by_parent_child(
            tasks,
            include_orphaned=not options.hide_orphaned
        )

        # Filter by completion if needed
        if options.show_closed_only:
            # Show ONLY closed tasks
            root_tasks = [t for t in root_tasks if self._is_completed(t)]
        elif not options.include_completed:
            # Show only open tasks (default behavior)
            root_tasks = [t for t in root_tasks if not self._is_completed(t)]
        # If include_completed is True, show all tasks (no filtering)

        # Define functions for tree building
        def format_fn(task):
            return self.formatter.format_task(task, options)

        def get_children_fn(task):
            children = task.get('_children', [])
            if options.show_closed_only:
                # Show ONLY closed tasks
                children = [c for c in children if self._is_completed(c)]
            elif not options.include_completed:
                # Show only open tasks (default behavior)
                children = [c for c in children if not self._is_completed(c)]
            # If include_completed is True, show all children (no filtering)
            return sorted(children, key=lambda t: (
                self._get_priority_value(t),
                t.get('name', '').lower()
            ))

        # Render the tree
        return TreeFormatter.render(root_tasks, format_fn, get_children_fn, header)

    def organize_by_dependencies(
        self,
        tasks: List[Dict[str, Any]],
        dependency_type: str = 'waiting_on'
    ) -> List[Dict[str, Any]]:
        """
        Organize tasks by dependency relationships.

        Args:
            tasks: List of tasks
            dependency_type: Type of dependency ('waiting_on', 'blocking')

        Returns:
            List of root tasks with nested dependencies
        """
        task_map = {task['id']: task for task in tasks if task.get('id')}

        # Build dependency relationships
        for task in tasks:
            task['_deps'] = []

        for task in tasks:
            dependencies = task.get('dependencies', [])
            for dep in dependencies:
                dep_id = dep.get('depends_on') if dependency_type == 'waiting_on' else dep.get('task_id')
                if dep_id and dep_id in task_map:
                    task_map[dep_id]['_deps'].append(task)

        # Find tasks with no dependencies
        root_tasks = [task for task in tasks if not task.get('_deps')]

        return sorted(root_tasks, key=lambda t: (
            self._get_priority_value(t),
            t.get('name', '').lower()
        ))

    def get_task_count(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get counts of tasks by status.

        Args:
            tasks: List of tasks

        Returns:
            Dictionary with task counts
        """
        counts = {
            'total': len(tasks),
            'completed': 0,
            'in_progress': 0,
            'blocked': 0,
            'todo': 0
        }

        for task in tasks:
            status = self._get_status(task)
            if status == 'complete':
                counts['completed'] += 1
            elif status in ('in progress', 'in review'):
                counts['in_progress'] += 1
            elif status == 'blocked':
                counts['blocked'] += 1
            else:
                counts['todo'] += 1

        return counts

    @staticmethod
    def _is_completed(task: Dict[str, Any]) -> bool:
        """Check if a task is completed."""
        status = task.get('status', {})
        status_name = status.get('status') if isinstance(status, dict) else status
        return str(status_name).lower() in ('complete', 'completed', 'closed', 'done')

    @staticmethod
    def _get_status(task: Dict[str, Any]) -> str:
        """Get task status as a string."""
        status = task.get('status', {})
        if isinstance(status, dict):
            return str(status.get('status', '')).lower()
        return str(status).lower()

    @staticmethod
    def _get_priority_value(task: Dict[str, Any]) -> int:
        """Get numeric priority value (1=urgent, 4=low)."""
        priority = task.get('priority', {})

        # Extract priority value from dict or use direct value
        if isinstance(priority, dict):
            priority_val = priority.get('priority', 4)
        else:
            priority_val = priority

        # Handle string priority names
        if isinstance(priority_val, str):
            # Check if it's a numeric string first
            if priority_val.isdigit():
                return int(priority_val)

            priority_map = {
                'urgent': 1,
                'high': 2,
                'normal': 3,
                'low': 4
            }
            return priority_map.get(priority_val.lower(), 4)

        # Try to convert to int
        try:
            return int(priority_val)
        except (ValueError, TypeError):
            return 4
