"""
Example complex command using BaseCommand with ID resolution and formatting.

This demonstrates a more complex command that uses multiple BaseCommand features:
- ID resolution
- Format options
- Error handling
- Colorization
"""

from typing import Optional
from clickup_framework.commands.base_command import BaseCommand
from clickup_framework.components import TaskDetailView
from clickup_framework.utils.colors import TextColor, TextStyle


class TaskDetailCommand(BaseCommand):
    """
    Example task detail command using BaseCommand.
    
    This shows how to use:
    - ID resolution methods
    - Format options
    - Error handling
    - Colorization
    """
    
    def execute(self):
        """Execute the task detail command."""
        # Get task ID from args or resolve from context
        task_id = self.args.task_id if hasattr(self.args, 'task_id') else None
        
        if not task_id:
            # Try to get from context
            task_id = self.get_task_id()
            if not task_id:
                self.error("No task ID provided. Use: cum detail <task_id> [list_id]")
        
        # Resolve task ID (handles 'current' keyword)
        try:
            resolved_task_id = self.resolve_id('task', task_id)
        except ValueError:
            # If resolve_id fails, it already called error() and exited
            return
        
        # Get list ID if provided (optional)
        list_id = None
        if hasattr(self.args, 'list_id') and self.args.list_id:
            list_id = self.resolve_list(self.args.list_id)
        
        # Fetch task data
        try:
            task = self.client.get_task(resolved_task_id)
        except Exception as e:
            self.error(f"Failed to fetch task: {e}")
        
        # Display task details using format options
        if self.format_options:
            view = TaskDetailView(self.client, self.format_options)
            view.display_task(task, list_id)
        else:
            # Simple display without formatting
            self._display_simple(task)
    
    def _display_simple(self, task: dict):
        """Display task in simple format."""
        name = task.get('name', 'Unnamed Task')
        status = task.get('status', {}).get('status', 'Unknown')
        
        self.print_color(f"Task: {name}", TextColor.BRIGHT_CYAN, TextStyle.BOLD)
        self.print(f"Status: {status}")
        self.print(f"ID: {task.get('id', 'Unknown')}")


def task_detail_command(args):
    """
    Command function wrapper for backward compatibility.
    """
    command = TaskDetailCommand(args, command_name='detail')
    command.run()


def register_command(subparsers, add_common_args=None):
    """Register the task detail command with argparse."""
    from clickup_framework.commands.utils import add_common_args
    
    parser = subparsers.add_parser(
        'detail',
        aliases=['d'],
        help='Display detailed task information',
        description='Show detailed information about a task'
    )
    parser.add_argument('task_id', help='Task ID or "current"')
    parser.add_argument('list_id', nargs='?', help='Optional list ID for context')
    
    # Add common formatting arguments
    add_common_args(parser)
    
    parser.set_defaults(func=task_detail_command)

