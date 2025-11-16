"""Git stash command - wrapper for git stash operations."""

import subprocess
import sys


def stash_command(args):
    """Execute git stash operations."""
    # Build git stash command
    cmd = ['git', 'stash']

    # Add subcommand if provided
    if args.subcommand:
        cmd.append(args.subcommand)

    # Add additional arguments
    if args.args:
        cmd.extend(args.args)

    # Execute git stash
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    # Print output
    if result.stdout:
        print(result.stdout.strip())

    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)

    # Exit with same code as git stash
    sys.exit(result.returncode)


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
