"""Git integration module for ClickUp Framework.

This module provides automated Git workflow execution with ClickUp task synchronization.
"""

from clickup_framework.git.overflow import (
    execute_overflow_workflow,
    WorkflowType,
    OverflowContext,
    CommitResult,
    ClickUpUpdate,
    WorkflowResult,
)
from clickup_framework.git.git_operations import (
    check_git_repo,
    get_uncommitted_changes,
    stage_all_changes,
    create_commit,
    push_to_remote,
    get_current_branch,
    get_remote_url,
    get_commit_stats,
    get_commit_author,
    GitOperationError,
)
from clickup_framework.git.url_generator import (
    generate_commit_url,
    generate_branch_url,
    generate_pr_url,
    parse_remote_url,
    URLParseError,
)
from clickup_framework.git.config import (
    load_config,
    OverflowConfig,
    StatusMapping,
    ConfigError,
)
from clickup_framework.git import clickup_bridge

__all__ = [
    # Workflow execution
    'execute_overflow_workflow',
    'WorkflowType',
    'OverflowContext',
    'CommitResult',
    'ClickUpUpdate',
    'WorkflowResult',
    # Git operations
    'check_git_repo',
    'get_uncommitted_changes',
    'stage_all_changes',
    'create_commit',
    'push_to_remote',
    'get_current_branch',
    'get_remote_url',
    'get_commit_stats',
    'get_commit_author',
    'GitOperationError',
    # URL generation
    'generate_commit_url',
    'generate_branch_url',
    'generate_pr_url',
    'parse_remote_url',
    'URLParseError',
    # Configuration
    'load_config',
    'OverflowConfig',
    'StatusMapping',
    'ConfigError',
    # ClickUp bridge
    'clickup_bridge',
]
