"""
Data models for parent task automation.

Defines the data structures used to track automation events and results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ParentUpdateResult:
    """
    Result of an attempted parent task automation update.

    Attributes:
        parent_task_id: ID of parent task
        parent_task_name: Name of parent task
        old_status: Parent's previous status
        new_status: Parent's new status (after update)
        update_successful: Whether update succeeded
        comment_posted: Whether comment was posted
        skip_reason: If skipped, why? (e.g., "parent_already_active")
        error_message: If failed, error details
        latency_ms: Time taken for update operation

    Change History:
        v1.0.0 - Initial implementation
    """

    parent_task_id: str
    parent_task_name: str
    old_status: str
    new_status: str
    update_successful: bool
    comment_posted: bool
    skip_reason: Optional[str] = None
    error_message: Optional[str] = None
    latency_ms: int = 0


@dataclass
class TaskUpdateEvent:
    """
    Represents a task status update event with automation context.

    Attributes:
        task_id: ID of the task being updated
        old_status: Previous status
        new_status: New status after update
        parent_id: Parent task ID (None if no parent)
        automation_triggered: Whether this update triggered parent automation
        automation_result: Result of parent automation (if triggered)
        timestamp: When the update occurred
        user_initiated: Whether update was user-initiated vs automated

    Change History:
        v1.0.0 - Initial implementation
    """

    task_id: str
    old_status: str
    new_status: str
    parent_id: Optional[str] = None
    automation_triggered: bool = False
    automation_result: Optional[ParentUpdateResult] = None
    timestamp: datetime = field(default_factory=datetime.now)
    user_initiated: bool = True
