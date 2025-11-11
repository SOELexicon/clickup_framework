"""
Container Hierarchy Formatter Module

Organizes and formats tasks by their container hierarchy (workspace → space → folder → list).
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from clickup_framework.components.options import FormatOptions
from clickup_framework.components.task_formatter import RichTaskFormatter
from clickup_framework.utils.colors import colorize, container_color, completion_color, TextColor, TextStyle


class ContainerHierarchyFormatter:
    """
    Formats tasks organized by container hierarchy.

    Creates a tree view showing:
        Workspace
        └─Space (3/5)
          └─Folder (2/3)
            └─List (1/2)
              └─Task Name
    """

    def __init__(self, formatter: Optional[RichTaskFormatter] = None):
        """
        Initialize the container hierarchy formatter.

        Args:
            formatter: Task formatter to use
        """
        self.formatter = formatter or RichTaskFormatter()

    def format_container_hierarchy(
        self,
        tasks: List[Dict[str, Any]],
        options: Optional[FormatOptions] = None
    ) -> str:
        """
        Format tasks organized by container hierarchy.

        Args:
            tasks: List of tasks
            options: Format options

        Returns:
            Formatted hierarchy string
        """
        if options is None:
            options = FormatOptions()

        # Build container structure
        structure = self._build_container_structure(tasks, options)

        # Format the output
        lines = []

        if options.colorize_output:
            header = colorize("Tasks organized by container:", TextColor.BRIGHT_WHITE, TextStyle.BOLD)
        else:
            header = "Tasks organized by container:"

        lines.append(header)
        lines.append("")

        # Format each workspace/space
        for space_id, space_data in structure.items():
            lines.extend(self._format_space(space_data, options))

        # Add summary
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if self._is_completed(t))

        lines.append("")
        if options.colorize_output:
            color = completion_color(completed_tasks, total_tasks)
            summary = f"Total: {colorize(f'{completed_tasks}/{total_tasks} tasks complete', color)}"
        else:
            summary = f"Total: {completed_tasks}/{total_tasks} tasks complete"

        lines.append(summary)

        return "\n".join(lines)

    def _build_container_structure(
        self,
        tasks: List[Dict[str, Any]],
        options: FormatOptions
    ) -> Dict[str, Any]:
        """
        Build the container hierarchy structure from tasks.

        Args:
            tasks: List of tasks
            options: Format options

        Returns:
            Nested dictionary structure
        """
        structure = defaultdict(lambda: {
            'name': '',
            'folders': defaultdict(lambda: {
                'name': '',
                'lists': defaultdict(lambda: {
                    'name': '',
                    'tasks': []
                })
            })
        })

        for task in tasks:
            # Filter tasks based on completion status
            is_completed = self._is_completed(task)
            if options.show_closed_only:
                # Show ONLY closed tasks - skip if not completed
                if not is_completed:
                    continue
            elif not options.include_completed:
                # Show only open tasks (default) - skip if completed
                if is_completed:
                    continue
            # If include_completed is True, show all tasks (no filtering)

            # Extract container information
            space = task.get('space', {}) or {}
            folder = task.get('folder', {}) or {}
            list_info = task.get('list', {}) or {}

            space_id = space.get('id', 'unknown')
            space_name = space.get('name', 'Unknown Space')
            folder_id = folder.get('id', 'no_folder') if folder else 'no_folder'
            folder_name = folder.get('name', 'No Folder') if folder else 'No Folder'
            list_id = list_info.get('id', 'unknown')
            list_name = list_info.get('name', 'Unknown List')

            # Build structure
            if not structure[space_id]['name']:
                structure[space_id]['name'] = space_name

            if not structure[space_id]['folders'][folder_id]['name']:
                structure[space_id]['folders'][folder_id]['name'] = folder_name

            if not structure[space_id]['folders'][folder_id]['lists'][list_id]['name']:
                structure[space_id]['folders'][folder_id]['lists'][list_id]['name'] = list_name

            structure[space_id]['folders'][folder_id]['lists'][list_id]['tasks'].append(task)

        return dict(structure)

    def _format_space(self, space_data: Dict[str, Any], options: FormatOptions) -> List[str]:
        """Format a space and its contents."""
        lines = []
        space_name = space_data['name']

        # Calculate totals
        total, completed = self._count_tasks(space_data)

        # Format space header
        space_line = f"{space_name} ({completed}/{total})"
        if options.colorize_output:
            color = container_color('space')
            stat_color = completion_color(completed, total)
            space_line = f"{colorize(space_name, color)} {colorize(f'({completed}/{total})', stat_color)}"

        lines.append(f"├─{space_line}")

        # Format folders
        folders = list(space_data['folders'].items())
        for i, (folder_id, folder_data) in enumerate(folders):
            is_last_folder = (i == len(folders) - 1)
            folder_lines = self._format_folder(folder_data, options, is_last_folder)
            # Add proper indentation
            for line in folder_lines:
                if is_last_folder:
                    lines.append(f"  {line}")
                else:
                    lines.append(f"│ {line}")

        return lines

    def _format_folder(
        self,
        folder_data: Dict[str, Any],
        options: FormatOptions,
        is_last: bool
    ) -> List[str]:
        """Format a folder and its contents."""
        lines = []
        folder_name = folder_data['name']

        # Calculate totals
        total, completed = self._count_tasks_in_folder(folder_data)

        # Format folder header
        folder_line = f"{folder_name} ({completed}/{total})"
        if options.colorize_output:
            color = container_color('folder')
            stat_color = completion_color(completed, total)
            folder_line = f"{colorize(folder_name, color)} {colorize(f'({completed}/{total})', stat_color)}"

        branch = "└─" if is_last else "├─"
        lines.append(f"{branch}{folder_line}")

        # Format lists
        lists = list(folder_data['lists'].items())
        for i, (list_id, list_data) in enumerate(lists):
            is_last_list = (i == len(lists) - 1)
            list_lines = self._format_list(list_data, options, is_last_list)
            # Add proper indentation
            prefix = "  " if is_last else "│ "
            for line in list_lines:
                lines.append(f"{prefix}{line}")

        return lines

    def _format_list(
        self,
        list_data: Dict[str, Any],
        options: FormatOptions,
        is_last: bool
    ) -> List[str]:
        """Format a list and its tasks."""
        lines = []
        list_name = list_data['name']
        tasks = list_data['tasks']

        total = len(tasks)
        completed = sum(1 for t in tasks if self._is_completed(t))

        # Format list header
        list_line = f"{list_name} ({completed}/{total})"
        if options.colorize_output:
            color = container_color('list')
            stat_color = completion_color(completed, total)
            list_line = f"{colorize(list_name, color)} {colorize(f'({completed}/{total})', stat_color)}"

        branch = "└─" if is_last else "├─"
        lines.append(f"{branch}{list_line}")

        # Format tasks
        for i, task in enumerate(tasks):
            is_last_task = (i == len(tasks) - 1)
            task_branch = "└─" if is_last_task else "├─"

            formatted_task = self.formatter.format_task(task, options)
            prefix = "  " if is_last else "│ "

            # Handle multi-line formatted content
            formatted_lines = formatted_task.split('\n')

            # Add the first line with branch character
            lines.append(f"{prefix}{task_branch}{formatted_lines[0]}")

            # Add remaining lines with proper indentation
            if len(formatted_lines) > 1:
                # Calculate the continuation prefix for multi-line task content
                if is_last_task:
                    continuation_prefix = prefix + "  "  # No vertical line
                else:
                    continuation_prefix = prefix + "│ "  # Continue vertical line

                for line in formatted_lines[1:]:
                    lines.append(f"{continuation_prefix}{line}")

        return lines

    def _count_tasks(self, space_data: Dict[str, Any]) -> tuple:
        """Count total and completed tasks in a space."""
        total = 0
        completed = 0

        for folder_data in space_data['folders'].values():
            for list_data in folder_data['lists'].values():
                for task in list_data['tasks']:
                    total += 1
                    if self._is_completed(task):
                        completed += 1

        return total, completed

    def _count_tasks_in_folder(self, folder_data: Dict[str, Any]) -> tuple:
        """Count total and completed tasks in a folder."""
        total = 0
        completed = 0

        for list_data in folder_data['lists'].values():
            for task in list_data['tasks']:
                total += 1
                if self._is_completed(task):
                    completed += 1

        return total, completed

    @staticmethod
    def _is_completed(task: Dict[str, Any]) -> bool:
        """Check if a task is completed."""
        status = task.get('status', {})
        status_name = status.get('status') if isinstance(status, dict) else status
        return str(status_name).lower() in ('complete', 'completed', 'closed', 'done')
