"""Git stash command - wrapper for git stash operations."""

import subprocess
from clickup_framework.commands.base_command import BaseCommand


class StashCommand(BaseCommand):
    """
    Git Stash Command using BaseCommand.
    """

    def execute(self):
        """Execute git stash operations."""
        # Build git stash command
        cmd = ['git', 'stash']

        # Add subcommand if provided
        if self.args.subcommand:
            cmd.append(self.args.subcommand)

        # Add additional arguments
        if self.args.args:
            cmd.extend(self.args.args)

        # Execute git stash
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        # Print output
        if result.stdout:
            self.print(result.stdout.strip())

        if result.stderr:
            self.print_error(result.stderr.strip())

        # Exit with same code as git stash
        if result.returncode != 0:
            exit(result.returncode)


def stash_command(args):
    """
    Command function wrapper for backward compatibility.

    This function maintains the existing function-based API while
    using the BaseCommand class internally.
    """
    command = StashCommand(args, command_name='stash')
    command.execute()


def register_command(subparsers, add_common_args=None):
    """Register the stash command."""
    parser = subparsers.add_parser(
        'stash',
        help='Wrapper for git stash operations',
        description='Execute git stash commands to save and restore uncommitted changes.',
        epilog='''Tips:
  • Save changes: cum stash push -m "description"
  • List stashes: cum stash list
  • Apply latest: cum stash pop
  • Apply specific: cum stash apply stash@{0}
  • Clear all stashes: cum stash clear
  • Passes all args directly to git stash'''
    )

    parser.add_argument(
        'subcommand',
        nargs='?',
        help='Stash subcommand (push, pop, list, apply, drop, clear, etc.)'
    )

    parser.add_argument(
        'args',
        nargs='*',
        help='Additional arguments to pass to git stash'
    )

    parser.set_defaults(func=stash_command)
