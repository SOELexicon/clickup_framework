"""Git integration module for ClickUp Framework.

This module provides automated Git workflow execution with ClickUp task synchronization.
"""

from clickup_framework.git.overflow import execute_overflow_workflow
from clickup_framework.git.git_operations import (
    check_git_repo,
    get_uncommitted_changes,
    stage_all_changes,
    create_commit,
    push_to_remote,
    get_current_branch,
    get_remote_url,
)
from clickup_framework.git.url_generator import (
    generate_commit_url,
    parse_remote_url,
)

__all__ = [
    'execute_overflow_workflow',
    'check_git_repo',
    'get_uncommitted_changes',
    'stage_all_changes',
    'create_commit',
    'push_to_remote',
    'get_current_branch',
    'get_remote_url',
    'generate_commit_url',
    'parse_remote_url',
]
