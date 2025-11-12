"""Git operations wrapper module.

Provides Python wrappers around Git CLI commands for use in overflow workflows.
"""

import subprocess
import re
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime


class GitOperationError(Exception):
    """Raised when a Git operation fails."""
    pass


def check_git_repo(repo_path: str = ".") -> bool:
    """
    Verify the directory is a Git repository.

    Args:
        repo_path: Path to check (default: current directory)

    Returns:
        bool: True if valid Git repo

    Raises:
        None - Returns False instead of raising
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False


def get_uncommitted_changes(repo_path: str = ".") -> List[str]:
    """
    Get list of files with uncommitted changes.

    Uses 'git status --porcelain' for machine-readable output.
    Includes both staged and unstaged changes.

    Args:
        repo_path: Repository path

    Returns:
        List of file paths relative to repo root

    Raises:
        GitOperationError: If git status command fails
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                # Format: "XY filename" where XY is status code
                # Examples: " M file.txt", "A  newfile.txt", "?? untracked.txt"
                filename = line[3:].strip()
                if filename:
                    files.append(filename)

        return files
    except subprocess.CalledProcessError as e:
        raise GitOperationError(f"Failed to get uncommitted changes: {e.stderr}")


def stage_all_changes(repo_path: str = ".") -> bool:
    """
    Stage all changes (git add .).

    Args:
        repo_path: Repository path

    Returns:
        True if successful

    Raises:
        GitOperationError: If staging fails
    """
    try:
        subprocess.run(
            ["git", "add", "."],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        raise GitOperationError(f"Failed to stage changes: {e.stderr}")


def create_commit(repo_path: str, message: str) -> Tuple[str, str]:
    """
    Create a Git commit.

    Args:
        repo_path: Repository path
        message: Commit message

    Returns:
        Tuple of (commit_sha_full, commit_sha_short)

    Raises:
        GitOperationError: If commit fails
    """
    try:
        # Commit with the message
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        # Extract commit SHA from git log
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        commit_sha = sha_result.stdout.strip()
        commit_sha_short = commit_sha[:7]

        return commit_sha, commit_sha_short

    except subprocess.CalledProcessError as e:
        raise GitOperationError(f"Failed to create commit: {e.stderr}")


def push_to_remote(
    repo_path: str = ".",
    remote: str = "origin",
    branch: Optional[str] = None
) -> bool:
    """
    Push commits to remote repository.

    Args:
        repo_path: Repository path
        remote: Remote name (default: origin)
        branch: Branch name (default: current branch)

    Returns:
        True if push successful

    Raises:
        GitOperationError: If push fails
    """
    try:
        cmd = ["git", "push", remote]
        if branch:
            cmd.append(branch)

        subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        raise GitOperationError(f"Failed to push to remote: {e.stderr}")


def get_current_branch(repo_path: str = ".") -> str:
    """
    Get the current Git branch name.

    Args:
        repo_path: Repository path

    Returns:
        Current branch name

    Raises:
        GitOperationError: If unable to determine branch
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        branch = result.stdout.strip()
        return branch
    except subprocess.CalledProcessError as e:
        raise GitOperationError(f"Failed to get current branch: {e.stderr}")


def get_remote_url(repo_path: str = ".", remote: str = "origin") -> str:
    """
    Get the remote repository URL.

    Args:
        repo_path: Repository path
        remote: Remote name (default: origin)

    Returns:
        Remote URL (HTTPS or SSH format)

    Raises:
        GitOperationError: If unable to get remote URL
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", remote],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GitOperationError(f"Failed to get remote URL: {e.stderr}")


def get_commit_stats(repo_path: str = ".", commit_sha: Optional[str] = None) -> dict:
    """
    Get statistics for a commit (files changed, additions, deletions).

    Args:
        repo_path: Repository path
        commit_sha: Commit SHA (default: HEAD)

    Returns:
        Dict with keys: files_changed (list), additions (int), deletions (int)

    Raises:
        GitOperationError: If unable to get stats
    """
    try:
        sha = commit_sha or "HEAD"

        # Get list of files changed
        files_result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        files_changed = [f for f in files_result.stdout.strip().split('\n') if f]

        # Get additions and deletions
        stats_result = subprocess.run(
            ["git", "show", "--stat", "--format=", sha],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        # Parse the summary line: "X files changed, Y insertions(+), Z deletions(-)"
        additions = 0
        deletions = 0
        for line in stats_result.stdout.strip().split('\n'):
            if 'insertion' in line or 'deletion' in line:
                # Extract numbers
                match_add = re.search(r'(\d+) insertion', line)
                match_del = re.search(r'(\d+) deletion', line)
                if match_add:
                    additions = int(match_add.group(1))
                if match_del:
                    deletions = int(match_del.group(1))

        return {
            'files_changed': files_changed,
            'files_changed_count': len(files_changed),
            'additions': additions,
            'deletions': deletions,
        }

    except subprocess.CalledProcessError as e:
        raise GitOperationError(f"Failed to get commit stats: {e.stderr}")


def get_commit_author(repo_path: str = ".", commit_sha: Optional[str] = None) -> Tuple[str, str]:
    """
    Get author name and email for a commit.

    Args:
        repo_path: Repository path
        commit_sha: Commit SHA (default: HEAD)

    Returns:
        Tuple of (author_name, author_email)

    Raises:
        GitOperationError: If unable to get author info
    """
    try:
        sha = commit_sha or "HEAD"

        # Get author name
        name_result = subprocess.run(
            ["git", "log", "-1", "--format=%an", sha],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        author_name = name_result.stdout.strip()

        # Get author email
        email_result = subprocess.run(
            ["git", "log", "-1", "--format=%ae", sha],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        author_email = email_result.stdout.strip()

        return author_name, author_email

    except subprocess.CalledProcessError as e:
        raise GitOperationError(f"Failed to get commit author: {e.stderr}")
