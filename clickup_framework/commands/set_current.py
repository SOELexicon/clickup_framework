"""Set current context command."""

from clickup_framework.commands.base_command import BaseCommand


class SetCurrentCommand(BaseCommand):
    """
    Set current resource context command using BaseCommand.

    Sets the current context for task, list, space, folder, workspace,
    assignee, or API token.
    """

    def execute(self):
        """Execute the set current command."""
        resource_type = self.args.resource_type.lower()
        resource_id = self.args.resource_id

        # Map resource types to setter methods
        setters = {
            'task': self.context.set_current_task,
            'list': self.context.set_current_list,
            'space': self.context.set_current_space,
            'folder': self.context.set_current_folder,
            'workspace': self.context.set_current_workspace,
            'team': self.context.set_current_workspace,  # Alias
            'assignee': lambda aid: self.context.set_default_assignee(int(aid)),
            'token': self.context.set_api_token,
        }

        setter = setters.get(resource_type)
        if not setter:
            self.error(f"Unknown resource type '{resource_type}'. "
                      f"Valid types: {', '.join(setters.keys())}")

        try:
            setter(resource_id)
            # Mask token in output for security
            if resource_type == 'token':
                masked_token = f"{resource_id[:15]}...{resource_id[-4:]}" if len(resource_id) > 20 else "********"
                self.print_success(f"API token validated and saved successfully: {masked_token}")
            else:
                self.print_success(f"Set current {resource_type} to: {resource_id}")
        except ValueError as e:
            self.error(str(e))


def set_current_command(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = SetCurrentCommand(args, command_name='set_current')
    command.execute()


def register_command(subparsers, add_common_args=None):
    """Register the set_current command with argparse."""
    parser = subparsers.add_parser(
        'set_current',
        aliases=['set'],
        help='Set current resource context',
        description='Set current resource context for use with "current" keyword',
        epilog='''Tips:
  • Set current task: cum set task 86abc123
  • Set current list: cum set list 901234567
  • Set API token: cum set token your-api-token
  • Set default assignee: cum set assignee 12345678
  • Use "current" in commands: cum d current
  • Check current context: cum show'''
    )
    parser.add_argument(
        'resource_type',
        choices=['task', 'list', 'space', 'folder', 'workspace', 'team', 'assignee', 'token'],
        help='Type of resource to set as current'
    )
    parser.add_argument('resource_id', help='ID/value of the resource (API token for token type)')
    parser.set_defaults(func=set_current_command)
