# Notification System

The ClickUp JSON Manager includes a flexible notification system that allows sending notifications through various channels. This document explains how to use the notification system, create notification plugins, and how to leverage notification hooks.

## Overview

The notification system consists of these key components:

1. **Notification Manager** - Central component that discovers and manages notification plugins
2. **Notification Plugins** - Plugins that implement specific notification channels (Email, Slack, etc.)
3. **Notification Hooks** - Extension points that allow customizing notification behavior
4. **CLI Commands** - Command-line interface to interact with the notification system

## Using the Notification System

### From the Command Line

The CLI provides several commands for interacting with the notification system:

#### Sending Notifications

```bash
# Basic notification
./cujm send-notification "Task Updated" "The task has been updated successfully"

# Notification with type and priority
./cujm send-notification "Critical Error" "Database connection failed" \
  --type error --priority high

# Notification with specific recipients and channels
./cujm send-notification "Task Assigned" "Task assigned to John Doe" \
  --recipients john@example.com alice@example.com \
  --channels email slack

# Notification with additional data
./cujm send-notification "Task Created" "New task created" \
  --data '{"task_id": "tsk_123456", "status": "to do"}'
```

#### Managing Notification Channels

```bash
# List available notification channels
./cujm list-notification-channels

# Set default notification channels
./cujm set-default-channels email slack

# List installed notification plugins
./cujm list-notification-plugins

# List detailed plugin information
./cujm list-notification-plugins --details
```

### From Python Code

You can also use the notification system directly from Python code:

```python
from clickup_json_manager.refactor.plugins.notification import notification_manager
from clickup_json_manager.refactor.plugins.notification.notification_manager import Notification, NotificationType

# Initialize the notification manager
notification_manager.initialize()

# Create a notification
notification = Notification(
    subject="Task Updated",
    message="Task 'Implement Feature X' has been updated",
    notification_type=NotificationType.TASK_UPDATED,
    recipients=["team@example.com"],
    data={"task_id": "tsk_123456", "changes": ["status", "priority"]}
)

# Send the notification
result = notification_manager.send_notification(notification)
```

The notification manager also provides helper methods for common task-related notifications:

```python
# Task created notification
notification_manager.notify_task_created(task_data)

# Task updated notification
notification_manager.notify_task_updated(task_data, changed_fields=["status", "priority"])

# Task status changed notification
notification_manager.notify_task_status_changed(task_data, old_status="in progress", new_status="complete")
```

## Creating Notification Plugins

Notification plugins extend the `NotificationPlugin` interface and implement methods for sending notifications through specific channels.

### Plugin Structure

A notification plugin consists of at least two files:

1. **Manifest File** (`manifest.json`): Defines plugin metadata and configuration
2. **Plugin Implementation**: Python module implementing the `NotificationPlugin` interface

### Manifest File Example

```json
{
  "id": "email_notification_plugin",
  "name": "Email Notification Plugin",
  "version": "1.0.0",
  "description": "Send notifications via email (SMTP)",
  "author": "ClickUp JSON Manager Team",
  "entry_point": "email_plugin.py:EmailNotificationPlugin",
  "type": "notification",
  "requires_config": true,
  "config_schema": {
    "smtp_server": {
      "type": "string",
      "description": "SMTP server hostname",
      "default": "smtp.gmail.com",
      "required": true
    },
    "smtp_port": {
      "type": "integer",
      "description": "SMTP server port",
      "default": 587,
      "required": true
    }
    // Additional configuration options...
  }
}
```

### Plugin Implementation Example

```python
from typing import Any, Dict, List
from plugins.plugin_interface import NotificationPlugin

class EmailNotificationPlugin(NotificationPlugin):
    def __init__(self, plugin_id, manager):
        super().__init__(plugin_id, manager)
        # Initialize plugin-specific attributes
    
    def initialize(self) -> bool:
        # Initialize the plugin
        config = self.get_config()
        # Validate configuration and setup resources
        return super().initialize()
    
    def cleanup(self) -> bool:
        # Clean up resources
        return super().cleanup()
    
    def get_notification_channels(self) -> List[str]:
        # Return supported channels
        return ["email"]
    
    def send_notification(self, channel: str, message: str, options: Dict[str, Any]) -> bool:
        # Send notification through the specified channel
        if channel != "email":
            return False
            
        # Implementation for sending email
        # ...
        
        return True
    
    def get_config_schema(self) -> Dict[str, Dict[str, Any]]:
        # Return configuration schema
        return {
            "smtp_server": {
                "type": "string",
                "description": "SMTP server hostname",
                "default": "smtp.gmail.com",
                "required": True
            },
            # Additional configuration options...
        }
```

### Required Methods

1. **`get_notification_channels()`**: Returns a list of supported notification channels
2. **`send_notification()`**: Sends a notification through a specific channel
3. **`get_config_schema()`** (optional): Returns the configuration schema for the plugin

