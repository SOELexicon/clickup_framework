"""
Task: tsk_3f55d115 - Update Plugins Module Comments
Document: refactor/plugins/hooks/notification_hooks.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)

Used By:
    - NotificationSystem: Triggers hooks for notification events
    - NotificationPlugins: Register with these hooks to send notifications
    - TaskService: Uses notification hooks for task event notifications
    - CommandSystem: Triggers notification hooks for command execution events

Purpose:
    Defines hook points for extending notification functionality in the
    ClickUp JSON Manager. Provides a comprehensive set of notification 
    extension points for different system events and notification channels.

Requirements:
    - Notification hooks must support multiple delivery channels
    - Hook points must be available for all major system events
    - Plugin notification implementations must be isolated
    - CRITICAL: Notification failures must not crash the system
    - CRITICAL: Sensitive information must be handled securely in notifications
    - CRITICAL: Notification hooks must be executed asynchronously when appropriate

Notification Hook Definitions

This module defines hook points for extending notification-related operations
in the ClickUp JSON Manager.
"""

from typing import Any, Dict, List, Optional

from .hook_system import registry


class NotificationHooks:
    """
    Notification operation hook points.
    
    These hooks allow plugins to extend or modify notification-related operations
    such as sending notifications, formatting messages, and determining recipients.
    """
    
    # General notification hooks
    NOTIFICATION_SEND = "notification.send"
    NOTIFICATION_RECEIVED = "notification.received"
    
    # Notification formatting
    FORMAT_NOTIFICATION = "notification.format"
    RENDER_NOTIFICATION = "notification.render"
    
    # Channel-specific hooks
    PRE_CHANNEL_SEND = "notification.pre_channel_send"
    POST_CHANNEL_SEND = "notification.post_channel_send"
    
    # Recipient management
    GET_RECIPIENTS = "notification.get_recipients"
    FILTER_RECIPIENTS = "notification.filter_recipients"
    
    # Task-related notification hooks
    TASK_CREATED_NOTIFICATION = "notification.task_created"
    TASK_UPDATED_NOTIFICATION = "notification.task_updated"
    TASK_STATUS_CHANGED_NOTIFICATION = "notification.task_status_changed"
    TASK_COMMENT_ADDED_NOTIFICATION = "notification.task_comment_added"
    TASK_ASSIGNED_NOTIFICATION = "notification.task_assigned"
    TASK_DUE_SOON_NOTIFICATION = "notification.task_due_soon"
    TASK_OVERDUE_NOTIFICATION = "notification.task_overdue"


# Create hooks in the registry
def _register_notification_hooks() -> None:
    """Register all notification hooks in the global registry."""
    
    # General notification hooks
    registry.create_hook(
        NotificationHooks.NOTIFICATION_SEND,
        "Called before a notification is sent. Plugins can modify the notification "
        "content or recipients, or prevent sending by returning False."
    )
    
    registry.create_hook(
        NotificationHooks.NOTIFICATION_RECEIVED,
        "Called when a notification is received from an external source. "
        "Plugins can process or transform incoming notifications."
    )
    
    # Notification formatting
    registry.create_hook(
        NotificationHooks.FORMAT_NOTIFICATION,
        "Called to format a notification message. Plugins can modify the message "
        "format or add additional content."
    )
    
    registry.create_hook(
        NotificationHooks.RENDER_NOTIFICATION,
        "Called to render a notification for display. Plugins can customize the "
        "display format for different UI contexts."
    )
    
    # Channel-specific hooks
    registry.create_hook(
        NotificationHooks.PRE_CHANNEL_SEND,
        "Called before sending a notification through a specific channel. "
        "Plugins can modify channel-specific formatting or prevent sending."
    )
    
    registry.create_hook(
        NotificationHooks.POST_CHANNEL_SEND,
        "Called after sending a notification through a specific channel. "
        "Plugins can perform logging or additional actions based on the result."
    )
    
    # Recipient management
    registry.create_hook(
        NotificationHooks.GET_RECIPIENTS,
        "Called to determine notification recipients. Plugins can add or "
        "modify the list of recipients for a notification."
    )
    
    registry.create_hook(
        NotificationHooks.FILTER_RECIPIENTS,
        "Called to filter notification recipients. Plugins can exclude certain "
        "recipients based on custom rules or preferences."
    )
    
    # Task-related notification hooks
    registry.create_hook(
        NotificationHooks.TASK_CREATED_NOTIFICATION,
        "Called when a task is created to generate notifications. "
        "Plugins can customize task creation notification content."
    )
    
    registry.create_hook(
        NotificationHooks.TASK_UPDATED_NOTIFICATION,
        "Called when a task is updated to generate notifications. "
        "Plugins can customize task update notification content."
    )
    
    registry.create_hook(
        NotificationHooks.TASK_STATUS_CHANGED_NOTIFICATION,
        "Called when a task's status changes to generate notifications. "
        "Plugins can customize status change notification content."
    )
    
    registry.create_hook(
        NotificationHooks.TASK_COMMENT_ADDED_NOTIFICATION,
        "Called when a comment is added to a task to generate notifications. "
        "Plugins can customize comment notification content."
    )
    
    registry.create_hook(
        NotificationHooks.TASK_ASSIGNED_NOTIFICATION,
        "Called when a task is assigned to generate notifications. "
        "Plugins can customize assignment notification content."
    )
    
    registry.create_hook(
        NotificationHooks.TASK_DUE_SOON_NOTIFICATION,
        "Called when a task is due soon to generate notifications. "
        "Plugins can customize due date reminder notification content."
    )
    
    registry.create_hook(
        NotificationHooks.TASK_OVERDUE_NOTIFICATION,
        "Called when a task is overdue to generate notifications. "
        "Plugins can customize overdue notification content."
    )


# Register all hooks
_register_notification_hooks() 