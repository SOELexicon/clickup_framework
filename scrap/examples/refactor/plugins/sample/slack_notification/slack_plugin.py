"""
Slack Notification Plugin

This plugin sends notifications to Slack channels using webhooks.
"""

import json
import logging
import requests
from typing import Any, Dict, List, Optional, Tuple

from ....common.exceptions import PluginError
from ...hooks.notification_hooks import NotificationHooks
from ...hooks.task_hooks import TaskHooks
from ...plugin_interface import NotificationPlugin


logger = logging.getLogger(__name__)


class SlackNotificationPlugin(NotificationPlugin):
    """
    Slack notification plugin for ClickUp JSON Manager.
    
    This plugin allows sending notifications to Slack channels using webhooks.
    """
    
    def __init__(self, plugin_id: str, manager: 'PluginManager'):
        """Initialize the Slack notification plugin."""
        super().__init__(plugin_id, manager)
        self.webhook_url = None
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        config = self.get_config()
        
        # Validate required configuration
        if not config.get("webhook_url"):
            logger.error("Missing required configuration: webhook_url")
            return False
        
        self.webhook_url = config.get("webhook_url")
        
        # Register hooks
        hook_registry = self.manager.get_service("hook_registry")
        if hook_registry:
            # Register for task hooks based on configuration
            if config.get("notify_on_create", True):
                hook_registry.get_hook(TaskHooks.TASK_CREATED).register(
                    self.plugin_id, self.on_task_created, priority="HIGH"
                )
            
            if config.get("notify_on_update", False):
                hook_registry.get_hook(TaskHooks.TASK_UPDATED).register(
                    self.plugin_id, self.on_task_updated, priority="NORMAL"
                )
            
            if config.get("notify_on_complete", True):
                hook_registry.get_hook(TaskHooks.POST_STATUS_CHANGE).register(
                    self.plugin_id, self.on_status_change, priority="NORMAL"
                )
        
        logger.info("Slack notification plugin initialized")
        return super().initialize()
    
    def cleanup(self) -> bool:
        """
        Clean up resources used by the plugin.
        
        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        # Unregister hooks
        hook_registry = self.manager.get_service("hook_registry")
        if hook_registry:
            hook_registry.unregister_hooks(self.plugin_id)
        
        return super().cleanup()
    
    def get_notification_channels(self) -> List[str]:
        """
        Get the notification channels supported by this plugin.
        
        Returns:
            List[str]: Names of supported notification channels
        """
        return ["slack"]
    
    def send_notification(self, channel: str, message: str, options: Dict[str, Any]) -> bool:
        """
        Send a notification using Slack webhook.
        
        Args:
            channel: Notification channel to use
            message: Notification message
            options: Notification options
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise
        """
        if channel != "slack":
            logger.warning(f"Unsupported notification channel: {channel}")
            return False
            
        config = self.get_config()
        
        # Get options
        subject = options.get("subject", "Notification from ClickUp JSON Manager")
        notification_type = options.get("notification_type", "info")
        
        # Determine color
        color_mapping = config.get("color_mapping", {})
        color = color_mapping.get(
            notification_type.lower() if isinstance(notification_type, str) else "info", 
            "#2196f3"  # Default blue
        )
        
        # Create payload
        payload = self._create_slack_payload(subject, message, color, options)
        
        # Send the notification
        try:
            self._send_to_slack(payload)
            logger.info("Slack notification sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return False
    
    def _create_slack_payload(
        self, 
        subject: str, 
        message: str,
        color: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a Slack message payload.
        
        Args:
            subject: Notification subject/title
            message: Notification message
            color: Color for the message attachment
            options: Additional options
            
        Returns:
            Dict[str, Any]: Slack message payload
        """
        config = self.get_config()
        
        # Get slack-specific options
        channel = options.get("channel", config.get("default_channel"))
        username = config.get("username", "ClickUp JSON Manager")
        icon_emoji = config.get("icon_emoji", ":clipboard:")
        icon_url = config.get("icon_url")
        
        # Build attachments
        attachments = [{
            "title": subject,
            "text": message,
            "color": color,
            "mrkdwn_in": ["text"]
        }]
        
        # Add task details if available and enabled
        if config.get("include_task_details", True) and options.get("data", {}).get("task"):
            task = options["data"]["task"]
            
            # Build fields for task details
            fields = [
                {
                    "title": "ID",
                    "value": task.get("id", "N/A"),
                    "short": True
                },
                {
                    "title": "Status",
                    "value": task.get("status", "N/A"),
                    "short": True
                },
                {
                    "title": "Priority",
                    "value": str(task.get("priority", "N/A")),
                    "short": True
                }
            ]
            
            # Add old and new status if available for status changes
            if options["data"].get("old_status") and options["data"].get("new_status"):
                fields.append({
                    "title": "Status Change",
                    "value": f"{options['data']['old_status']} → {options['data']['new_status']}",
                    "short": True
                })
            
            # Add fields to the first attachment
            attachments[0]["fields"] = fields
        
        # Create the full payload
        payload = {
            "username": username,
            "attachments": attachments
        }
        
        # Add channel if specified
        if channel:
            payload["channel"] = channel
            
        # Add icon
        if icon_url:
            payload["icon_url"] = icon_url
        elif icon_emoji:
            payload["icon_emoji"] = icon_emoji
            
        return payload
    
    def _send_to_slack(self, payload: Dict[str, Any]) -> None:
        """
        Send a payload to Slack.
        
        Args:
            payload: Slack message payload
            
        Raises:
            PluginError: If the Slack API request fails
        """
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                error_msg = f"Slack API returned {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise PluginError(error_msg)
                
            if response.text != "ok":
                error_msg = f"Slack API returned unexpected response: {response.text}"
                logger.error(error_msg)
                raise PluginError(error_msg)
                
        except requests.RequestException as e:
            raise PluginError(f"Request to Slack API failed: {str(e)}")
    
    def on_task_created(self, task: Dict[str, Any]) -> None:
        """
        Handle task creation events.
        
        Args:
            task: Created task data
        """
        task_name = task.get("name", "Task")
        task_id = task.get("id", "unknown")
        
        notification_manager = self.manager.get_service("notification_manager")
        if notification_manager:
            notification_manager.notify_task_created(task)
        else:
            # Fall back to direct notification if manager not available
            self.send_notification(
                "slack",
                f"Task '{task_name}' was created.",
                {
                    "subject": f"Task Created: {task_name}",
                    "notification_type": "task_created",
                    "data": {"task": task}
                }
            )
    
    def on_task_updated(self, task: Dict[str, Any], changed_fields: List[str]) -> None:
        """
        Handle task update events.
        
        Args:
            task: Updated task data
            changed_fields: List of fields that were changed
        """
        task_name = task.get("name", "Task")
        
        notification_manager = self.manager.get_service("notification_manager")
        if notification_manager:
            notification_manager.notify_task_updated(task, changed_fields)
        else:
            # Fall back to direct notification if manager not available
            self.send_notification(
                "slack",
                f"Task '{task_name}' was updated.\nChanged fields: {', '.join(changed_fields)}",
                {
                    "subject": f"Task Updated: {task_name}",
                    "notification_type": "task_updated",
                    "data": {"task": task, "changed_fields": changed_fields}
                }
            )
    
    def on_status_change(self, task: Dict[str, Any], old_status: str, new_status: str) -> None:
        """
        Handle task status change events.
        
        Args:
            task: Task data
            old_status: Previous status
            new_status: New status
        """
        task_name = task.get("name", "Task")
        
        # Only notify for completion if configured
        config = self.get_config()
        if new_status.lower() == "complete" and not config.get("notify_on_complete", True):
            return
            
        notification_manager = self.manager.get_service("notification_manager")
        if notification_manager:
            notification_manager.notify_task_status_changed(task, old_status, new_status)
        else:
            # Fall back to direct notification if manager not available
            notification_type = "task_completed" if new_status.lower() == "complete" else "task_status_changed"
            
            self.send_notification(
                "slack",
                f"Task '{task_name}' status changed from '{old_status}' to '{new_status}'.",
                {
                    "subject": f"Task Status Changed: {task_name}",
                    "notification_type": notification_type,
                    "data": {
                        "task": task,
                        "old_status": old_status,
                        "new_status": new_status
                    }
                }
            )
    
    def get_config_schema(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the configuration schema for this plugin.
        
        Returns:
            Dict[str, Dict[str, Any]]: Configuration schema
        """
        return {
            "webhook_url": {
                "type": "string",
                "description": "Slack webhook URL for the workspace",
                "required": True,
                "sensitive": True
            },
            "default_channel": {
                "type": "string",
                "description": "Default channel to send notifications to",
                "default": "#general"
            },
            "username": {
                "type": "string",
                "description": "Username to display for notifications",
                "default": "ClickUp JSON Manager"
            },
            "icon_emoji": {
                "type": "string",
                "description": "Emoji to use as the icon (e.g., :clipboard:)",
                "default": ":clipboard:"
            },
            "icon_url": {
                "type": "string",
                "description": "URL to an image to use as the icon (overrides icon_emoji)"
            },
            "notify_on_create": {
                "type": "boolean",
                "description": "Send notification when tasks are created",
                "default": True
            },
            "notify_on_update": {
                "type": "boolean",
                "description": "Send notification when tasks are updated",
                "default": False
            },
            "notify_on_complete": {
                "type": "boolean",
                "description": "Send notification when tasks are completed",
                "default": True
            },
            "include_task_details": {
                "type": "boolean",
                "description": "Include detailed task information in notifications",
                "default": True
            },
            "color_mapping": {
                "type": "object",
                "description": "Color mapping for different notification types",
                "default": {
                    "task_created": "#36a64f",
                    "task_updated": "#2196f3",
                    "task_status_changed": "#ff9800",
                    "task_completed": "#8bc34a",
                    "error": "#f44336",
                    "warning": "#ff9800",
                    "info": "#2196f3"
                }
            }
        } 