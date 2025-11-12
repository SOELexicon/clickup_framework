"""Git Overflow workflow orchestration.

Coordinates Git operations with ClickUp task updates for automated workflows.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from clickup_framework.client import ClickUpClient
from clickup_framework.git import git_operations as git_ops
from clickup_framework.git import url_generator
from clickup_framework.git import clickup_bridge
from clickup_framework.git.config import load_config, OverflowConfig, get_status_for_action


logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Types of Git Overflow workflows."""
    DIRECT_COMMIT = 0  # Workflow 0: Direct commit to current branch
    PULL_REQUEST = 1   # Workflow 1: Create PR/MR
    WIP_BRANCH = 2     # Workflow 2: Branch and WIP commit
    HOTFIX = 3         # Workflow 3: Hotfix workflow
    MERGE_COMPLETE = 4 # Workflow 4: Merge and mark complete


@dataclass
class OverflowContext:
    """
    Context data for overflow workflow execution.

    Contains all information needed to execute a workflow and update ClickUp.
    """
    # Task information
    task_id: str
    task_url: str
    task_name: Optional[str] = None

    # Git information
    repo_path: str = "."
    branch: Optional[str] = None
    commit_message: str = ""
    remote: str = "origin"
    remote_url: Optional[str] = None

    # Workflow configuration
    workflow_type: WorkflowType = WorkflowType.DIRECT_COMMIT
    auto_push: bool = True
    update_clickup: bool = True

    # Additional options
    assignees: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None
    status: Optional[str] = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    dry_run: bool = False


@dataclass
class CommitResult:
    """
    Result of Git commit operation.

    Contains details about the created commit and changed files.
    """
    # Commit details
    commit_sha: str
    commit_sha_short: str
    commit_message: str
    commit_url: Optional[str] = None

    # Author information
    author_name: Optional[str] = None
    author_email: Optional[str] = None

    # File changes
    files_changed: List[str] = field(default_factory=list)
    files_changed_count: int = 0
    additions: int = 0
    deletions: int = 0

    # Branch information
    branch: Optional[str] = None
    remote_url: Optional[str] = None

    # Status
    pushed: bool = False
    push_error: Optional[str] = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ClickUpUpdate:
    """
    ClickUp task update to be applied.

    Represents a set of changes to apply to a ClickUp task.
    """
    task_id: str

    # Comment to add
    comment: Optional[str] = None

    # Status update
    status: Optional[str] = None

    # Field updates
    priority: Optional[str] = None
    assignees_add: Optional[List[str]] = None
    assignees_remove: Optional[List[str]] = None
    tags_add: Optional[List[str]] = None
    tags_remove: Optional[List[str]] = None

    # Links to add
    links: Optional[List[Dict[str, str]]] = None

    # Custom fields
    custom_fields: Optional[Dict[str, Any]] = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    applied: bool = False
    error: Optional[str] = None


@dataclass
class WorkflowResult:
    """
    Complete result of workflow execution.

    Contains results from both Git operations and ClickUp updates.
    """
    # Status
    success: bool
    workflow_type: WorkflowType
    error: Optional[str] = None

    # Results
    commit_result: Optional[CommitResult] = None
    clickup_update: Optional[ClickUpUpdate] = None

    # Execution details
    duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    # Additional info
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


def execute_overflow_workflow(
    context: OverflowContext,
    config: Optional[OverflowConfig] = None,
    client: Optional[ClickUpClient] = None
) -> WorkflowResult:
    """
    Execute a Git Overflow workflow.

    Orchestrates Git operations and ClickUp updates based on workflow type.

    Args:
        context: Workflow execution context
        config: Overflow configuration (optional - will load from file if not provided)
        client: ClickUpClient instance (optional - will create if not provided)

    Returns:
        WorkflowResult with execution status and details

    Raises:
        ValueError: If required parameters are missing
        git_ops.GitOperationError: If Git operations fail
    """
    start_time = datetime.now()
    warnings = []

    # Load configuration if not provided
    if config is None:
        config = load_config(search=True)
        logger.debug("Loaded overflow configuration")

    # Route to appropriate workflow handler
    if context.workflow_type == WorkflowType.DIRECT_COMMIT:
        return _execute_workflow_0(context, config, client, start_time, warnings)
    else:
        # Other workflows not yet implemented
        return WorkflowResult(
            success=False,
            workflow_type=context.workflow_type,
            error=f"Workflow type {context.workflow_type.name} not yet implemented",
            warnings=warnings,
            duration_seconds=(datetime.now() - start_time).total_seconds()
        )


