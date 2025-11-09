"""
Task: tsk_3f55d115 - Update Plugins Module Comments
Document: refactor/plugins/notification/notification_manager.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)

Used By:
    - CoreManager: Uses this to send system notifications
    - TaskService: Sends task-related notifications through this manager
    - NotificationPlugins: Register with this manager to deliver notifications
    - CommandSystem: Uses this to notify about command execution events

Purpose:
    Provides the notification manager which handles sending notifications
    through registered notification plugins. Centralizes notification logic,
    recipient filtering, channel selection, and delivery tracking.

Requirements:
    - Must support multiple notification channels and plugins
    - Must properly handle notification priorities
    - Must apply hooks for customizing notifications
    - Must isolate plugin failures to prevent system crashes
    - CRITICAL: Error handling must prevent notification failures from affecting core operations
    - CRITICAL: Notification delivery must be properly tracked
    - CRITICAL: Notification content must be secured when containing sensitive information

Notification Manager

This module provides the notification manager which handles sending notifications
through registered notification plugins.
"""

import logging
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Type, Union

from ..hooks.hook_system import HookPriority, registry
from ..hooks.notification_hooks import NotificationHooks
from ..plugin_interface import NotificationPlugin
from ..plugin_manager import plugin_manager


logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    URGENT = auto()


class NotificationType(Enum):
    """Types of notifications."""
    TASK_CREATED = auto()
    TASK_UPDATED = auto()
    TASK_STATUS_CHANGED = auto()
    TASK_COMMENT_ADDED = auto()
    TASK_ASSIGNED = auto()
    TASK_DUE_SOON = auto()
    TASK_OVERDUE = auto()
    SYSTEM = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CUSTOM = auto()


