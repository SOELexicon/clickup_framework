"""ANSI output configuration command."""

from clickup_framework.commands.base_command import BaseCommand


class AnsiCommand(BaseCommand):
    """
    ANSI color output configuration command using BaseCommand.

    Enables, disables, or checks the status of ANSI color output.
    """

    def execute(self):
        """Execute the ANSI configuration command."""
        if self.args.action == 'enable':
            self.context.set_ansi_output(True)
            self.print_success("ANSI color output enabled")
        elif self.args.action == 'disable':
            self.context.set_ansi_output(False)
            self.print("✓ ANSI color output disabled")
        elif self.args.action == 'status':
            enabled = self.context.get_ansi_output()
            status = "enabled" if enabled else "disabled"
            self.print(f"ANSI color output is currently: {status}")


def ansi_command(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = AnsiCommand(args, command_name='ansi')
    command.execute()


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
