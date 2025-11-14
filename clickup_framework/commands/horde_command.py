"""Git horde command - execute git stash operations on all repositories recursively."""

import subprocess
import sys
from pathlib import Path


def find_git_repositories(root_path):
    """Recursively find all Git repositories."""
    repos = []
    root = Path(root_path).resolve()

    # Directories to skip
    skip_dirs = {
        'node_modules', '.venv', 'venv', 'env',
        '__pycache__', '.pytest_cache', '.mypy_cache',
        '.tox', 'dist', 'build', '.git'
    }

    # Walk directory tree
    for path in root.rglob('.git'):
        # Check if .git is a directory (not a file)
        if path.is_dir():
            repo_path = path.parent
            # Skip if any parent is in skip list
            if not any(skip in repo_path.parts for skip in skip_dirs):
                repos.append(repo_path)

    return sorted(repos)


def horde_command(args):
    """Execute git stash operations on all Git repositories in project folder."""
    print("🔍 Searching for Git repositories...")

    # Find all repositories
    repos = find_git_repositories('.')

    if not repos:
        print("No Git repositories found in current directory")
        return

    print(f"📁 Found {len(repos)} repositories:\n")

    # Build git stash command
    cmd = ['git', 'stash']

    # Add subcommand if provided
    if args.subcommand:
        cmd.append(args.subcommand)

    # Add additional arguments
    if args.args:
        cmd.extend(args.args)

    successful = 0
    failed = 0

    # Iterate over all repositories
    for i, repo_path in enumerate(repos, 1):
        print(f"{i}. {repo_path}")

        # Execute git stash command in repository directory
        result = subprocess.run(
            cmd,
            cwd=str(repo_path),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("   ✅ Stash operation successful")
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n')[:3]:
                    print(f"      {line}")
            successful += 1
        else:
            print(f"   ⚠️  Stash operation failed: {result.stderr.strip()}")
            failed += 1

        print()  # Empty line between repos

    # Summary
    print(f"Summary: {successful} successful, {failed} failed")
    sys.exit(1 if failed > 0 else 0)


def register_command(subparsers, add_common_args=None):
    """Register the horde command."""
    parser = subparsers.add_parser(
        'horde',
        help='Execute git stash operations on all Git repositories in project folder',
        description='Recursively find and execute git stash operations on all Git repositories. Usage: cum horde [push|pop|list|apply|drop|clear|...] [args...]'
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

    parser.set_defaults(func=horde_command)