class Notification:
    """
    Represents a notification to be sent.
    
    This class contains all the information needed to send a notification,
    including the message, recipients, priority, type, and additional data.
    """
    
    def __init__(
        self,
        subject: str,
        message: str,
        notification_type: Union[NotificationType, str] = NotificationType.INFO,
        priority: Union[NotificationPriority, str] = NotificationPriority.MEDIUM,
        recipients: Optional[List[str]] = None,
        sender: str = "system",
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None,
    ):
        """
        Initialize a notification.
        
        Args:
            subject: Subject of the notification
            message: Content of the notification
            notification_type: Type of notification
            priority: Priority of the notification
            recipients: List of recipient identifiers
            sender: Identifier of the sender
            data: Additional data for the notification
            channels: Specific channels to send through (None for all available)
        """
        self.subject = subject
        self.message = message
        
        # Convert string type to enum if needed
        if isinstance(notification_type, str):
            try:
                self.notification_type = NotificationType[notification_type.upper()]
            except KeyError:
                self.notification_type = NotificationType.CUSTOM
        else:
            self.notification_type = notification_type
        
        # Convert string priority to enum if needed
        if isinstance(priority, str):
            try:
                self.priority = NotificationPriority[priority.upper()]
            except KeyError:
                self.priority = NotificationPriority.MEDIUM
        else:
            self.priority = priority
        
        self.recipients = recipients or []
        self.sender = sender
        self.data = data or {}
        self.channels = channels or []
        self.timestamp = None  # Will be set when sent
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the notification to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the notification
        """
        return {
            "subject": self.subject,
            "message": self.message,
            "notification_type": self.notification_type.name if isinstance(self.notification_type, NotificationType) else self.notification_type,
            "priority": self.priority.name if isinstance(self.priority, NotificationPriority) else self.priority,
            "recipients": self.recipients,
            "sender": self.sender,
            "data": self.data,
            "channels": self.channels,
            "timestamp": self.timestamp,
        }


class NotificationManager:
    """
    Manages sending notifications through registered notification plugins.
    
    This class provides methods for sending notifications, registering notification
    plugins, and managing notification settings.
    """
    
    def __init__(self):
        """Initialize the notification manager."""
        self.notification_plugins: Dict[str, NotificationPlugin] = {}
        self.channel_mapping: Dict[str, List[str]] = {}  # channel -> [plugin_ids]
        self.enabled_channels: Set[str] = set()
        self.default_channels: List[str] = []
    
    def initialize(self) -> None:
        """Initialize the notification manager, discovering notification plugins."""
        logger.debug("Initializing notification manager")
        self._discover_notification_plugins()
    
    def _discover_notification_plugins(self) -> None:
        """
        Discover all registered notification plugins.
        """
        # Clear existing plugin registrations
        self.notification_plugins = {}
        self.channel_mapping = {}
        
        # Get all plugins from the plugin manager
        for plugin_id, plugin_info in plugin_manager.get_all_plugins().items():
            if not plugin_info.status.name == 'ENABLED':
                continue
                
            plugin_instance = plugin_manager.get_plugin_instance(plugin_id)
            if plugin_instance and isinstance(plugin_instance, NotificationPlugin):
                self.notification_plugins[plugin_id] = plugin_instance
                
                # Register the plugin's supported channels
                channels = plugin_instance.get_notification_channels()
                for channel in channels:
                    if channel not in self.channel_mapping:
                        self.channel_mapping[channel] = []
                    
                    self.channel_mapping[channel].append(plugin_id)
                    self.enabled_channels.add(channel)
        
        # Set default channels if available
        if self.enabled_channels:
            self.default_channels = list(self.enabled_channels)[:1]
            
        logger.debug(f"Discovered {len(self.notification_plugins)} notification plugins with {len(self.enabled_channels)} channels")
    
    def send_notification(self, notification: Notification) -> bool:
        """
        Send a notification through appropriate channels.
        
        Args:
            notification: The notification to send
            
        Returns:
            bool: True if at least one plugin successfully sent the notification
        """
        if not notification:
            return False
            
        # If no channels specified, use default channels
        channels = notification.channels or self.default_channels
        if not channels:
            logger.warning("No notification channels available, notification not sent")
            return False
        
        # Apply hooks to get and filter recipients
        notification.recipients = self._get_recipients(notification)
        if not notification.recipients:
            logger.debug("No recipients for notification, skipping")
            return True  # Consider this a success since there's no one to notify
        
        # Apply formatting hooks
        formatted_notification = self._format_notification(notification)
        
        # Use hooks to determine if we should send this notification
        if not self._should_send_notification(formatted_notification):
            logger.debug("Notification send prevented by hook")
            return False
        
        # Try to send through all specified channels
        success = False
        sent_channels = []
        
        for channel in channels:
            if channel not in self.enabled_channels:
                logger.warning(f"Notification channel '{channel}' not available")
                continue
                
            # Execute pre-channel send hook
            channel_notification = formatted_notification
            channel_notification = self._pre_channel_send(channel, channel_notification)
            
            # Get plugins that implement this channel
            plugin_ids = self.channel_mapping.get(channel, [])
            if not plugin_ids:
                logger.warning(f"No plugins available for channel '{channel}'")
                continue
            
            # Try each plugin until one succeeds
            for plugin_id in plugin_ids:
                plugin = self.notification_plugins.get(plugin_id)
                if not plugin:
                    continue
                    
                try:
                    if plugin.send_notification(
                        channel, 
                        channel_notification.message, 
                        {
                            "subject": channel_notification.subject,
                            "recipients": channel_notification.recipients,
                            "data": channel_notification.data,
                            "priority": channel_notification.priority
                        }
                    ):
                        success = True
                        sent_channels.append(channel)
                        
                        # Execute post-channel send hook
                        self._post_channel_send(channel, channel_notification, True)
                        break
                except Exception as e:
                    logger.error(f"Error sending notification through plugin {plugin_id}: {str(e)}")
                    # Execute post-channel send hook with failure
                    self._post_channel_send(channel, channel_notification, False, error=str(e))
            
        logger.debug(f"Notification sent through channels: {sent_channels}")
        return success
    
    def _get_recipients(self, notification: Notification) -> List[str]:
        """
        Get recipients for a notification, applying hooks.
        
        Args:
            notification: The notification being sent
            
        Returns:
            List[str]: List of recipient identifiers
        """
        # Start with the notification's recipients
        recipients = notification.recipients.copy()
        
        # Apply GET_RECIPIENTS hook
        hook = registry.get_hook(NotificationHooks.GET_RECIPIENTS)
        if hook:
            try:
                hook_result = hook.execute(notification=notification, recipients=recipients)
                if hook_result:
                    recipients = hook_result
            except Exception as e:
                logger.error(f"Error executing GET_RECIPIENTS hook: {str(e)}")
        
        # Apply FILTER_RECIPIENTS hook
        hook = registry.get_hook(NotificationHooks.FILTER_RECIPIENTS)
        if hook:
            try:
                hook_result = hook.execute(notification=notification, recipients=recipients)
                if hook_result:
                    recipients = hook_result
            except Exception as e:
                logger.error(f"Error executing FILTER_RECIPIENTS hook: {str(e)}")
        
        return recipients
    
    def _format_notification(self, notification: Notification) -> Notification:
        """
        Format a notification, applying hooks.
        
        Args:
            notification: The notification to format
            
        Returns:
            Notification: Formatted notification
        """
        # Create a copy of the notification to avoid modifying the original
        formatted = Notification(
            subject=notification.subject,
            message=notification.message,
            notification_type=notification.notification_type,
            priority=notification.priority,
            recipients=notification.recipients,
            sender=notification.sender,
            data=notification.data.copy() if notification.data else {},
            channels=notification.channels,
        )
        
        # Apply FORMAT_NOTIFICATION hook
        hook = registry.get_hook(NotificationHooks.FORMAT_NOTIFICATION)
        if hook:
            try:
                hook_result = hook.execute(notification=formatted)
                if hook_result:
                    formatted = hook_result
            except Exception as e:
                logger.error(f"Error executing FORMAT_NOTIFICATION hook: {str(e)}")
        
        return formatted
    
    def _should_send_notification(self, notification: Notification) -> bool:
        """
        Determine if a notification should be sent, applying hooks.
        
        Args:
            notification: The notification to send
            
        Returns:
            bool: True if the notification should be sent, False otherwise
        """
        hook = registry.get_hook(NotificationHooks.NOTIFICATION_SEND)
        if hook:
            try:
                hook_result = hook.execute(notification=notification)
                if hook_result is False:  # Only prevent if explicitly False
                    return False
            except Exception as e:
                logger.error(f"Error executing NOTIFICATION_SEND hook: {str(e)}")
        
        return True
    
    def _pre_channel_send(self, channel: str, notification: Notification) -> Notification:
        """
        Apply pre-channel send hooks to a notification.
        
        Args:
            channel: The channel being used
            notification: The notification to send
            
        Returns:
            Notification: Potentially modified notification
        """
        hook = registry.get_hook(NotificationHooks.PRE_CHANNEL_SEND)
        if hook:
            try:
                hook_result = hook.execute(channel=channel, notification=notification)
                if hook_result:
                    return hook_result
            except Exception as e:
                logger.error(f"Error executing PRE_CHANNEL_SEND hook: {str(e)}")
        
        return notification
    
    def _post_channel_send(self, channel: str, notification: Notification, success: bool, error: str = "") -> None:
        """
        Apply post-channel send hooks after sending a notification.
        
        Args:
            channel: The channel used
            notification: The notification sent
            success: Whether the send was successful
            error: Error message if not successful
        """
        hook = registry.get_hook(NotificationHooks.POST_CHANNEL_SEND)
        if hook:
            try:
                hook.execute(
                    channel=channel,
                    notification=notification,
                    success=success,
                    error=error
                )
            except Exception as e:
                logger.error(f"Error executing POST_CHANNEL_SEND hook: {str(e)}")
    
    def notify_task_created(self, task: Dict[str, Any]) -> bool:
        """
        Send a notification for a task creation event.
        
        Args:
            task: The task that was created
            
        Returns:
            bool: True if the notification was sent successfully
        """
        task_id = task.get('id', '')
        task_name = task.get('name', 'Task')
        
        notification = Notification(
            subject=f"Task Created: {task_name}",
            message=f"A new task '{task_name}' was created with ID {task_id}.",
            notification_type=NotificationType.TASK_CREATED,
            data={"task": task}
        )
        
        # Apply task creation notification hook
        hook = registry.get_hook(NotificationHooks.TASK_CREATED_NOTIFICATION)
        if hook:
            try:
                hook_result = hook.execute(task=task, notification=notification)
                if hook_result:
                    notification = hook_result
            except Exception as e:
                logger.error(f"Error executing TASK_CREATED_NOTIFICATION hook: {str(e)}")
        
        return self.send_notification(notification)
    
    def notify_task_updated(self, task: Dict[str, Any], changed_fields: List[str]) -> bool:
        """
        Send a notification for a task update event.
        
        Args:
            task: The task that was updated
            changed_fields: List of fields that were changed
            
        Returns:
            bool: True if the notification was sent successfully
        """
        task_id = task.get('id', '')
        task_name = task.get('name', 'Task')
        
        notification = Notification(
            subject=f"Task Updated: {task_name}",
            message=f"Task '{task_name}' was updated. Changed fields: {', '.join(changed_fields)}",
            notification_type=NotificationType.TASK_UPDATED,
            data={"task": task, "changed_fields": changed_fields}
        )
        
        # Apply task update notification hook
        hook = registry.get_hook(NotificationHooks.TASK_UPDATED_NOTIFICATION)
        if hook:
            try:
                hook_result = hook.execute(task=task, changed_fields=changed_fields, notification=notification)
                if hook_result:
                    notification = hook_result
            except Exception as e:
                logger.error(f"Error executing TASK_UPDATED_NOTIFICATION hook: {str(e)}")
        
        return self.send_notification(notification)
    
    def notify_task_status_changed(self, task: Dict[str, Any], old_status: str, new_status: str) -> bool:
        """
        Send a notification for a task status change event.
        
        Args:
            task: The task whose status changed
            old_status: Previous status
            new_status: New status
            
        Returns:
            bool: True if the notification was sent successfully
        """
        task_id = task.get('id', '')
        task_name = task.get('name', 'Task')
        
        notification = Notification(
            subject=f"Task Status Changed: {task_name}",
            message=f"Task '{task_name}' status changed from '{old_status}' to '{new_status}'.",
            notification_type=NotificationType.TASK_STATUS_CHANGED,
            data={"task": task, "old_status": old_status, "new_status": new_status}
        )
        
        # Apply task status change notification hook
        hook = registry.get_hook(NotificationHooks.TASK_STATUS_CHANGED_NOTIFICATION)
        if hook:
            try:
                hook_result = hook.execute(
                    task=task, 
                    old_status=old_status, 
                    new_status=new_status, 
                    notification=notification
                )
                if hook_result:
                    notification = hook_result
            except Exception as e:
                logger.error(f"Error executing TASK_STATUS_CHANGED_NOTIFICATION hook: {str(e)}")
        
        return self.send_notification(notification)
    
    def get_available_channels(self) -> List[str]:
        """
        Get a list of available notification channels.
        
        Returns:
            List[str]: List of channel names
        """
        return list(self.enabled_channels)
    
    def set_default_channels(self, channels: List[str]) -> None:
        """
        Set the default notification channels.
        
        Args:
            channels: List of channel names to use by default
        """
        # Verify channels exist
        valid_channels = [channel for channel in channels if channel in self.enabled_channels]
        if not valid_channels:
            logger.warning("No valid channels specified, keeping current defaults")
            return
            
        self.default_channels = valid_channels
        logger.debug(f"Default notification channels set to: {valid_channels}")


# Global notification manager instance
notification_manager = NotificationManager() 