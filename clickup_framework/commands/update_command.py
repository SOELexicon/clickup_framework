"""Update command for ClickUp Framework CLI."""

import sys
import os
import platform
import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple
from clickup_framework import get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations

# Ensure UTF-8 encoding for Windows
if platform.system() == 'Windows':
    try:
        # Try to reconfigure stdout/stderr to use UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass  # If reconfigure fails, continue anyway


def find_all_cum_instances():
    """Find all cum executable instances on the system."""
    instances = []
    system = platform.system()

    try:
        if system == "Windows":
            # Use where.exe on Windows
            result = subprocess.run(
                ['where.exe', 'cum'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                instances = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        else:
            # Use which -a on Linux/Mac
            result = subprocess.run(
                ['which', '-a', 'cum'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                instances = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

            # Also try whereis as a fallback
            if not instances:
                result = subprocess.run(
                    ['whereis', 'cum'],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    # whereis output format: "cum: /path/to/cum /other/path"
                    parts = result.stdout.strip().split(':')
                    if len(parts) > 1:
                        paths = parts[1].strip().split()
                        instances = [p for p in paths if os.path.isfile(p)]
    except Exception as e:
        print(f"Warning: Error finding cum instances: {e}", file=sys.stderr)

    return instances


def get_python_from_script(script_path):
    """Extract the Python interpreter path from a script's shebang."""
    script_dir = os.path.dirname(script_path)

    # On Windows, try to find python.exe in the expected locations first
    if platform.system() == "Windows":
        # Check multiple parent directory levels for python.exe
        # This handles cases like C:\Python\Scr\bin\cum.exe -> C:\Python\python.exe
        current_dir = script_dir
        for _ in range(4):  # Check up to 4 levels up
            parent_dir = os.path.dirname(current_dir)
            if not parent_dir or parent_dir == current_dir:
                break

            # Check for python.exe and python3.exe in parent directory
            for python_name in ['python.exe', 'python3.exe']:
                python_exe = os.path.join(parent_dir, python_name)
                if os.path.isfile(python_exe):
                    return python_exe

            current_dir = parent_dir

        # Also check in same directory as cum.exe
        for python_name in ['python.exe', 'python3.exe']:
            python_exe = os.path.join(script_dir, python_name)
            if os.path.isfile(python_exe):
                return python_exe

        # As a last resort on Windows, try to find python in PATH using where.exe
        # Try multiple Python command names
        for python_cmd in ['py', 'python', 'python3']:
            try:
                # First verify the command works
                result = subprocess.run(
                    [python_cmd, '--version'],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    # Now get the actual path using where.exe
                    where_result = subprocess.run(
                        ['where.exe', python_cmd],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    if where_result.returncode == 0:
                        # Get the first path from the output
                        python_path = where_result.stdout.strip().split('\n')[0].strip()
                        if os.path.isfile(python_path):
                            return python_path
            except Exception:
                continue
    else:
        # On Unix, try to read the shebang
        try:
            with open(script_path, 'r') as f:
                first_line = f.readline().strip()
                if first_line.startswith('#!'):
                    python_path = first_line[2:].strip()
                    # Handle shebangs like "#!/usr/bin/env python"
                    if 'env' in python_path:
                        parts = python_path.split()
                        if len(parts) > 1:
                            python_path = parts[-1]
                    return python_path
        except Exception:
            pass

        # Fallback: try to find python in bin parent dir
        if script_dir.endswith('/bin'):
            parent_dir = os.path.dirname(script_dir)
            python_path = os.path.join(parent_dir, 'bin', 'python')
            if os.path.isfile(python_path):
                return python_path

    return None


def get_package_info(python_path):
    """Get package installation info for a specific Python environment."""
    try:
        # Try using the python -m pip approach
        result = subprocess.run(
            [python_path, '-m', 'pip', 'show', 'clickup-framework'],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            info = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()
            return info
    except Exception:
        pass

    return None


def show_humorous_progress(message: str, duration: float = 1.5, use_color: bool = True):
    """Display a humorous progress bar similar to jizz command."""
    import time

    if not use_color:
        print(f"  {message}...")
        time.sleep(duration)
        return

    bar_length = 40
    colored_msg = colorize(f"  {message}", TextColor.BRIGHT_MAGENTA, TextStyle.BOLD)

    for i in range(bar_length + 1):
        percent = int((i / bar_length) * 100)
        filled = '█' * i
        empty = '░' * (bar_length - i)

        # Color progression
        if percent < 33:
            color = TextColor.BRIGHT_CYAN
        elif percent < 66:
            color = TextColor.BRIGHT_MAGENTA
        else:
            color = TextColor.BRIGHT_YELLOW

        colored_filled = colorize(filled, color)
        bar = f"{colored_filled}{empty}"

        print(f"\r{colored_msg} [{bar}] {percent}%", end='', flush=True)
        time.sleep(duration / bar_length)

    print()


def update_instance(script_path, python_path, use_color):
    """Update a single cum instance."""
    print()
    if use_color:
        print(colorize(f"Updating instance: {script_path}", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
        print(colorize(f"Python: {python_path}", TextColor.WHITE))
    else:
        print(f"Updating instance: {script_path}")
        print(f"Python: {python_path}")

    # Get package info
    pkg_info = get_package_info(python_path)
    if not pkg_info:
        print(colorize("  ⚠ Package not found in this environment", TextColor.YELLOW) if use_color else "  ⚠ Package not found in this environment")
        return False

    location = pkg_info.get('Location', '')
    editable_location = pkg_info.get('Editable project location', '')

    # Check if it's an editable install
    is_editable = bool(editable_location)

    if is_editable:
        # For editable installs, try to update the source
        if use_color:
            print(colorize(f"  Editable install at: {editable_location}", TextColor.WHITE))
        else:
            print(f"  Editable install at: {editable_location}")

        # Try to update git repo if it exists
        if os.path.isdir(os.path.join(editable_location, '.git')):
            try:
                if use_color:
                    print(colorize("  💦 Pulling latest changes...", TextColor.BRIGHT_YELLOW))
                else:
                    print("  Pulling latest changes...")

                # Fetch and pull
                subprocess.run(
                    ['git', 'fetch', '--all'],
                    cwd=editable_location,
                    capture_output=True,
                    check=True
                )

                # Determine main branch
                main_branch = None
                for branch_name in ['main', 'master']:
                    result = subprocess.run(
                        ['git', 'rev-parse', '--verify', f'origin/{branch_name}'],
                        cwd=editable_location,
                        capture_output=True
                    )
                    if result.returncode == 0:
                        main_branch = branch_name
                        break

                if main_branch:
                    result = subprocess.run(
                        ['git', 'pull', 'origin', main_branch],
                        cwd=editable_location,
                        capture_output=True,
                        text=True,
                        check=True
                    )

                    if use_color:
                        print(ANSIAnimations.success_message("  Updated source code"))
                    else:
                        print("  ✓ Updated source code")
            except subprocess.CalledProcessError as e:
                print(colorize(f"  ⚠ Could not update source: {e}", TextColor.YELLOW) if use_color else f"  ⚠ Could not update source: {e}")

        # Reinstall editable
        try:
            show_humorous_progress("💪 Pumping up the package (reinstalling)", 1.2, use_color)

            # Run pip without capturing output so user sees real progress
            result = subprocess.run(
                [python_path, '-m', 'pip', 'install', '-e', editable_location, '--force-reinstall', '--no-deps'],
                check=True
            )

            if use_color:
                print(ANSIAnimations.success_message("  Successfully reinstalled"))
            else:
                print("  ✓ Successfully reinstalled")
            return True
        except subprocess.CalledProcessError as e:
            print(colorize(f"  ✗ Failed to reinstall: {e}", TextColor.RED) if use_color else f"  ✗ Failed to reinstall: {e}", file=sys.stderr)
            return False
    else:
        # For regular installs, reinstall from git
        if use_color:
            print(colorize("  🍆 Regular install - time to get fresh from the source...", TextColor.BRIGHT_YELLOW))
        else:
            print("  Regular install - reinstalling from git...")

        try:
            show_humorous_progress("💦 Downloading hot new package from git", 1.5, use_color)

            # Run pip without capturing output so user sees real progress
            result = subprocess.run(
                [python_path, '-m', 'pip', 'install',
                 'git+https://github.com/SOELexicon/clickup_framework.git',
                 '--upgrade', '--force-reinstall'],
                check=True
            )

            if use_color:
                print(ANSIAnimations.success_message("  Successfully reinstalled from git"))
            else:
                print("  ✓ Successfully reinstalled from git")
            return True
        except subprocess.CalledProcessError as e:
            print(colorize(f"  ✗ Failed to reinstall: {e}", TextColor.RED) if use_color else f"  ✗ Failed to reinstall: {e}", file=sys.stderr)
            return False


def update_cum_command(args):
    """Update the cum tool in all Python environments where it's installed."""
    from clickup_framework import __version__

    context = get_context_manager()
    use_color = context.get_ansi_output()

    # Show current version
    if use_color:
        print(colorize(f"Current version: {__version__}", TextColor.BRIGHT_CYAN, TextStyle.BOLD))
    else:
        print(f"Current version: {__version__}")
    print()

    # Find all cum instances
    if use_color:
        print(colorize("Searching for all cum instances on the system...", TextColor.BRIGHT_YELLOW))
    else:
        print("Searching for all cum instances on the system...")

    instances = find_all_cum_instances()

    if not instances:
        print(colorize("No cum instances found!", TextColor.RED) if use_color else "No cum instances found!", file=sys.stderr)
        sys.exit(1)

    if use_color:
        print(colorize(f"Found {len(instances)} instance(s):", TextColor.BRIGHT_GREEN))
    else:
        print(f"Found {len(instances)} instance(s):")

    for instance in instances:
        print(f"  • {instance}")

    # Update each instance
    updated_count = 0
    failed_count = 0

    for instance in instances:
        python_path = get_python_from_script(instance)

        if not python_path:
            print()
            if use_color:
                print(colorize(f"⚠ Could not determine Python for: {instance}", TextColor.YELLOW))
            else:
                print(f"⚠ Could not determine Python for: {instance}")
            failed_count += 1
            continue

        # Verify python exists
        if not os.path.isfile(python_path):
            print()
            if use_color:
                print(colorize(f"⚠ Python not found at: {python_path}", TextColor.YELLOW))
            else:
                print(f"⚠ Python not found at: {python_path}")
            failed_count += 1
            continue

        if update_instance(instance, python_path, use_color):
            updated_count += 1
        else:
            failed_count += 1

    # Summary
    print()
    print("=" * 60)
    if use_color:
        if updated_count > 0:
            print(colorize(f"✓ Successfully updated {updated_count} instance(s)", TextColor.BRIGHT_GREEN))
        if failed_count > 0:
            print(colorize(f"✗ Failed to update {failed_count} instance(s)", TextColor.RED))
    else:
        if updated_count > 0:
            print(f"✓ Successfully updated {updated_count} instance(s)")
        if failed_count > 0:
            print(f"✗ Failed to update {failed_count} instance(s)")

    if updated_count > 0:
        # Try to get the new version
        try:
            import importlib
            import clickup_framework
            importlib.reload(clickup_framework)
            from clickup_framework import __version__ as new_version

            print()
            if use_color:
                success_msg = ANSIAnimations.success_message(f"Update complete! Version: {new_version}")
                print(success_msg)
            else:
                print(f"Update complete! Version: {new_version}")
        except Exception:
            if use_color:
                print(colorize("Update complete!", TextColor.BRIGHT_GREEN))
            else:
                print("Update complete!")

    sys.exit(0 if failed_count == 0 else 1)


# ============================================================================
# Version Bump Functions (from scripts/bump_version.py)
# ============================================================================

def run_git_command(cmd: list, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    return subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        check=False
    )


def get_latest_tag() -> Optional[str]:
    """Get the latest version tag from git."""
    result = run_git_command(['git', 'tag', '-l', '--sort=-v:refname'])

    if result.returncode != 0 or not result.stdout.strip():
        return None

    # Get the first tag (most recent)
    tags = result.stdout.strip().split('\n')
    for tag in tags:
        # Match semantic versioning pattern
        if re.match(r'^\d+\.\d+\.\d+', tag):
            return tag

    return None


def parse_version(version_str: str) -> Tuple[int, int, int, str]:
    """
    Parse a version string into components.
    Returns (major, minor, patch, suffix)
    """
    # Remove 'v' prefix if present
    version_str = version_str.lstrip('v')

    # Match version pattern with optional suffix
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)(.*)', version_str)

    if not match:
        raise ValueError(f"Invalid version format: {version_str}")

    major, minor, patch, suffix = match.groups()
    return int(major), int(minor), int(patch), suffix or ''


def format_version(major: int, minor: int, patch: int, suffix: str = '') -> str:
    """Format version components into a version string."""
    return f"{major}.{minor}.{patch}{suffix}"


def increment_version(version_str: str, increment_type: str) -> str:
    """
    Increment a version string.

    Args:
        version_str: Current version (e.g., "1.2.3")
        increment_type: One of "major", "minor", "patch"

    Returns:
        New version string
    """
    major, minor, patch, suffix = parse_version(version_str)

    if increment_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif increment_type == 'minor':
        minor += 1
        patch = 0
    elif increment_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Invalid increment type: {increment_type}")

    # Remove suffix for incremented versions
    return format_version(major, minor, patch)


def create_and_push_tag(version: str, push: bool = True, use_color: bool = True) -> bool:
    """
    Create a git tag and optionally push it to origin.

    Args:
        version: Version string (e.g., "1.0.0")
        push: Whether to push the tag to origin
        use_color: Whether to use colored output

    Returns:
        True if successful, False otherwise
    """
    tag_name = f"v{version}" if not version.startswith('v') else version

    # Create the tag
    print()
    msg = f"Creating tag: {tag_name}"
    if use_color:
        print(colorize(msg, TextColor.BRIGHT_YELLOW))
    else:
        print(msg)

    result = run_git_command(['git', 'tag', '-a', tag_name, '-m', f'Release {version}'])

    if result.returncode != 0:
        error_msg = f"Error creating tag: {result.stderr}"
        if use_color:
            print(colorize(error_msg, TextColor.RED), file=sys.stderr)
        else:
            print(error_msg, file=sys.stderr)
        return False

    success_msg = f"✓ Tag {tag_name} created successfully"
    if use_color:
        print(colorize(success_msg, TextColor.BRIGHT_GREEN))
    else:
        print(success_msg)

    if push:
        # Push the tag to origin
        msg = "Pushing tag to origin..."
        if use_color:
            print(colorize(msg, TextColor.BRIGHT_YELLOW))
        else:
            print(msg)

        result = run_git_command(['git', 'push', 'origin', tag_name])

        if result.returncode != 0:
            error_msg = f"Error pushing tag: {result.stderr}"
            if use_color:
                print(colorize(error_msg, TextColor.RED), file=sys.stderr)
                print(colorize(f"You can manually push with: git push origin {tag_name}", TextColor.YELLOW))
            else:
                print(error_msg, file=sys.stderr)
                print(f"You can manually push with: git push origin {tag_name}")
            return False

        success_msg = f"✓ Tag {tag_name} pushed to origin"
        if use_color:
            print(colorize(success_msg, TextColor.BRIGHT_GREEN))
        else:
            print(success_msg)

    return True


def interactive_bump(use_color: bool = True) -> Optional[str]:
    """Interactive version bump - prompts user for increment type."""
    current_version = get_latest_tag()

    print("=" * 60)
    title = "Version Bump Tool"
    if use_color:
        print(colorize(title, TextColor.BRIGHT_CYAN, TextStyle.BOLD))
    else:
        print(title)
    print("=" * 60)
    print()

    if current_version:
        msg = f"Current version: {current_version}"
        if use_color:
            print(colorize(msg, TextColor.BRIGHT_WHITE))
        else:
            print(msg)
    else:
        msg = "No version tags found. Starting from 0.0.0"
        if use_color:
            print(colorize(msg, TextColor.YELLOW))
        else:
            print(msg)
        current_version = "0.0.0"

    print()
    print("How would you like to increment the version?")
    print()

    major, minor, patch, _ = parse_version(current_version)

    option1 = f"  1. Major (breaking changes)     -> {format_version(major + 1, 0, 0)}"
    option2 = f"  2. Minor (new features)          -> {format_version(major, minor + 1, 0)}"
    option3 = f"  3. Patch (bug fixes)             -> {format_version(major, minor, patch + 1)}"

    if use_color:
        print(colorize(option1, TextColor.BRIGHT_WHITE))
        print(colorize(option2, TextColor.BRIGHT_WHITE))
        print(colorize(option3, TextColor.BRIGHT_WHITE))
    else:
        print(option1)
        print(option2)
        print(option3)

    print("  4. Custom version")
    print("  5. Cancel")
    print()

    choice = input("Enter your choice (1-5): ").strip()

    if choice == '1':
        new_version = increment_version(current_version, 'major')
    elif choice == '2':
        new_version = increment_version(current_version, 'minor')
    elif choice == '3':
        new_version = increment_version(current_version, 'patch')
    elif choice == '4':
        custom = input("Enter custom version (e.g., 1.0.0-alpha): ").strip()
        try:
            # Validate the version
            parse_version(custom)
            new_version = custom
        except ValueError as e:
            error_msg = f"Error: {e}"
            if use_color:
                print(colorize(error_msg, TextColor.RED), file=sys.stderr)
            else:
                print(error_msg, file=sys.stderr)
            return None
    elif choice == '5':
        if use_color:
            print(colorize("Cancelled.", TextColor.YELLOW))
        else:
            print("Cancelled.")
        return None
    else:
        error_msg = "Invalid choice."
        if use_color:
            print(colorize(error_msg, TextColor.RED), file=sys.stderr)
        else:
            print(error_msg, file=sys.stderr)
        return None

    print()
    msg = f"New version will be: {new_version}"
    if use_color:
        print(colorize(msg, TextColor.BRIGHT_CYAN, TextStyle.BOLD))
    else:
        print(msg)

    confirm = input("Confirm? (y/n): ").strip().lower()

    if confirm != 'y':
        if use_color:
            print(colorize("Cancelled.", TextColor.YELLOW))
        else:
            print("Cancelled.")
        return None

    return new_version


def update_version_command(args):
    """Update the project version by creating a new git tag."""
    context = get_context_manager()
    use_color = context.get_ansi_output()

    # Check if git is available
    try:
        git_check = subprocess.run(
            ['git', '--version'],
            capture_output=True,
            text=True,
            check=False
        )
        if git_check.returncode != 0:
            error_msg = "Error: git command not found. Please install git and try again."
            if use_color:
                print(colorize(error_msg, TextColor.RED), file=sys.stderr)
            else:
                print(error_msg, file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)
    except FileNotFoundError:
        error_msg = "Error: git command not found. Please install git and try again."
        if use_color:
            print(colorize(error_msg, TextColor.RED), file=sys.stderr)
        else:
            print(error_msg, file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)

    # Check if we're in a git repository
    result = run_git_command(['git', 'rev-parse', '--git-dir'])
    if result.returncode != 0:
        error_msg = "Error: Not in a git repository"
        if use_color:
            print(colorize(error_msg, TextColor.RED), file=sys.stderr)
            print(colorize("This command must be run from within the clickup_framework git repository.", TextColor.YELLOW), file=sys.stderr)
        else:
            print(error_msg, file=sys.stderr)
            print("This command must be run from within the clickup_framework git repository.", file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)

    # Determine new version
    new_version = None

    # Handle quick increment flags
    if hasattr(args, 'major') and args.major:
        increment_type = 'major'
    elif hasattr(args, 'minor') and args.minor:
        increment_type = 'minor'
    elif hasattr(args, 'patch') and args.patch:
        increment_type = 'patch'
    else:
        increment_type = None

    # Handle specific version argument
    if hasattr(args, 'version') and args.version:
        try:
            parse_version(args.version)
            new_version = args.version
            msg = f"Setting version to: {new_version}"
            if use_color:
                print(colorize(msg, TextColor.BRIGHT_CYAN))
            else:
                print(msg)
        except ValueError as e:
            error_msg = f"Error: {e}"
            if use_color:
                print(colorize(error_msg, TextColor.RED), file=sys.stderr)
            else:
                print(error_msg, file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)
    elif increment_type:
        current_version = get_latest_tag()
        if not current_version:
            msg = "No version tags found. Creating initial version 0.1.0"
            if use_color:
                print(colorize(msg, TextColor.YELLOW))
            else:
                print(msg)
            new_version = "0.1.0"
        else:
            new_version = increment_version(current_version, increment_type)
            msg = f"Bumping {increment_type} version: {current_version} -> {new_version}"
            if use_color:
                print(colorize(msg, TextColor.BRIGHT_CYAN))
            else:
                print(msg)
    else:
        # Interactive mode
        if use_color:
            print(colorize("No version specified. Starting interactive mode...", TextColor.BRIGHT_YELLOW))
        else:
            print("No version specified. Starting interactive mode...")
        print()
        sys.stdout.flush()
        new_version = interactive_bump(use_color)

    if not new_version:
        sys.exit(1)

    # Check for --no-push flag
    no_push = hasattr(args, 'no_push') and args.no_push

    # Create and push the tag
    success = create_and_push_tag(new_version, push=not no_push, use_color=use_color)

    if success:
        print()
        print("=" * 60)
        success_msg = f"✓ Version {new_version} tagged successfully!"
        if use_color:
            print(colorize(success_msg, TextColor.BRIGHT_GREEN, TextStyle.BOLD))
        else:
            print(success_msg)

        if not no_push:
            push_msg = "✓ Tag pushed to origin"
            if use_color:
                print(colorize(push_msg, TextColor.BRIGHT_GREEN))
            else:
                print(push_msg)

        print()
        update_msg = "Run 'cum update cum' to update to the new version."
        if use_color:
            print(colorize(update_msg, TextColor.BRIGHT_YELLOW))
        else:
            print(update_msg)
        print("=" * 60)
        sys.exit(0)
    else:
        sys.exit(1)


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

    # Update version (bump version)
    update_version_parser = update_subparsers.add_parser('version',
                                                         help='Bump project version and create git tag')
    update_version_parser.add_argument(
        'version',
        nargs='?',
        help='Specific version to set (e.g., 1.0.0)'
    )
    update_version_parser.add_argument(
        '--major',
        action='store_true',
        help='Increment major version'
    )
    update_version_parser.add_argument(
        '--minor',
        action='store_true',
        help='Increment minor version'
    )
    update_version_parser.add_argument(
        '--patch',
        action='store_true',
        help='Increment patch version'
    )
    update_version_parser.add_argument(
        '--no-push',
        action='store_true',
        help='Create tag locally but do not push to origin'
    )
    update_version_parser.set_defaults(func=update_version_command)
