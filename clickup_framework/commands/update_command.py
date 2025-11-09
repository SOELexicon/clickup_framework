"""Update command for ClickUp Framework CLI."""

import sys
import subprocess
from clickup_framework import get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations


def update_cum_command(args):
    """Update the cum tool from git and reinstall."""
    from clickup_framework import __version__

    context = get_context_manager()
    use_color = context.get_ansi_output()

    # Show current version
    if use_color:
        print(colorize(f"Current version: {__version__}", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
    else:
        print(f"Current version: {__version__}")
    print()

    # Get the repository root
    try:
        repo_root = subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            stderr=subprocess.PIPE,
            text=True
        ).strip()
    except subprocess.CalledProcessError:
        print("Error: Not in a git repository. Cannot update.", file=sys.stderr)
        sys.exit(1)

    # Check current branch
    try:
        current_branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=repo_root,
            stderr=subprocess.PIPE,
            text=True
        ).strip()

        if use_color:
            print(colorize(f"Current branch: {current_branch}", TextColor.BRIGHT_WHITE))
        else:
            print(f"Current branch: {current_branch}")
    except subprocess.CalledProcessError:
        pass

    # Fetch latest changes
    if use_color:
        print(colorize("Fetching latest changes from git...", TextColor.BRIGHT_YELLOW))
    else:
        print("Fetching latest changes from git...")

    try:
        # Fetch all branches
        subprocess.run(
            ['git', 'fetch', '--all'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )

        # Determine the main branch name (master or main)
        main_branch = None
        for branch_name in ['main', 'master']:
            result = subprocess.run(
                ['git', 'rev-parse', '--verify', f'origin/{branch_name}'],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                main_branch = branch_name
                break

        if main_branch:
            if use_color:
                print(colorize(f"Pulling from origin/{main_branch}...", TextColor.BRIGHT_YELLOW))
            else:
                print(f"Pulling from origin/{main_branch}...")

            # Pull from the main branch
            result = subprocess.run(
                ['git', 'pull', 'origin', main_branch],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout:
                print(result.stdout)

            if "Already up to date" in result.stdout or "Already up-to-date" in result.stdout:
                if use_color:
                    print(colorize("✓ Repository is already up to date", TextColor.BRIGHT_GREEN))
                else:
                    print("✓ Repository is already up to date")
            else:
                if use_color:
                    print(colorize("✓ Successfully pulled latest changes", TextColor.BRIGHT_GREEN))
                else:
                    print("✓ Successfully pulled latest changes")
        else:
            # No main/master branch, just fetch is enough
            if use_color:
                print(colorize("✓ Fetched latest changes", TextColor.BRIGHT_GREEN))
            else:
                print("✓ Fetched latest changes")

    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not update from git: {e.stderr}", file=sys.stderr)
        print("Continuing with reinstall...", file=sys.stderr)

    print()

    # Force reinstall
    if use_color:
        print(colorize("Reinstalling package...", TextColor.BRIGHT_YELLOW))
    else:
        print("Reinstalling package...")

    try:
        result = subprocess.run(
            ['pip', 'install', '-e', repo_root, '--force-reinstall', '--no-deps'],
            capture_output=True,
            text=True,
            check=True
        )

        # Show relevant output
        if result.stdout:
            # Filter to show only important lines
            for line in result.stdout.split('\n'):
                if 'Successfully installed' in line or 'clickup-framework' in line.lower():
                    print(line)

        if use_color:
            print(colorize("✓ Package reinstalled successfully", TextColor.BRIGHT_GREEN))
        else:
            print("✓ Package reinstalled successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error reinstalling package: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    print()

    # Import the updated version
    import importlib
    import clickup_framework
    importlib.reload(clickup_framework)
    from clickup_framework import __version__ as new_version

    if use_color:
        success_msg = ANSIAnimations.success_message(f"Update complete! Version: {new_version}")
        print(success_msg)
    else:
        print(f"Update complete! Version: {new_version}")


def register_command(subparsers):
    """Register update command."""
    # Update command
    update_parser = subparsers.add_parser('update',
                                          help='Update components of the cum tool')
    update_subparsers = update_parser.add_subparsers(dest='update_target', help='Component to update')

    # Update cum (self-update)
    update_cum_parser = update_subparsers.add_parser('cum',
                                                     help='Update cum tool from git and reinstall')
    update_cum_parser.set_defaults(func=update_cum_command)