def _execute_workflow_0(
    context: OverflowContext,
    config: OverflowConfig,
    client: Optional[ClickUpClient],
    start_time: datetime,
    warnings: List[str]
) -> WorkflowResult:
    """
    Execute Workflow 0: Direct Commit to current branch.

    Steps:
    1. Verify Git repository
    2. Check for uncommitted changes
    3. Stage all changes
    4. Create commit
    5. Get commit stats and author info
    6. Push to remote (if enabled)
    7. Generate commit URL
    8. Update ClickUp task (if enabled)

    Args:
        context: Workflow execution context
        config: Overflow configuration
        client: ClickUpClient instance (optional)
        start_time: Workflow start time
        warnings: List to accumulate warnings

    Returns:
        WorkflowResult with execution details
    """
    logger.info(f"Starting Workflow 0 (Direct Commit) for task {context.task_id}")

    # Validate required parameters
    if not context.commit_message:
        return WorkflowResult(
            success=False,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            error="Commit message is required",
            warnings=warnings,
            duration_seconds=(datetime.now() - start_time).total_seconds()
        )

    # If dry run, log and return
    if context.dry_run:
        logger.info("DRY RUN MODE - No actual changes will be made")
        return WorkflowResult(
            success=True,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            warnings=["DRY RUN - No changes made"],
            duration_seconds=(datetime.now() - start_time).total_seconds(),
            metadata={"dry_run": True}
        )

    commit_result = None
    clickup_update = None

    try:
        # Step 1: Verify Git repository
        if not git_ops.check_git_repo(context.repo_path):
            return WorkflowResult(
                success=False,
                workflow_type=WorkflowType.DIRECT_COMMIT,
                error=f"Not a Git repository: {context.repo_path}",
                warnings=warnings,
                duration_seconds=(datetime.now() - start_time).total_seconds()
            )

        # Step 2: Check for uncommitted changes
        uncommitted_files = git_ops.get_uncommitted_changes(context.repo_path)
        if not uncommitted_files:
            logger.warning("No uncommitted changes found")
            warnings.append("No uncommitted changes to commit")
            # Continue anyway - might be doing an empty commit or amend

        # Step 3: Stage all changes
        logger.info(f"Staging {len(uncommitted_files)} changed files")
        git_ops.stage_all_changes(context.repo_path)

        # Step 4: Create commit
        logger.info(f"Creating commit: {context.commit_message[:50]}...")
        commit_sha, commit_sha_short = git_ops.create_commit(
            context.repo_path,
            context.commit_message
        )
        logger.info(f"Created commit {commit_sha_short}")

        # Step 5: Get commit stats and author
        commit_stats = git_ops.get_commit_stats(context.repo_path, commit_sha)
        author_name, author_email = git_ops.get_commit_author(context.repo_path, commit_sha)
        branch = context.branch or git_ops.get_current_branch(context.repo_path)
        remote_url = context.remote_url or git_ops.get_remote_url(context.repo_path, context.remote)

        # Build commit result
        commit_result = CommitResult(
            commit_sha=commit_sha,
            commit_sha_short=commit_sha_short,
            commit_message=context.commit_message,
            author_name=author_name,
            author_email=author_email,
            files_changed=commit_stats['files_changed'],
            files_changed_count=commit_stats['files_changed_count'],
            additions=commit_stats['additions'],
            deletions=commit_stats['deletions'],
            branch=branch,
            remote_url=remote_url,
            pushed=False
        )

        # Step 6: Push to remote (if enabled)
        if context.auto_push:
            try:
                logger.info(f"Pushing to {context.remote}/{branch}")
                git_ops.push_to_remote(context.repo_path, context.remote, branch)
                commit_result.pushed = True
                logger.info("Push successful")
            except git_ops.GitOperationError as e:
                commit_result.push_error = str(e)
                warnings.append(f"Push failed: {e}")
                logger.warning(f"Failed to push: {e}")

        # Step 7: Generate commit URL
        try:
            commit_url = url_generator.generate_commit_url(remote_url, commit_sha)
            commit_result.commit_url = commit_url
            logger.debug(f"Generated commit URL: {commit_url}")
        except url_generator.URLParseError as e:
            warnings.append(f"Could not generate commit URL: {e}")
            logger.warning(f"Could not generate commit URL: {e}")

        # Step 8: Update ClickUp task (if enabled)
        if context.update_clickup:
            clickup_update = _update_clickup_task(
                context, config, commit_result, client, warnings
            )

        # Success!
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Workflow 0 completed successfully in {duration:.2f}s")

        return WorkflowResult(
            success=True,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            commit_result=commit_result,
            clickup_update=clickup_update,
            warnings=warnings,
            duration_seconds=duration
        )

    except git_ops.GitOperationError as e:
        # Git operation failed
        logger.error(f"Git operation failed: {e}")
        duration = (datetime.now() - start_time).total_seconds()
        return WorkflowResult(
            success=False,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            error=f"Git operation failed: {e}",
            commit_result=commit_result,
            warnings=warnings,
            duration_seconds=duration
        )

    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error: {e}", exc_info=True)
        duration = (datetime.now() - start_time).total_seconds()
        return WorkflowResult(
            success=False,
            workflow_type=WorkflowType.DIRECT_COMMIT,
            error=f"Unexpected error: {e}",
            commit_result=commit_result,
            warnings=warnings,
            duration_seconds=duration
        )


