"""ANSI output configuration command."""

from clickup_framework import get_context_manager


def ansi_command(args):
    """Enable or disable ANSI color output."""
    context = get_context_manager()

    if args.action == 'enable':
        context.set_ansi_output(True)
        print("✓ ANSI color output enabled")
    elif args.action == 'disable':
        context.set_ansi_output(False)
        print("✓ ANSI color output disabled")
    elif args.action == 'status':
        enabled = context.get_ansi_output()
        status = "enabled" if enabled else "disabled"
        print(f"ANSI color output is currently: {status}")


def register_command(subparsers, add_common_args=None):
    """Register the ansi command with argparse."""
    parser = subparsers.add_parser(
        'ansi',
        help='Enable or disable ANSI color output',
        description='Configure ANSI color output for the CLI'
    )
    parser.add_argument(
        'action',
        choices=['enable', 'disable', 'status'],
        help='Action to perform (enable/disable/status)'
    )
    parser.set_defaults(func=ansi_command)
