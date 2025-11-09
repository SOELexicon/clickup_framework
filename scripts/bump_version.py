#!/usr/bin/env python3
"""
Version Bump Script

This script helps manage version tags for the clickup_framework project.
It can automatically increment version numbers (major, minor, patch) or
set a specific version, then creates and pushes the tag to origin.

Usage:
    # Interactive mode - prompts for version increment
    python scripts/bump_version.py

    # Set specific version
    python scripts/bump_version.py 1.0.0

    # Quick increment without confirmation
    python scripts/bump_version.py --patch
    python scripts/bump_version.py --minor
    python scripts/bump_version.py --major
"""

import subprocess
import sys
import re
import argparse
from typing import Optional, Tuple


def run_command(cmd: list, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        check=False
    )


def get_latest_tag() -> Optional[str]:
    """Get the latest version tag from git."""
    result = run_command(['git', 'tag', '-l', '--sort=-v:refname'])

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


def create_and_push_tag(version: str, push: bool = True) -> bool:
    """
    Create a git tag and optionally push it to origin.

    Args:
        version: Version string (e.g., "1.0.0")
        push: Whether to push the tag to origin

    Returns:
        True if successful, False otherwise
    """
    tag_name = f"v{version}" if not version.startswith('v') else version

    # Create the tag
    print(f"\nCreating tag: {tag_name}")
    result = run_command(['git', 'tag', '-a', tag_name, '-m', f'Release {version}'])

    if result.returncode != 0:
        print(f"Error creating tag: {result.stderr}", file=sys.stderr)
        return False

    print(f"✓ Tag {tag_name} created successfully")

    if push:
        # Push the tag to origin
        print(f"Pushing tag to origin...")
        result = run_command(['git', 'push', 'origin', tag_name])

        if result.returncode != 0:
            print(f"Error pushing tag: {result.stderr}", file=sys.stderr)
            print(f"You can manually push with: git push origin {tag_name}")
            return False

        print(f"✓ Tag {tag_name} pushed to origin")

    return True


def interactive_bump() -> Optional[str]:
    """Interactive version bump - prompts user for increment type."""
    current_version = get_latest_tag()

    print("=" * 60)
    print("Version Bump Tool")
    print("=" * 60)
    print()

    if current_version:
        print(f"Current version: {current_version}")
    else:
        print("No version tags found. Starting from 0.0.0")
        current_version = "0.0.0"

    print()
    print("How would you like to increment the version?")
    print()
    print("  1. Major (breaking changes)     -> ", end="")
    major, minor, patch, _ = parse_version(current_version)
    print(f"{format_version(major + 1, 0, 0)}")

    print("  2. Minor (new features)          -> ", end="")
    print(f"{format_version(major, minor + 1, 0)}")

    print("  3. Patch (bug fixes)             -> ", end="")
    print(f"{format_version(major, minor, patch + 1)}")

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
            print(f"Error: {e}", file=sys.stderr)
            return None
    elif choice == '5':
        print("Cancelled.")
        return None
    else:
        print("Invalid choice.", file=sys.stderr)
        return None

    print()
    print(f"New version will be: {new_version}")
    confirm = input("Confirm? (y/n): ").strip().lower()

    if confirm != 'y':
        print("Cancelled.")
        return None

    return new_version


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Bump version and create git tag',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python scripts/bump_version.py

  # Set specific version
  python scripts/bump_version.py 1.0.0
  python scripts/bump_version.py 2.0.0-beta

  # Quick increment
  python scripts/bump_version.py --major
  python scripts/bump_version.py --minor
  python scripts/bump_version.py --patch

  # Don't push to origin (create tag locally only)
  python scripts/bump_version.py --patch --no-push
        """
    )

    parser.add_argument(
        'version',
        nargs='?',
        help='Specific version to set (e.g., 1.0.0)'
    )
    parser.add_argument(
        '--major',
        action='store_true',
        help='Increment major version'
    )
    parser.add_argument(
        '--minor',
        action='store_true',
        help='Increment minor version'
    )
    parser.add_argument(
        '--patch',
        action='store_true',
        help='Increment patch version'
    )
    parser.add_argument(
        '--no-push',
        action='store_true',
        help='Create tag locally but do not push to origin'
    )

    args = parser.parse_args()

    # Check if we're in a git repository
    result = run_command(['git', 'rev-parse', '--git-dir'])
    if result.returncode != 0:
        print("Error: Not in a git repository", file=sys.stderr)
        sys.exit(1)

    # Determine new version
    new_version = None

    # Check for mutually exclusive options
    increment_flags = sum([args.major, args.minor, args.patch])
    if increment_flags > 1:
        print("Error: Cannot specify multiple increment types", file=sys.stderr)
        sys.exit(1)

    if args.version and increment_flags > 0:
        print("Error: Cannot specify both version and increment type", file=sys.stderr)
        sys.exit(1)

    # Handle quick increment flags
    if args.major or args.minor or args.patch:
        current_version = get_latest_tag()
        if not current_version:
            print("No version tags found. Creating initial version 0.1.0")
            new_version = "0.1.0"
        else:
            increment_type = 'major' if args.major else ('minor' if args.minor else 'patch')
            new_version = increment_version(current_version, increment_type)
            print(f"Bumping {increment_type} version: {current_version} -> {new_version}")

    # Handle specific version argument
    elif args.version:
        try:
            parse_version(args.version)
            new_version = args.version
            print(f"Setting version to: {new_version}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Interactive mode
    else:
        new_version = interactive_bump()

    if not new_version:
        sys.exit(1)

    # Create and push the tag
    success = create_and_push_tag(new_version, push=not args.no_push)

    if success:
        print()
        print("=" * 60)
        print(f"✓ Version {new_version} tagged successfully!")
        if not args.no_push:
            print("✓ Tag pushed to origin")
        print()
        print("Run 'cum update cum' to update to the new version.")
        print("=" * 60)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
