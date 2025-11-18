"""Clear current context command."""

from clickup_framework.commands.base_command import BaseCommand


class ClearCurrentCommand(BaseCommand):
    """
    Clear Current Command using BaseCommand.
    """

    def execute(self):
        """Execute the clear current command."""
        if self.args.resource_type:
            resource_type = self.args.resource_type.lower()

            # Map resource types to clear methods
            clearers = {
                'task': self.context.clear_current_task,
                'list': self.context.clear_current_list,
                'space': self.context.clear_current_space,
                'folder': self.context.clear_current_folder,
                'workspace': self.context.clear_current_workspace,
                'team': self.context.clear_current_workspace,  # Alias
                'token': self.context.clear_api_token,
            }

            clearer = clearers.get(resource_type)
            if not clearer:
                self.error(f"Unknown resource type '{resource_type}'. "
                          f"Valid types: {', '.join(clearers.keys())}")

            clearer()
            self.print_success(f"Cleared current {resource_type}")
        else:
            # Clear all context
            self.context.clear_all()
            self.print_success("Cleared all context")


def clear_current_command(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = ClearCurrentCommand(args, command_name='clear_current')
    command.execute()


def register_command(subparsers, add_common_args=None):
    """Register the clear_current command with argparse."""
    parser = subparsers.add_parser(
        'clear_current',
        aliases=['clear'],
        help='Clear current resource context',
        description='Clear current resource context or all context',
        epilog='''Tips:
  • Clear all context: cum clear
  • Clear specific resource: cum clear task
  • Clear API token: cum clear token
  • Use after switching projects
  • Check context before clearing: cum show'''
    )
    parser.add_argument(
        'resource_type',
        nargs='?',
        choices=['task', 'list', 'space', 'folder', 'workspace', 'team', 'assignee', 'token'],
        help='Type of resource to clear (omit to clear all)'
    )
    parser.set_defaults(func=clear_current_command)