def _update_clickup_task(
    context: OverflowContext,
    config: OverflowConfig,
    commit_result: CommitResult,
    client: Optional[ClickUpClient],
    warnings: List[str]
) -> ClickUpUpdate:
    """
    Update ClickUp task with commit information.

    Args:
        context: Workflow execution context
        config: Overflow configuration
        commit_result: Result from Git commit operation
        client: ClickUpClient instance (optional - will create if needed)
        warnings: List to accumulate warnings

    Returns:
        ClickUpUpdate with applied status and any errors
    """
    logger.info(f"Updating ClickUp task {context.task_id}")

    # Create client if not provided
    if client is None:
        try:
            client = ClickUpClient()
        except Exception as e:
            error_msg = f"Failed to create ClickUp client: {e}"
            logger.error(error_msg)
            return ClickUpUpdate(
                task_id=context.task_id,
                applied=False,
                error=error_msg
            )

    # Build ClickUp update
    clickup_update = ClickUpUpdate(task_id=context.task_id)

    # Determine status to set (from context or config)
    status = context.status
    if not status:
        # Use status from config based on action
        if commit_result.pushed:
            status = get_status_for_action(config, 'push')
        else:
            status = get_status_for_action(config, 'commit')

    clickup_update.status = status

    # Format commit comment using template
    if commit_result.commit_url:
        comment_text = clickup_bridge.format_commit_comment(
            commit_sha_short=commit_result.commit_sha_short,
            commit_message=commit_result.commit_message,
            commit_url=commit_result.commit_url,
            files_changed=commit_result.files_changed,
            additions=commit_result.additions,
            deletions=commit_result.deletions,
            template=config.commit_comment_template if hasattr(config, 'commit_comment_template') else None
        )
        clickup_update.comment = comment_text

    # Apply updates to ClickUp
    try:
        results = clickup_bridge.apply_clickup_update(
            client=client,
            task_id=context.task_id,
            comment=clickup_update.comment,
            status=clickup_update.status,
            commit_url=commit_result.commit_url,
            commit_sha_short=commit_result.commit_sha_short,
            priority=context.priority,
            tags=context.tags,
            assignees_add=context.assignees
        )

        # Mark as applied if any operations succeeded
        if results['success']:
            clickup_update.applied = True
            logger.info(f"ClickUp update successful: {results['success']}")

        # Add any errors to warnings
        if results['errors']:
            for error in results['errors']:
                warnings.append(error)
            clickup_update.error = "; ".join(results['errors'])

        return clickup_update

    except clickup_bridge.ClickUpBridgeError as e:
        error_msg = f"ClickUp update failed: {e}"
        logger.error(error_msg)
        warnings.append(error_msg)
        clickup_update.applied = False
        clickup_update.error = str(e)
        return clickup_update

    except Exception as e:
        error_msg = f"Unexpected error updating ClickUp: {e}"
        logger.error(error_msg, exc_info=True)
        warnings.append(error_msg)
        clickup_update.applied = False
        clickup_update.error = str(e)
        return clickup_update
