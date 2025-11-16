"""Git pull command with rebase."""

import subprocess
import sys
from pathlib import Path


def pull_command(args):
    """Execute git pull --rebase in current directory."""
    # Check if in Git repository
    git_dir = Path('.git')
    if not git_dir.exists():
        print("Error: Not in a Git repository", file=sys.stderr)
        sys.exit(1)

    # Execute git pull --rebase
    result = subprocess.run(
        ['git', 'pull', '--rebase'],
        capture_output=False,  # Show output in real-time
        text=True
    )

    # Exit with Git's exit code
    sys.exit(result.returncode)


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
