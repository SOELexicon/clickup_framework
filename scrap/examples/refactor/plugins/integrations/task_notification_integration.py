"""
Task Notification Integration

This module connects task hooks with the notification system,
sending notifications automatically when task events occur.
"""

import logging
from typing import Any, Dict, List, Optional

from ..hooks.hook_system import HookPriority, register_hook
from ..hooks.task_hooks import TaskHooks
from ..notification.notification_manager import notification_manager, Notification, NotificationType


logger = logging.getLogger(__name__)


def initialize() -> bool:
    """
    Initialize the task notification integration.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    logger.info("Initializing task notification integration")
    
    # Initialize notification manager if needed
    if not notification_manager.notification_plugins:
        notification_manager.initialize()
    
    return True


@register_hook(TaskHooks.TASK_CREATED, priority=HookPriority.NORMAL)
def on_task_created(task: Dict[str, Any]) -> None:
    """
    Handle task creation event.
    
    Args:
        task: The task that was created
    """
    logger.debug(f"Task created event: {task.get('id', 'unknown')}")
    
    # Send notification through notification manager
    notification_manager.notify_task_created(task)


@register_hook(TaskHooks.TASK_UPDATED, priority=HookPriority.NORMAL)
def on_task_updated(task: Dict[str, Any], changed_fields: List[str]) -> None:
    """
    Handle task update event.
    
    Args:
        task: The task that was updated
        changed_fields: List of fields that were changed
    """
    # Skip minor updates to reduce notification noise
    if set(changed_fields).issubset({"updated_at", "last_modified"}):
        return
        
    logger.debug(f"Task updated event: {task.get('id', 'unknown')} - Changed fields: {changed_fields}")
    
    # Send notification through notification manager
    notification_manager.notify_task_updated(task, changed_fields)


@register_hook(TaskHooks.POST_STATUS_CHANGE, priority=HookPriority.NORMAL)
def on_status_change(task: Dict[str, Any], old_status: str, new_status: str) -> None:
    """
    Handle task status change event.
    
    Args:
        task: The task whose status changed
        old_status: Previous status
        new_status: New status
    """
    logger.debug(f"Task status change event: {task.get('id', 'unknown')} - {old_status} -> {new_status}")
    
    # Send notification through notification manager
    notification_manager.notify_task_status_changed(task, old_status, new_status)


@register_hook(TaskHooks.PRE_STATUS_CHANGE, priority=HookPriority.HIGH)
def validate_status_change(task: Dict[str, Any], old_status: str, new_status: str) -> bool:
    """
    Validate a status change before it happens.
    This could prevent certain status changes and notify about it.
    
    Args:
        task: The task whose status is changing
        old_status: Current status
        new_status: Requested new status
        
    Returns:
        bool: True if the status change is allowed, False otherwise
    """
    # Example validation: Prevent changing from "to do" directly to "complete"
    if old_status.lower() == "to do" and new_status.lower() == "complete":
        logger.warning(f"Prevented status change from 'to do' directly to 'complete' for task {task.get('id', 'unknown')}")
        
        # Send a notification about the rejected status change
        notification = Notification(
            subject=f"Invalid Status Change: {task.get('name', 'Task')}",
            message=f"Cannot change task status directly from 'to do' to 'complete'. Please use 'in progress' first.",
            notification_type=NotificationType.WARNING,
            data={
                "task": task,
                "old_status": old_status,
                "new_status": new_status,
                "reason": "Invalid status transition"
            }
        )
        
        notification_manager.send_notification(notification)
        return False
        
    return True


@register_hook(TaskHooks.VALIDATE_TASK, priority=HookPriority.NORMAL)
def validate_task(task: Dict[str, Any]) -> List[str]:
    """
    Validate a task and return validation errors.
    
    Args:
        task: The task to validate
        
    Returns:
        List[str]: List of validation error messages
    """
    errors = []
    
    # Example validation: Priority must be set for tasks
    if "priority" not in task or task["priority"] is None:
        errors.append("Task priority must be set")
    
    # Example validation: Description must not be empty
    if not task.get("description"):
        errors.append("Task description cannot be empty")
    
    # If errors were found, send a notification
    if errors:
        logger.warning(f"Task validation failed for {task.get('id', 'unknown')}: {errors}")
        
        notification = Notification(
            subject=f"Task Validation Failed: {task.get('name', 'Task')}",
            message=f"The task has validation errors:\n• " + "\n• ".join(errors),
            notification_type=NotificationType.WARNING,
            data={
                "task": task,
                "errors": errors
            }
        )
        
        notification_manager.send_notification(notification)
    
    return errors


@register_hook(TaskHooks.TASK_SELECTED, priority=HookPriority.LOW)
def on_task_selected(task: Dict[str, Any]) -> None:
    """
    Handle task selection event (e.g., in the UI).
    
    Args:
        task: The task that was selected
    """
    # Check if the task is due soon
    if "due_date" in task and task.get("due_date"):
        import datetime
        
        try:
            due_date = datetime.datetime.fromisoformat(task["due_date"])
            now = datetime.datetime.now()
            
            # If task is due within 24 hours and not completed
            if (due_date - now).total_seconds() < 86400 and task.get("status", "").lower() != "complete":
                # Send due soon notification
                notification = Notification(
                    subject=f"Task Due Soon: {task.get('name', 'Task')}",
                    message=f"This task is due within 24 hours. Current status: {task.get('status', 'unknown')}",
                    notification_type=NotificationType.TASK_DUE_SOON,
                    data={"task": task}
                )
                
                notification_manager.send_notification(notification)
        except (ValueError, TypeError):
            pass 