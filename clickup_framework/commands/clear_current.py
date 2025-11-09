"""Clear current context command."""

import sys
from clickup_framework import get_context_manager


def clear_current_command(args):
    """Clear current resource context."""
    context = get_context_manager()

    if args.resource_type:
        resource_type = args.resource_type.lower()

        # Map resource types to clear methods
        clearers = {
            'task': context.clear_current_task,
            'list': context.clear_current_list,
            'space': context.clear_current_space,
            'folder': context.clear_current_folder,
            'workspace': context.clear_current_workspace,
            'team': context.clear_current_workspace,  # Alias
            'token': context.clear_api_token,
        }

        clearer = clearers.get(resource_type)
        if not clearer:
            print(f"Error: Unknown resource type '{resource_type}'", file=sys.stderr)
            print(f"Valid types: {', '.join(clearers.keys())}", file=sys.stderr)
            sys.exit(1)

        clearer()
        print(f"✓ Cleared current {resource_type}")
    else:
        # Clear all context
        context.clear_all()
        print("✓ Cleared all context")


def register_command(subparsers, add_common_args=None):
    """Register the clear_current command with argparse."""
    parser = subparsers.add_parser(
        'clear_current',
        help='Clear current resource context',
        description='Clear current resource context or all context'
    )
    parser.add_argument(
        'resource_type',
        nargs='?',
        choices=['task', 'list', 'space', 'folder', 'workspace', 'team', 'assignee', 'token'],
        help='Type of resource to clear (omit to clear all)'
    )
    parser.set_defaults(func=clear_current_command)