### Registering for Task Hooks

Notification plugins can register for task-related hooks to automatically send notifications when specific events occur:

```python
def initialize(self) -> bool:
    # Get configuration
    config = self.get_config()
    
    # Register for hooks
    hook_registry = self.manager.get_service("hook_registry")
    if hook_registry:
        if config.get("notify_on_create", True):
            hook_registry.get_hook(TaskHooks.TASK_CREATED).register(
                self.plugin_id, self.on_task_created
            )
        
        if config.get("notify_on_complete", True):
            hook_registry.get_hook(TaskHooks.POST_STATUS_CHANGE).register(
                self.plugin_id, self.on_status_change
            )
    
    return super().initialize()

def on_task_created(self, task):
    # Handle task creation event
    # Send notification about the created task
    pass

def on_status_change(self, task, old_status, new_status):
    # Handle task status change event
    # Only notify about completion
    if new_status.lower() == "complete":
        # Send notification about completed task
        pass
```

## Notification Hooks

The notification system provides several hooks for extending notification behavior:

### General Notification Hooks

- **`notification.send`**: Called before a notification is sent
- **`notification.received`**: Called when a notification is received from an external source

### Notification Formatting

- **`notification.format`**: Called to format a notification message
- **`notification.render`**: Called to render a notification for display

### Channel-specific Hooks

- **`notification.pre_channel_send`**: Called before sending through a specific channel
- **`notification.post_channel_send`**: Called after sending through a specific channel

### Recipient Management

- **`notification.get_recipients`**: Called to determine notification recipients
- **`notification.filter_recipients`**: Called to filter notification recipients

### Task-related Notification Hooks

- **`notification.task_created`**: Called when generating a task creation notification
- **`notification.task_updated`**: Called when generating a task update notification
- **`notification.task_status_changed`**: Called when generating a status change notification
- **`notification.task_comment_added`**: Called when generating a comment notification
- **`notification.task_assigned`**: Called when generating an assignment notification
- **`notification.task_due_soon`**: Called when generating a due date reminder
- **`notification.task_overdue`**: Called when generating an overdue notification

### Registering Hook Callbacks

Example of registering a hook callback:

```python
from plugins.hooks.notification_hooks import NotificationHooks
from plugins.hooks.hook_system import register_hook, HookPriority

@register_hook(NotificationHooks.FORMAT_NOTIFICATION, priority=HookPriority.HIGH)
def format_notification(notification):
    """Format a notification by adding a prefix to the subject."""
    notification.subject = f"[ClickUp] {notification.subject}"
    return notification

@register_hook(NotificationHooks.FILTER_RECIPIENTS)
def filter_recipients(notification, recipients):
    """Filter out certain recipients based on notification type."""
    if notification.notification_type == "ERROR":
        # Only send error notifications to admin team
        return [r for r in recipients if r.endswith("@admin.example.com")]
    return recipients
```

## Built-in Notification Plugins

The system includes example plugins for common notification channels:

### Email Notification Plugin

Sends notifications via email using SMTP:

- **Channel**: `email`
- **Configuration**: SMTP server, port, credentials, and formatting options
- **Features**: HTML formatting, task details inclusion, secure authentication

### Slack Notification Plugin

Sends notifications to Slack channels using webhooks:

- **Channel**: `slack`
- **Configuration**: Webhook URL, default channel, username, and icon
- **Features**: Rich message formatting, task field display, color-coded messages

## Advanced Topics

### Notification Manager Services

The notification manager is registered as a service and can be accessed from plugins:

```python
def initialize(self) -> bool:
    # Get notification manager service
    notification_manager = self.manager.get_service("notification_manager")
    if notification_manager:
        # Use notification manager APIs
        pass
    
    return super().initialize()
```

### Security Considerations

- Notification plugins should implement proper error handling and logging
- Sensitive configuration (passwords, API keys) should be marked as `"sensitive": true`
- Network access should be restricted to necessary hosts with `allowed_network_hosts`
- Use TLS/SSL for secure communications whenever possible

### Performance Optimization

- Implement batch notification support for high-volume scenarios
- Use asynchronous sending for non-critical notifications
- Consider rate limiting to avoid overwhelming notification channels

## Troubleshooting

Common issues and solutions:

### No Notification Channels Available

- Check that notification plugins are properly installed
- Verify plugin configuration is complete
- Ensure plugin dependencies are installed
- Check plugin initialization logs for errors

### Notifications Not Being Sent

- Verify notification manager is initialized
- Check that notification plugins are registered
- Ensure at least one notification channel is enabled
- Verify recipient list is not empty
- Check for network connectivity issues

### Task Event Notifications Not Working

- Ensure task hooks are properly registered
- Check that notification plugins are configured to handle task events
- Verify task event hook callbacks are implemented correctly 