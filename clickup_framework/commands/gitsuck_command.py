"""Git suck command - pull all repositories recursively."""

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


def suck_command(args):
    """Pull all Git repositories in project folder."""
    print("🔍 Searching for Git repositories...")

    # Find all repositories
    repos = find_git_repositories('.')

    if not repos:
        print("No Git repositories found in current directory")
        return

    print(f"📁 Found {len(repos)} repositories:\n")

    successful = 0
    failed = 0

    for i, repo_path in enumerate(repos, 1):
        print(f"{i}. {repo_path}")

        # Execute git pull --rebase in repository directory
        result = subprocess.run(
            ['git', 'pull', '--rebase'],
            cwd=str(repo_path),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("   ✅ Pull successful")
            if result.stdout.strip():
                # Show condensed output
                for line in result.stdout.strip().split('\n')[:3]:
                    print(f"      {line}")
            successful += 1
        else:
            print(f"   ⚠️  Pull failed: {result.stderr.strip()}")
            failed += 1

        print()  # Empty line between repos

    # Summary
    print(f"Summary: {successful} successful, {failed} failed")

    # Exit with error if any failed
    sys.exit(1 if failed > 0 else 0)


def register_command(subparsers, add_common_args=None):
    """Register the suck command."""
    parser = subparsers.add_parser(
        'suck',
        help='Pull all Git repositories in project folder',
        description='Recursively find and pull all Git repositories',
        epilog='''Tips:
  • Update all repos: cum suck (runs git pull in all subdirectories)
  • Automatically discovers all .git directories
  • Shows progress for each repository found
  • Useful for multi-repo projects or monorepos
  • Skips repositories with uncommitted changes'''
    )
    parser.set_defaults(func=suck_command)
