"""Bridge between Git operations and ClickUp API for workflow automation.

Provides high-level functions for updating ClickUp tasks during Git workflows.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from clickup_framework.client import ClickUpClient
from clickup_framework.exceptions import ClickUpAPIError, ClickUpRateLimitError


logger = logging.getLogger(__name__)


class ClickUpBridgeError(Exception):
    """Raised when ClickUp bridge operation fails."""
    pass


def format_commit_comment(
    commit_sha_short: str,
    commit_message: str,
    commit_url: str,
    files_changed: Optional[List[str]] = None,
    additions: int = 0,
    deletions: int = 0,
    template: Optional[str] = None
) -> str:
    """
    Format a commit into a markdown comment for ClickUp.

    Args:
        commit_sha_short: Short commit SHA (e.g., "abc123")
        commit_message: Full commit message
        commit_url: URL to view commit on GitHub/GitLab
        files_changed: List of changed files (optional)
        additions: Number of lines added
        deletions: Number of lines deleted
        template: Custom template (optional)

    Returns:
        Formatted markdown comment
    """
    if template:
        # Use custom template with string formatting
        return template.format(
            commit_sha_short=commit_sha_short,
            commit_message=commit_message,
            commit_url=commit_url,
            files_changed=files_changed or [],
            additions=additions,
            deletions=deletions
        )

    # Default template
    comment_lines = [
        f"✅ **Committed: {commit_sha_short}**",
        "",
        f"📝 {commit_message}",
        "",
    ]

    # Add change statistics if provided
    if files_changed:
        files_count = len(files_changed)
        comment_lines.extend([
            f"📊 **Changes:** {files_count} file{'s' if files_count != 1 else ''} changed",
            f"  • +{additions} additions, -{deletions} deletions",
            "",
        ])

    # Add commit link
    comment_lines.append(f"🔗 [View Commit]({commit_url})")

    return "\n".join(comment_lines)


def post_commit_comment(
    client: ClickUpClient,
    task_id: str,
    comment_text: str,
    retry_count: int = 3
) -> Dict[str, Any]:
    """
    Post a comment to a ClickUp task with retry logic.

    Args:
        client: ClickUpClient instance
        task_id: ClickUp task ID
        comment_text: Comment text (markdown supported)
        retry_count: Number of retry attempts (default: 3)

    Returns:
        Comment response from API

    Raises:
        ClickUpBridgeError: If comment posting fails after retries
    """
    last_error = None

    for attempt in range(retry_count):
        try:
            response = client.create_task_comment(task_id, comment_text)
            logger.info(f"Posted comment to task {task_id}")
            return response

        except ClickUpRateLimitError as e:
            # Rate limited - wait and retry
            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
            logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{retry_count}")
            time.sleep(wait_time)
            last_error = e

        except ClickUpAPIError as e:
            # Other API errors
            if attempt < retry_count - 1:
                wait_time = 2 ** attempt
                logger.warning(f"API error, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
                last_error = e
            else:
                last_error = e
                break

    # All retries failed
    raise ClickUpBridgeError(f"Failed to post comment after {retry_count} attempts: {last_error}")


def link_commit_to_task(
    client: ClickUpClient,
    task_id: str,
    commit_url: str,
    commit_sha_short: Optional[str] = None,
    retry_count: int = 3
) -> Dict[str, Any]:
    """
    Add commit URL as a link to ClickUp task.

    Args:
        client: ClickUpClient instance
        task_id: ClickUp task ID
        commit_url: URL to commit on GitHub/GitLab
        commit_sha_short: Short SHA for link title (optional)
        retry_count: Number of retry attempts (default: 3)

    Returns:
        Link response from API

    Raises:
        ClickUpBridgeError: If link creation fails after retries
    """
    # Determine link title
    if commit_sha_short:
        link_title = f"Commit {commit_sha_short}"
    else:
        # Extract SHA from URL if possible
        parts = commit_url.rstrip('/').split('/')
        if len(parts) > 0:
            link_title = f"Commit {parts[-1][:7]}"
        else:
            link_title = "Commit"

    last_error = None

    for attempt in range(retry_count):
        try:
            # add_task_link expects: task_id, link_url, link_text
            response = client.add_task_link(task_id, commit_url, link_title)
            logger.info(f"Added commit link to task {task_id}")
            return response

        except ClickUpRateLimitError as e:
            wait_time = 2 ** attempt
            logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{retry_count}")
            time.sleep(wait_time)
            last_error = e

        except ClickUpAPIError as e:
            if attempt < retry_count - 1:
                wait_time = 2 ** attempt
                logger.warning(f"API error, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
                last_error = e
            else:
                last_error = e
                break

    raise ClickUpBridgeError(f"Failed to add link after {retry_count} attempts: {last_error}")


def update_task_status(
    client: ClickUpClient,
    task_id: str,
    status: str,
    retry_count: int = 3
) -> Dict[str, Any]:
    """
    Update ClickUp task status.

    Args:
        client: ClickUpClient instance
        task_id: ClickUp task ID
        status: New status name (e.g., "in progress", "complete")
        retry_count: Number of retry attempts (default: 3)

    Returns:
        Task update response from API

    Raises:
        ClickUpBridgeError: If status update fails after retries
    """
    last_error = None

    for attempt in range(retry_count):
        try:
            response = client.update_task(task_id, status=status)
            logger.info(f"Updated task {task_id} status to '{status}'")
            return response

        except ClickUpRateLimitError as e:
            wait_time = 2 ** attempt
            logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{retry_count}")
            time.sleep(wait_time)
            last_error = e

        except ClickUpAPIError as e:
            if attempt < retry_count - 1:
                wait_time = 2 ** attempt
                logger.warning(f"API error, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
                last_error = e
            else:
                last_error = e
                break

    raise ClickUpBridgeError(f"Failed to update status after {retry_count} attempts: {last_error}")


def update_task_fields(
    client: ClickUpClient,
    task_id: str,
    priority: Optional[str] = None,
    assignees_add: Optional[List[str]] = None,
    assignees_remove: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    retry_count: int = 3
) -> Dict[str, Any]:
    """
    Update multiple task fields at once.

    Args:
        client: ClickUpClient instance
        task_id: ClickUp task ID
        priority: New priority (optional)
        assignees_add: User IDs to add as assignees (optional)
        assignees_remove: User IDs to remove from assignees (optional)
        tags: Tags to set (optional)
        retry_count: Number of retry attempts (default: 3)

    Returns:
        Task update response from API

    Raises:
        ClickUpBridgeError: If update fails after retries
    """
    # Build update payload
    updates = {}

    if priority is not None:
        updates['priority'] = priority

    if assignees_add is not None:
        # Note: ClickUp API format for adding assignees
        updates['assignees'] = {'add': assignees_add}

    if assignees_remove is not None:
        if 'assignees' not in updates:
            updates['assignees'] = {}
        updates['assignees']['rem'] = assignees_remove

    if tags is not None:
        updates['tags'] = tags

    if not updates:
        logger.info("No fields to update")
        return {}

    last_error = None

    for attempt in range(retry_count):
        try:
            response = client.update_task(task_id, **updates)
            logger.info(f"Updated task {task_id} fields")
            return response

        except ClickUpRateLimitError as e:
            wait_time = 2 ** attempt
            logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{retry_count}")
            time.sleep(wait_time)
            last_error = e

        except ClickUpAPIError as e:
            if attempt < retry_count - 1:
                wait_time = 2 ** attempt
                logger.warning(f"API error, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
                last_error = e
            else:
                last_error = e
                break

    raise ClickUpBridgeError(f"Failed to update fields after {retry_count} attempts: {last_error}")


def apply_clickup_update(
    client: ClickUpClient,
    task_id: str,
    comment: Optional[str] = None,
    status: Optional[str] = None,
    commit_url: Optional[str] = None,
    commit_sha_short: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
    assignees_add: Optional[List[str]] = None,
    assignees_remove: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """
    Apply multiple updates to a ClickUp task.

    Convenience function that combines comment, status, link, and field updates.

    Args:
        client: ClickUpClient instance
        task_id: ClickUp task ID
        comment: Comment text to add (optional)
        status: New status (optional)
        commit_url: Commit URL to link (optional)
        commit_sha_short: Short SHA for link title (optional)
        priority: New priority (optional)
        tags: Tags to set (optional)
        assignees_add: User IDs to add (optional)
        assignees_remove: User IDs to remove (optional)

    Returns:
        Dict with 'success' and 'errors' lists of operation descriptions

    Raises:
        ClickUpBridgeError: If all operations fail
    """
    results = {
        'success': [],
        'errors': []
    }

    # Apply comment
    if comment:
        try:
            post_commit_comment(client, task_id, comment)
            results['success'].append("Posted comment")
        except ClickUpBridgeError as e:
            results['errors'].append(f"Comment failed: {e}")
            logger.error(f"Failed to post comment: {e}")

    # Apply status update
    if status:
        try:
            update_task_status(client, task_id, status)
            results['success'].append(f"Updated status to '{status}'")
        except ClickUpBridgeError as e:
            results['errors'].append(f"Status update failed: {e}")
            logger.error(f"Failed to update status: {e}")

    # Add commit link
    if commit_url:
        try:
            link_commit_to_task(client, task_id, commit_url, commit_sha_short)
            results['success'].append("Added commit link")
        except ClickUpBridgeError as e:
            results['errors'].append(f"Link failed: {e}")
            logger.error(f"Failed to add link: {e}")

    # Update other fields
    if any([priority, tags, assignees_add, assignees_remove]):
        try:
            update_task_fields(
                client, task_id,
                priority=priority,
                tags=tags,
                assignees_add=assignees_add,
                assignees_remove=assignees_remove
            )
            results['success'].append("Updated task fields")
        except ClickUpBridgeError as e:
            results['errors'].append(f"Field update failed: {e}")
            logger.error(f"Failed to update fields: {e}")

    # If everything failed, raise error
    if not results['success'] and results['errors']:
        raise ClickUpBridgeError(f"All ClickUp updates failed: {results['errors']}")

    return results
