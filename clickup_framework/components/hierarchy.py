"""
Task Hierarchy Organization Module

Provides utilities for organizing tasks by parent-child relationships.
"""

import logging
from typing import List, Dict, Any, Set, Optional
from clickup_framework.components.options import FormatOptions
from clickup_framework.components.task_formatter import RichTaskFormatter
from clickup_framework.components.tree import TreeFormatter

logger = logging.getLogger(__name__)


class TaskHierarchyFormatter:
    """
    Organizes and formats tasks in hierarchical structures.

    Supports:
        - Parent-child task relationships
        - Dependency-based organization
        - Orphaned task detection
    """

    def __init__(self, formatter: Optional[RichTaskFormatter] = None, client=None):
        """
        Initialize the hierarchy formatter.

        Args:
            formatter: Task formatter to use (creates default if not provided)
            client: Optional ClickUpClient for fetching missing parent tasks
        """
        self.formatter = formatter or RichTaskFormatter()
        self.client = client
        self.circular_refs_detected = []  # Track detected circular references
        self.orphaned_tasks_handled = []  # Track orphaned tasks that were resolved

    def _detect_circular_references(
        self,
        task_map: Dict[str, Dict[str, Any]]
    ) -> Set[str]:
        """
        Detect circular references in parent-child relationships.

        Args:
            task_map: Dictionary mapping task IDs to task objects

        Returns:
            Set of task IDs that are part of circular references
        """
        circular_task_ids = set()

        def has_cycle(task_id: str, visited: Set[str], path: List[str]) -> bool:
            """
            Check if following the parent chain from this task leads to a cycle.

            Args:
                task_id: Current task ID to check
                visited: Set of task IDs already visited in this path
                path: Current path of task IDs (for logging)

            Returns:
                True if a cycle is detected, False otherwise
            """
            if task_id in visited:
                # Found a cycle!
                cycle_start_idx = path.index(task_id)
                cycle_path = path[cycle_start_idx:] + [task_id]
                cycle_names = [task_map.get(tid, {}).get('name', tid) for tid in cycle_path]

                logger.error(
                    f"Circular reference detected in task hierarchy!\n"
                    f"  Cycle: {' → '.join(cycle_names)}\n"
                    f"  Task IDs: {' → '.join(cycle_path)}\n"
                    f"  Breaking cycle by removing parent relationship."
                )

                # Add all tasks in the cycle to the set
                for tid in cycle_path[:-1]:  # Exclude the duplicate at the end
                    circular_task_ids.add(tid)

                # Store for potential user notification
                self.circular_refs_detected.append({
                    'cycle_path': cycle_path,
                    'cycle_names': cycle_names
                })

                return True

            if task_id not in task_map:
                # Task not in map, can't continue checking
                return False

            task = task_map[task_id]
            parent_id = task.get('parent')

            if not parent_id:
                # No parent, no cycle possible
                return False

            # Add to visited set and path
            visited.add(task_id)
            path.append(task_id)

            # Check parent
            cycle_found = has_cycle(parent_id, visited, path)

            # Remove from path (backtrack)
            path.pop()

            return cycle_found

        # Check each task for cycles
        for task_id in task_map:
            if task_id not in circular_task_ids:
                has_cycle(task_id, set(), [])

        return circular_task_ids

    def _handle_orphaned_tasks(
        self,
        tasks: List[Dict[str, Any]],
        task_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Handle orphaned tasks by attempting to fetch missing parents.

        Args:
            tasks: List of all tasks
            task_map: Current task map (will be modified if parents are fetched)

        Returns:
            Updated task map with fetched parent tasks added
        """
        if not self.client:
            # No client available, can't fetch missing parents
            return task_map

        orphaned_tasks = []
        missing_parent_ids = set()

        # Find orphaned tasks (tasks with parent ID not in task_map)
        for task in tasks:
            parent_id = task.get('parent')
            if parent_id and parent_id not in task_map:
                orphaned_tasks.append(task)
                missing_parent_ids.add(parent_id)

        # Attempt to fetch missing parents
        for parent_id in missing_parent_ids:
            try:
                logger.info(f"Fetching missing parent task: {parent_id}")
                parent_task = self.client.get_task(parent_id)

                if parent_task and parent_task.get('id'):
                    # Successfully fetched parent, add to task_map
                    task_map[parent_id] = parent_task
                    logger.info(f"Successfully fetched parent: {parent_task.get('name', parent_id)}")

                    # Track that we resolved this orphaned task
                    self.orphaned_tasks_handled.append({
                        'parent_id': parent_id,
                        'parent_name': parent_task.get('name', parent_id),
                        'status': 'fetched'
                    })
                else:
                    logger.warning(f"Parent task {parent_id} fetch returned empty result")
                    self.orphaned_tasks_handled.append({
                        'parent_id': parent_id,
                        'status': 'fetch_failed'
                    })

            except Exception as e:
                logger.warning(f"Failed to fetch parent task {parent_id}: {e}")
                # Track failed fetch
                self.orphaned_tasks_handled.append({
                    'parent_id': parent_id,
                    'status': 'fetch_failed',
                    'error': str(e)
                })

        return task_map

    def organize_by_parent_child(
        self,
        tasks: List[Dict[str, Any]],
        include_orphaned: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Organize tasks into a parent-child hierarchy with circular reference detection.

        Args:
            tasks: Flat list of tasks
            include_orphaned: Whether to include orphaned tasks

        Returns:
            List of root tasks with nested children

        Notes:
            - Detects and breaks circular references in parent-child relationships
            - Tasks involved in circular references are treated as root tasks
            - Logs errors when circular references are detected
        """
        # Reset tracking
        self.circular_refs_detected = []
        self.orphaned_tasks_handled = []

        # Build task map
        task_map = {task['id']: task for task in tasks if task.get('id')}

        # Handle orphaned tasks by fetching missing parents
        task_map = self._handle_orphaned_tasks(tasks, task_map)

        # Detect circular references
        circular_task_ids = self._detect_circular_references(task_map)

        # Find root tasks (no parent, parent not in list, or part of circular reference)
        root_tasks = []
        for task in tasks:
            parent_id = task.get('parent')
            task_id = task.get('id')

            # Treat tasks in circular references as root tasks (breaks the cycle)
            if task_id in circular_task_ids:
                root_tasks.append(task)
            elif not parent_id or parent_id not in task_map:
                if include_orphaned or not parent_id:
                    root_tasks.append(task)

        # Build children lists for each task
        for task in tasks:
            task['_children'] = []

        for task in tasks:
            parent_id = task.get('parent')
            task_id = task.get('id')

            # Only add as child if:
            # 1. Has a parent
            # 2. Parent exists in task_map
            # 3. Not part of a circular reference (already promoted to root)
            if parent_id and parent_id in task_map and task_id not in circular_task_ids:
                task_map[parent_id]['_children'].append(task)

        # Sort root tasks by priority and name
        root_tasks.sort(key=lambda t: (
            self._get_priority_value(t),
            t.get('name', '').lower()
        ))

        return root_tasks

    def get_circular_reference_warnings(self) -> Optional[str]:
        """
        Get user-friendly warnings about detected circular references.

        Returns:
            Warning message string if circular references were detected, None otherwise
        """
        if not self.circular_refs_detected:
            return None

        warnings = ["⚠️  Warning: Circular references detected in task hierarchy!"]
        warnings.append("")

        for idx, cycle_info in enumerate(self.circular_refs_detected, 1):
            cycle_names = cycle_info['cycle_names']
            warnings.append(f"  Cycle {idx}: {' → '.join(cycle_names)}")

        warnings.append("")
        warnings.append("  These tasks have been promoted to root level to prevent infinite loops.")
        warnings.append("  Please fix the parent relationships in ClickUp to resolve this issue.")
        warnings.append("")

        return "\n".join(warnings)

    def get_orphaned_task_info(self) -> Optional[str]:
        """
        Get information about orphaned tasks that were handled.

        Returns:
            Info message string if orphaned tasks were handled, None otherwise
        """
        if not self.orphaned_tasks_handled:
            return None

        # Separate fetched and failed
        fetched = [t for t in self.orphaned_tasks_handled if t['status'] == 'fetched']
        failed = [t for t in self.orphaned_tasks_handled if t['status'] == 'fetch_failed']

        if not fetched and not failed:
            return None

        info_lines = []

        if fetched:
            info_lines.append(f"ℹ️  Info: Fetched {len(fetched)} missing parent task(s):")
            for task_info in fetched:
                info_lines.append(f"  • {task_info['parent_name']} [{task_info['parent_id']}]")
            info_lines.append("")

        if failed:
            info_lines.append(f"⚠️  Warning: {len(failed)} orphaned task(s) with missing parents:")
            info_lines.append("  These tasks are shown at root level because their parent tasks could not be fetched.")
            for task_info in failed:
                parent_id = task_info['parent_id']
                info_lines.append(f"  • Parent ID: {parent_id}")
            info_lines.append("")

        return "\n".join(info_lines) if info_lines else None

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
            Formatted hierarchy string with circular reference warnings if detected
        """
        if options is None:
            options = FormatOptions()

        # Organize tasks into hierarchy (detects circular references)
        root_tasks = self.organize_by_parent_child(
            tasks,
            include_orphaned=not options.hide_orphaned
        )

        # Check for warnings and info messages
        circular_warning = self.get_circular_reference_warnings()
        orphaned_info = self.get_orphaned_task_info()

        # Filter by completion if needed
        if options.show_closed_only:
            # Show ONLY closed tasks
            root_tasks = [t for t in root_tasks if self._is_completed(t)]
        elif not options.include_completed:
            # Show only open tasks (default behavior)
            root_tasks = [t for t in root_tasks if not self._is_completed(t)]
        # If include_completed is True, show all tasks (no filtering)

        # Check if there are any tasks to display after filtering
        if not root_tasks:
            if options.show_closed_only:
                return "No closed tasks found."
            elif not options.include_completed:
                return "No open tasks found. Use --include-completed to show all tasks."
            else:
                return "No tasks found."

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

        # Render the tree with optional depth limit
        tree_output = TreeFormatter.render(
            root_tasks,
            format_fn,
            get_children_fn,
            header,
            max_depth=options.max_depth
        )

        # Prepend warnings and info messages
        messages = []
        if circular_warning:
            messages.append(circular_warning)
        if orphaned_info:
            messages.append(orphaned_info)

        if messages:
            return "\n".join(messages) + "\n" + tree_output
        else:
            return tree_output

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
