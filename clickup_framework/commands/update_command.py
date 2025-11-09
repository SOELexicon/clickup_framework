"""Update command for ClickUp Framework CLI."""

import sys
import os
import platform
import subprocess
from pathlib import Path
from clickup_framework import get_context_manager
from clickup_framework.utils.colors import colorize, TextColor, TextStyle
from clickup_framework.utils.animations import ANSIAnimations


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
        # On Windows, look for python.exe in Scripts parent dir
        if 'Scripts' in script_dir or 'scripts' in script_dir:
            parent_dir = os.path.dirname(script_dir)
            python_exe = os.path.join(parent_dir, 'python.exe')
            if os.path.isfile(python_exe):
                return python_exe

        # Also check if we can find python.exe by looking at the script
        # On Windows, cum might be cum.exe, and we need to find python.exe
        # Try the parent directory
        parent_dir = os.path.dirname(script_dir)
        python_exe = os.path.join(parent_dir, 'python.exe')
        if os.path.isfile(python_exe):
            return python_exe

        # As a last resort on Windows, try to use 'python' from PATH
        # This will find the python that would be used in the same environment
        try:
            result = subprocess.run(
                ['python', '--version'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return 'python'
        except Exception:
            pass
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
                    print(colorize("  Pulling latest changes...", TextColor.BRIGHT_YELLOW))
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
                        print(colorize("  ✓ Updated source code", TextColor.BRIGHT_GREEN))
                    else:
                        print("  ✓ Updated source code")
            except subprocess.CalledProcessError as e:
                print(colorize(f"  ⚠ Could not update source: {e}", TextColor.YELLOW) if use_color else f"  ⚠ Could not update source: {e}")

        # Reinstall editable
        try:
            if use_color:
                print(colorize("  Reinstalling package...", TextColor.BRIGHT_YELLOW))
            else:
                print("  Reinstalling package...")

            subprocess.run(
                [python_path, '-m', 'pip', 'install', '-e', editable_location, '--force-reinstall', '--no-deps'],
                capture_output=True,
                text=True,
                check=True
            )

            if use_color:
                print(colorize("  ✓ Successfully reinstalled", TextColor.BRIGHT_GREEN))
            else:
                print("  ✓ Successfully reinstalled")
            return True
        except subprocess.CalledProcessError as e:
            print(colorize(f"  ✗ Failed to reinstall: {e}", TextColor.RED) if use_color else f"  ✗ Failed to reinstall: {e}", file=sys.stderr)
            return False
    else:
        # For regular installs, reinstall from git
        if use_color:
            print(colorize("  Regular install - reinstalling from git...", TextColor.BRIGHT_YELLOW))
        else:
            print("  Regular install - reinstalling from git...")

        try:
            subprocess.run(
                [python_path, '-m', 'pip', 'install',
                 'git+https://github.com/SOELexicon/clickup_framework.git',
                 '--upgrade', '--force-reinstall'],
                capture_output=True,
                text=True,
                check=True
            )

            if use_color:
                print(colorize("  ✓ Successfully reinstalled from git", TextColor.BRIGHT_GREEN))
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
