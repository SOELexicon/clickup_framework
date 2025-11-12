"""Git repository URL parsing and commit URL generation.

Supports both GitHub and GitLab with HTTPS and SSH URL formats.
"""

import re
from typing import Optional, Dict
from urllib.parse import urlparse


class URLParseError(Exception):
    """Raised when URL parsing fails."""
    pass


def parse_remote_url(remote_url: str) -> Dict[str, str]:
    """
    Parse Git remote URL to extract host, owner, and repo name.

    Supports both HTTPS and SSH formats for GitHub and GitLab:
    - HTTPS: https://github.com/owner/repo.git
    - HTTPS: https://gitlab.com/owner/repo.git
    - SSH: git@github.com:owner/repo.git
    - SSH: git@gitlab.com:owner/repo.git

    Args:
        remote_url: Git remote URL (HTTPS or SSH format)

    Returns:
        Dict with keys: 'host', 'owner', 'repo'
        Example: {'host': 'github.com', 'owner': 'user', 'repo': 'project'}

    Raises:
        URLParseError: If URL format is invalid or unsupported
    """
    # Remove trailing .git if present
    url = remote_url.strip()
    if url.endswith('.git'):
        url = url[:-4]

    # Try SSH format first: git@host:owner/repo
    ssh_pattern = r'^git@([^:]+):(.+)/([^/]+)$'
    ssh_match = re.match(ssh_pattern, url)

    if ssh_match:
        host = ssh_match.group(1)
        owner = ssh_match.group(2)
        repo = ssh_match.group(3)

        # Validate host is GitHub or GitLab
        if host not in ['github.com', 'gitlab.com']:
            raise URLParseError(f"Unsupported host: {host}. Only github.com and gitlab.com are supported.")

        return {
            'host': host,
            'owner': owner,
            'repo': repo
        }

    # Try HTTPS format: https://host/owner/repo
    try:
        parsed = urlparse(url)

        if not parsed.scheme or not parsed.netloc:
            raise URLParseError(f"Invalid URL format: {remote_url}")

        if parsed.scheme not in ['http', 'https']:
            raise URLParseError(f"Unsupported scheme: {parsed.scheme}. Only http/https and SSH are supported.")

        # Validate host
        host = parsed.netloc
        if host not in ['github.com', 'gitlab.com']:
            raise URLParseError(f"Unsupported host: {host}. Only github.com and gitlab.com are supported.")

        # Extract owner and repo from path
        path_parts = parsed.path.strip('/').split('/')

        if len(path_parts) < 2:
            raise URLParseError(f"Invalid path format: {parsed.path}. Expected format: /owner/repo")

        owner = path_parts[0]
        repo = path_parts[1]

        return {
            'host': host,
            'owner': owner,
            'repo': repo
        }

    except Exception as e:
        if isinstance(e, URLParseError):
            raise
        raise URLParseError(f"Failed to parse URL: {remote_url}. Error: {str(e)}")


def generate_commit_url(remote_url: str, commit_sha: str) -> str:
    """
    Generate web URL for viewing a commit on GitHub or GitLab.

    Args:
        remote_url: Git remote URL (HTTPS or SSH format)
        commit_sha: Full or short commit SHA

    Returns:
        HTTPS URL for viewing the commit in browser
        Example: https://github.com/owner/repo/commit/abc123

    Raises:
        URLParseError: If remote URL is invalid
        ValueError: If commit SHA is empty
    """
    if not commit_sha or not commit_sha.strip():
        raise ValueError("Commit SHA cannot be empty")

    # Parse the remote URL
    parsed = parse_remote_url(remote_url)

    host = parsed['host']
    owner = parsed['owner']
    repo = parsed['repo']

    # Generate the commit URL
    # Both GitHub and GitLab use the same format: /owner/repo/commit/sha
    commit_url = f"https://{host}/{owner}/{repo}/commit/{commit_sha}"

    return commit_url


def generate_branch_url(remote_url: str, branch_name: str) -> str:
    """
    Generate web URL for viewing a branch on GitHub or GitLab.

    Args:
        remote_url: Git remote URL (HTTPS or SSH format)
        branch_name: Branch name

    Returns:
        HTTPS URL for viewing the branch in browser
        Example: https://github.com/owner/repo/tree/branch-name

    Raises:
        URLParseError: If remote URL is invalid
        ValueError: If branch name is empty
    """
    if not branch_name or not branch_name.strip():
        raise ValueError("Branch name cannot be empty")

    # Parse the remote URL
    parsed = parse_remote_url(remote_url)

    host = parsed['host']
    owner = parsed['owner']
    repo = parsed['repo']

    # Generate the branch URL
    # Both GitHub and GitLab use: /owner/repo/tree/branch
    branch_url = f"https://{host}/{owner}/{repo}/tree/{branch_name}"

    return branch_url


def generate_pr_url(remote_url: str, pr_number: Optional[int] = None) -> str:
    """
    Generate web URL for pull request / merge request.

    Args:
        remote_url: Git remote URL (HTTPS or SSH format)
        pr_number: PR/MR number (optional - if None, returns new PR creation URL)

    Returns:
        HTTPS URL for viewing or creating PR/MR

    Raises:
        URLParseError: If remote URL is invalid
    """
    # Parse the remote URL
    parsed = parse_remote_url(remote_url)

    host = parsed['host']
    owner = parsed['owner']
    repo = parsed['repo']

    if pr_number:
        # Generate URL to view existing PR/MR
        if host == 'github.com':
            return f"https://{host}/{owner}/{repo}/pull/{pr_number}"
        else:  # gitlab.com
            return f"https://{host}/{owner}/{repo}/-/merge_requests/{pr_number}"
    else:
        # Generate URL to create new PR/MR
        if host == 'github.com':
            return f"https://{host}/{owner}/{repo}/compare"
        else:  # gitlab.com
            return f"https://{host}/{owner}/{repo}/-/merge_requests/new"
