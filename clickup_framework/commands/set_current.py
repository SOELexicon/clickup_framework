"""Set current context command."""

import sys
from clickup_framework import get_context_manager


def set_current_command(args):
    """Set current resource context."""
    context = get_context_manager()

    resource_type = args.resource_type.lower()
    resource_id = args.resource_id

    # Map resource types to setter methods
    setters = {
        'task': context.set_current_task,
        'list': context.set_current_list,
        'space': context.set_current_space,
        'folder': context.set_current_folder,
        'workspace': context.set_current_workspace,
        'team': context.set_current_workspace,  # Alias
        'assignee': lambda aid: context.set_default_assignee(int(aid)),
        'token': context.set_api_token,
    }

    setter = setters.get(resource_type)
    if not setter:
        print(f"Error: Unknown resource type '{resource_type}'", file=sys.stderr)
        print(f"Valid types: {', '.join(setters.keys())}", file=sys.stderr)
        sys.exit(1)

    try:
        setter(resource_id)
        # Mask token in output for security
        if resource_type == 'token':
            masked_token = f"{resource_id[:15]}...{resource_id[-4:]}" if len(resource_id) > 20 else "********"
            print(f"✓ API token validated and saved successfully: {masked_token}")
        else:
            print(f"✓ Set current {resource_type} to: {resource_id}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def register_command(subparsers, add_common_args=None):
    """Register the set_current command with argparse."""
    parser = subparsers.add_parser(
        'set_current',
        aliases=['set'],
        help='Set current resource context',
        description='Set current resource context for use with "current" keyword'
    )
    parser.add_argument(
        'resource_type',
        choices=['task', 'list', 'space', 'folder', 'workspace', 'team', 'assignee', 'token'],
        help='Type of resource to set as current'
    )
    parser.add_argument('resource_id', help='ID/value of the resource (API token for token type)')
    parser.set_defaults(func=set_current_command)
