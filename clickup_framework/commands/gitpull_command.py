"""Git pull command with rebase."""

import subprocess
from pathlib import Path
from clickup_framework.commands.base_command import BaseCommand


class PullCommand(BaseCommand):
    """Execute git pull --rebase in current directory."""

    def execute(self):
        """Execute the pull command."""
        # Check if in Git repository
        git_dir = Path('.git')
        if not git_dir.exists():
            self.error("Not in a Git repository")

        # Execute git pull --rebase
        result = subprocess.run(
            ['git', 'pull', '--rebase'],
            capture_output=False,  # Show output in real-time
            text=True
        )

        # Exit with Git's exit code
        import sys
        sys.exit(result.returncode)


def pull_command(args):
    """Command wrapper for backward compatibility."""
    command = PullCommand(args, command_name='pull')
    command.execute()


def register_command(subparsers, add_common_args=None):
    """Register the pull command."""
    parser = subparsers.add_parser(
        'pull',
        help='Execute git pull --rebase',
        description='Pull latest changes with rebase in current Git repository',
        epilog='''Tips:
  • Update current repo: cum pull (runs git pull --rebase)
  • Uses rebase instead of merge for cleaner history
  • Run before starting new work to stay current
  • Resolves conflicts during rebase if needed
  • Alternative to 'git pull --rebase' shortcut'''
    )
    parser.set_defaults(func=pull_command)
