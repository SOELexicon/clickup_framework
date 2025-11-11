"""
Parent task automation engine.

Core automation logic for updating parent tasks when subtasks transition
to active development states.
"""

import logging
import time
from datetime import datetime
from typing import Optional

from clickup_framework.automation.config import AutomationConfig
from clickup_framework.automation.models import TaskUpdateEvent, ParentUpdateResult
from clickup_framework.automation.status_matcher import StatusMatcher
from clickup_framework.exceptions import ClickUpAPIError

logger = logging.getLogger(__name__)


class ParentTaskAutomationEngine:
    """
    Core automation engine for parent task updates.

    Responsibilities:
    - Detect when subtask transitions to development status
    - Check if parent update is needed and allowed
    - Execute parent task update via ClickUp API
    - Post optional comment documenting automation
    - Handle errors, retries, and edge cases
    - Log automation events for debugging

    Change History:
        v1.0.0 - Initial implementation with basic trigger logic
    """

    def __init__(self, config: AutomationConfig, api_client):
        """
        Initialize automation engine.

        Args:
            config: Automation configuration
            api_client: ClickUp API client instance
        """
        self.config = config
        self.api = api_client
        self.status_matcher = StatusMatcher(config)
        self.logger = logging.getLogger(__name__)

    def handle_status_update(
        self,
        task_id: str,
        old_status: str,
        new_status: str,
        force_update: bool = False,
        skip_automation: bool = False
    ) -> TaskUpdateEvent:
        """
        Handle a task status update and trigger parent automation if needed.

        This is the main entry point called after a task status is updated.
        Checks all automation conditions and executes parent update if appropriate.

        Args:
            task_id: ID of task that was updated
            old_status: Previous status
            new_status: New status after update
            force_update: Force parent update even if automation disabled
            skip_automation: Skip automation even if conditions met

        Returns:
            TaskUpdateEvent with automation details

        Change History:
            v1.0.0 - Initial implementation
        """
        event = TaskUpdateEvent(
            task_id=task_id,
            old_status=old_status,
            new_status=new_status,
            parent_id=None,
            automation_triggered=False,
            automation_result=None,
            timestamp=datetime.now(),
            user_initiated=True
        )

        # Short-circuit if automation disabled (unless forced)
        if not self.config.enabled and not force_update:
            self.logger.debug(f"Automation disabled for task {task_id}")
            return event

        # Short-circuit if explicitly skipping automation
        if skip_automation:
            self.logger.debug(f"Skipping automation for task {task_id} (user requested)")
            return event

        # Check if this is a subtask
        try:
            task = self.api.get_task(task_id)
        except Exception as e:
            self.logger.error(f"Failed to fetch task {task_id}: {e}")
            return event

        parent_id = task.get('parent')
        if not parent_id:
            self.logger.debug(f"Task {task_id} has no parent, skipping automation")
            return event

        event.parent_id = parent_id

        # Check if new status triggers automation
        if not self.status_matcher.is_development_status(new_status):
            self.logger.debug(f"Status '{new_status}' not in trigger list")
            return event

        # Execute parent update
        event.automation_triggered = True
        event.automation_result = self._update_parent_task(task, new_status)

        return event

    def _update_parent_task(
        self,
        subtask: dict,
        subtask_new_status: str
    ) -> ParentUpdateResult:
        """
        Execute the actual parent task update with retries and error handling.

        Args:
            subtask: The subtask that triggered the automation
            subtask_new_status: The new status of the subtask

        Returns:
            ParentUpdateResult with success/failure details

        Change History:
            v1.0.0 - Initial implementation with retry logic
        """
        start_time = datetime.now()
        parent_id = subtask.get('parent')
        subtask_id = subtask['id']
        subtask_name = subtask.get('name', 'Unknown')

        try:
            # Fetch parent task
            parent = self.api.get_task(parent_id)
            parent_name = parent.get('name', 'Unknown')

            # Get parent status
            parent_status_obj = parent.get('status', {})
            if isinstance(parent_status_obj, dict):
                parent_status = parent_status_obj.get('status', '')
            else:
                parent_status = parent_status_obj

            # Check if parent is in inactive state
            if not self.status_matcher.is_inactive_status(parent_status):
                self.logger.info(
                    f"Parent {parent_id} already active (status: {parent_status}), skipping update"
                )
                return ParentUpdateResult(
                    parent_task_id=parent_id,
                    parent_task_name=parent_name,
                    old_status=parent_status,
                    new_status=parent_status,  # Unchanged
                    update_successful=False,
                    comment_posted=False,
                    skip_reason="parent_already_active",
                    error_message=None,
                    latency_ms=self._calc_latency(start_time)
                )

            # Determine target status for parent
            target_status = self.config.parent_target_status

            # Update parent task status
            old_status = parent_status
            update_result = self._execute_parent_update(
                parent_id,
                target_status,
                max_retries=self.config.max_retries if self.config.retry_on_failure else 1
            )

            # Post comment if configured
            comment_posted = False
            if self.config.post_comment and update_result:
                comment_posted = self._post_automation_comment(
                    parent_id,
                    subtask_name,
                    target_status
                )

            return ParentUpdateResult(
                parent_task_id=parent_id,
                parent_task_name=parent_name,
                old_status=old_status,
                new_status=target_status,
                update_successful=update_result,
                comment_posted=comment_posted,
                skip_reason=None,
                error_message=None,
                latency_ms=self._calc_latency(start_time)
            )

        except ClickUpAPIError as e:
            self.logger.error(f"ClickUp API error updating parent {parent_id}: {e}")
            return ParentUpdateResult(
                parent_task_id=parent_id,
                parent_task_name="Unknown",
                old_status="Unknown",
                new_status="Unknown",
                update_successful=False,
                comment_posted=False,
                skip_reason=None,
                error_message=f"ClickUp API Error: {e.message} ({e.status_code})",
                latency_ms=self._calc_latency(start_time)
            )
        except Exception as e:
            self.logger.error(f"Failed to update parent task {parent_id}: {e}")
            return ParentUpdateResult(
                parent_task_id=parent_id,
                parent_task_name="Unknown",
                old_status="Unknown",
                new_status="Unknown",
                update_successful=False,
                comment_posted=False,
                skip_reason=None,
                error_message=str(e),
                latency_ms=self._calc_latency(start_time)
            )

    def _execute_parent_update(
        self,
        parent_id: str,
        target_status: str,
        max_retries: int = 3
    ) -> bool:
        """
        Execute parent task status update with retry logic.

        Args:
            parent_id: ID of parent task to update
            target_status: Status to set parent to
            max_retries: Maximum number of retry attempts

        Returns:
            bool: True if update succeeded, False otherwise
        """
        for attempt in range(max_retries):
            try:
                self.api.update_task(parent_id, status=target_status)
                self.logger.info(
                    f"Successfully updated parent {parent_id} to '{target_status}'"
                )
                return True
            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed for parent {parent_id}: {e}"
                )
                if attempt < max_retries - 1:
                    # Exponential backoff
                    backoff_time = 2 ** attempt
                    time.sleep(backoff_time)

        return False

    def _post_automation_comment(
        self,
        parent_id: str,
        subtask_name: str,
        new_status: str
    ) -> bool:
        """
        Post automation comment to parent task.

        Args:
            parent_id: Parent task ID
            subtask_name: Name of subtask that triggered automation
            new_status: New status that parent was set to

        Returns:
            bool: True if comment posted successfully
        """
        try:
            comment_text = self.config.comment_template.format(
                new_status=new_status,
                subtask_name=subtask_name
            )
            self.api.create_task_comment(parent_id, comment_text)
            self.logger.info(f"Posted automation comment to parent {parent_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to post comment to parent {parent_id}: {e}")
            return False

    def _calc_latency(self, start_time: datetime) -> int:
        """Calculate latency in milliseconds."""
        return int((datetime.now() - start_time).total_seconds() * 1000)
