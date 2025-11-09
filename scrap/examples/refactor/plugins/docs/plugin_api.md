# ClickUp JSON Manager Plugin API

This document provides comprehensive documentation for the plugin API of the ClickUp JSON Manager. It covers everything developers need to know to create and integrate plugins with the system.

## Table of Contents

1. [Introduction](#introduction)
2. [Plugin Architecture](#plugin-architecture)
3. [Plugin Types](#plugin-types)
4. [Creating a Plugin](#creating-a-plugin)
5. [Hook System](#hook-system)
6. [Configuration System](#configuration-system)
7. [Sandboxing and Security](#sandboxing-and-security)
8. [Plugin Manifest](#plugin-manifest)
9. [Plugin Lifecycle](#plugin-lifecycle)
10. [Services and Dependencies](#services-and-dependencies)
11. [Best Practices](#best-practices)
12. [Examples](#examples)

## Introduction

The ClickUp JSON Manager Plugin API allows developers to extend and enhance the functionality of the ClickUp JSON Manager by creating plugins. The plugin system is designed to be:

- **Modular**: Plugins can be independently developed and deployed
- **Secure**: A sandboxing system ensures plugins can't compromise system integrity
- **Configurable**: Plugins can be configured by users to adapt to different needs
- **Extensible**: Multiple hook points allow plugins to integrate with different parts of the application

## Plugin Architecture

The plugin system architecture consists of several key components:

1. **Plugin Manager**: Handles plugin discovery, loading, and lifecycle management
2. **Hook System**: Provides points for plugins to integrate with the application
3. **Configuration System**: Manages plugin configuration and settings
4. **Sandbox System**: Ensures plugin security through isolation

Plugins are loaded from the following locations:

- System plugin directory: `[installation_path]/plugins/`
- User plugin directory: `~/.clickup_json_manager/plugins/`
- Custom plugin directories specified in the application configuration

## Plugin Types

The ClickUp JSON Manager supports several types of plugins:

| Plugin Type | Interface | Description |
|-------------|-----------|-------------|
| `TaskOperationPlugin` | `TaskOperationPlugin` | Adds new operations or modifies behavior for task operations |
| `EntityTypePlugin` | `EntityTypePlugin` | Adds support for new entity types in the template system |
| `VisualizationPlugin` | `VisualizationPlugin` | Provides new visualization options for dashboards |
| `IntegrationPlugin` | `IntegrationPlugin` | Integrates with external systems and services |
| `StoragePlugin` | `StoragePlugin` | Provides alternative storage backends for templates |
| `CommandPlugin` | `CommandPlugin` | Adds new CLI commands to the application |
| `FilterPlugin` | `FilterPlugin` | Adds custom filtering capabilities |
| `UtilityPlugin` | `UtilityPlugin` | Provides utility functions and helpers |
| `ThemePlugin` | `ThemePlugin` | Customizes the application's appearance |

Plugins can implement multiple interfaces to provide combined functionality.

## Creating a Plugin

### Basic Structure

A plugin consists of at least two files:

1. A manifest file (`manifest.json`) that describes the plugin
2. A Python module with a class that implements a plugin interface

### Plugin Module

Here's a basic example of a plugin module:

```python
from clickup_json_manager.plugins.plugin_interface import TaskOperationPlugin
from clickup_json_manager.plugins.plugin_manager import Plugin

class MyTaskPlugin(TaskOperationPlugin):
    def __init__(self, plugin_id, manager):
        super().__init__(plugin_id, manager)
        self.register_handlers()
    
    def initialize(self) -> bool:
        # Get registry from the plugin manager
        hook_registry = self.manager.get_service("hook_registry")
        
        # Register for hooks
        if hook_registry:
            hook_registry.get_hook("task.created").register(
                self.plugin_id, self.on_task_created
            )
        
        return super().initialize()
    
    def cleanup(self) -> bool:
        # Clean up hook registrations
        hook_registry = self.manager.get_service("hook_registry")
        if hook_registry:
            hook_registry.unregister_hooks(self.plugin_id)
        
        return super().cleanup()
    
    def on_task_created(self, task):
        # Handle task creation
        print(f"Task created: {task['id']}")
```

### Plugin Installation

To install a plugin:

1. Package your plugin (manifest and Python modules) into a directory
2. Place it in one of the plugin directories
3. Restart the ClickUp JSON Manager or reload plugins

## Hook System

The hook system allows plugins to register callbacks for specific events in the application.

### Available Hooks

| Hook Name | Description | Arguments |
|-----------|-------------|-----------|
| `TaskHooks.TASK_CREATED` | Triggered when a task is created | `task` |
| `TaskHooks.TASK_UPDATED` | Triggered when a task is updated | `task`, `changed_fields` |
| `TaskHooks.TASK_DELETED` | Triggered when a task is deleted | `task_id` |
| `TaskHooks.PRE_STATUS_CHANGE` | Triggered before a task status changes | `task`, `old_status`, `new_status` |
| `TaskHooks.POST_STATUS_CHANGE` | Triggered after a task status changes | `task`, `old_status`, `new_status` |
| `TaskHooks.TASK_SELECTED` | Triggered when a task is selected in the UI | `task` |
| `TaskHooks.TASK_DESELECTED` | Triggered when a task is deselected in the UI | `task` |
| `TemplateHooks.TEMPLATE_LOADED` | Triggered when a template is loaded | `template` |
| `TemplateHooks.TEMPLATE_SAVED` | Triggered when a template is saved | `template`, `path` |
| `UiHooks.DASHBOARD_INIT` | Triggered when the dashboard is initialized | `dashboard` |
| `FilterHooks.FILTER_APPLIED` | Triggered when a filter is applied | `filter_spec`, `results` |

### Registering a Hook

To register a callback for a hook:

```python
def initialize(self) -> bool:
    hook_registry = self.manager.get_service("hook_registry")
    if hook_registry:
        hook_registry.get_hook(TaskHooks.TASK_CREATED).register(
            self.plugin_id, self.on_task_created, priority=HookPriority.NORMAL
        )
    return super().initialize()
```

### Hook Priority

Hooks can specify a priority to control execution order:

- `HookPriority.HIGHEST` (100): Executes first
- `HookPriority.HIGH` (75): Executes early
- `HookPriority.NORMAL` (50): Default execution order
- `HookPriority.LOW` (25): Executes late
- `HookPriority.LOWEST` (0): Executes last

### Creating Custom Hooks

Plugins can create and expose their own hooks for other plugins to use:

```python
def initialize(self) -> bool:
    hook_registry = self.manager.get_service("hook_registry")
    if hook_registry:
        # Create a new hook
        self.my_custom_hook = hook_registry.create_hook("my_plugin.custom_event")
    return super().initialize()

def trigger_custom_event(self, data):
    # Trigger the hook
    self.my_custom_hook.execute(data)
```

## Configuration System

The configuration system allows plugins to define, validate, and use configuration settings.

### Defining Configuration Schema

Define a configuration schema in your plugin class:

```python
def get_config_schema(self) -> Dict[str, Dict[str, Any]]:
    return {
        "api_key": {
            "type": "string",
            "description": "API key for the service",
            "required": True
        },
        "sync_interval": {
            "type": "integer",
            "description": "Sync interval in minutes",
            "default": 30,
            "minimum": 5,
            "maximum": 1440
        },
        "enabled_features": {
            "type": "array",
            "description": "List of enabled features",
            "default": ["basic"],
            "items": {
                "type": "string",
                "enum": ["basic", "advanced", "experimental"]
            }
        }
    }
```

### Validating Configuration

You can validate configuration values:

```python
def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    if "api_key" not in config or not config["api_key"]:
        return False, "API key is required"
    
    return True, None
```

### Accessing Configuration

Access configuration values in your plugin:

```python
def some_method(self):
    config = self.get_config()
    api_key = config.get("api_key")
    sync_interval = config.get("sync_interval", 30)
    
    # Use the configuration values
    # ...
```

## Sandboxing and Security

The plugin system includes a sandboxing mechanism to restrict plugin capabilities based on security levels.

### Security Levels

The following security levels are available:

- `SecurityLevel.UNTRUSTED`: Maximum restrictions, minimal capabilities
- `SecurityLevel.LOW_TRUST`: Many restrictions, basic capabilities
- `SecurityLevel.MEDIUM_TRUST`: Balanced restrictions/capabilities
- `SecurityLevel.HIGH_TRUST`: Few restrictions, extensive capabilities
- `SecurityLevel.FULL_TRUST`: No restrictions (internal plugins only)

### Sandbox Restrictions

Depending on the security level, plugins may be restricted in:

- File system access (read/write)
- Network access
- Module imports
- External process execution
- Memory and CPU usage

### Sandboxed Method Decorator

Use the `@sandboxed` decorator to explicitly run methods in a sandbox:

```python
from clickup_json_manager.plugins.sandbox import sandboxed, SecurityLevel

class MyPlugin(UtilityPlugin):
    # ...
    
    @sandboxed(security_level=SecurityLevel.LOW_TRUST)
    def process_data(self, data):
        # This method will run with LOW_TRUST restrictions
        # ...
```

## Plugin Manifest

The plugin manifest (`manifest.json`) contains metadata about the plugin and is used by the plugin manager during loading.

### Manifest Structure

```json
{
  "id": "my_task_plugin",
  "name": "My Task Plugin",
  "version": "1.0.0",
  "description": "Adds custom behavior to tasks",
  "author": "Your Name",
  "entry_point": "my_plugin.py:MyTaskPlugin",
  "type": "task_operation",
  "min_app_version": "2.0.0",
  "enabled_by_default": true,
  "requires_config": true,
  "dependencies": ["other_plugin_id"],
  "tags": ["task", "automation"],
  "icon": "task_icon.png",
  "permissions": ["network", "storage"],
  "security_level": "medium_trust",
  "allowed_imports": ["requests", "urllib"],
  "allowed_paths": ["data"],
  "allowed_network_hosts": ["api.example.com"],
  "config_schema": {
    // Same format as get_config_schema()
  }
}
```

### Manifest Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String | Yes | Unique identifier for the plugin |
| `name` | String | Yes | Human-readable name |
| `version` | String | Yes | Semantic version of the plugin |
| `description` | String | Yes | Description of the plugin's purpose and features |
| `author` | String | Yes | Plugin author or organization |
| `entry_point` | String | Yes | Path to plugin class within module |
| `type` | String | Yes | Primary plugin type |
| `min_app_version` | String | No | Minimum app version required |
| `enabled_by_default` | Boolean | No | Whether the plugin is enabled by default |
| `requires_config` | Boolean | No | Whether configuration is required |
| `dependencies` | Array | No | List of plugin IDs this plugin depends on |
| `tags` | Array | No | Categorization tags |
| `icon` | String | No | Path to plugin icon relative to plugin directory |
| `permissions` | Array | No | List of permissions requested |
| `security_level` | String | No | Requested security level |
| `allowed_imports` | Array | No | Additional modules the plugin needs to import |
| `allowed_paths` | Array | No | Additional paths the plugin needs to access |
| `allowed_network_hosts` | Array | No | Network hosts the plugin needs to access |
| `config_schema` | Object | No | Configuration schema (optional, can be in code) |

## Plugin Lifecycle

The lifecycle of a plugin consists of the following stages:

1. **Discovery**: Plugin is found by the plugin manager
2. **Loading**: Plugin manifest is read and validated
3. **Initialization**: Plugin's `initialize()` method is called
4. **Operation**: Plugin operates during application runtime
5. **Cleanup**: Plugin's `cleanup()` method is called during shutdown or reload
6. **Unloading**: Plugin is removed from memory

### Lifecycle Methods

Implement these methods to control your plugin's lifecycle:

```python
def initialize(self) -> bool:
    """Called when the plugin is being initialized."""
    # Set up resources, register hooks, etc.
    return True  # Return True on success, False on failure

def cleanup(self) -> bool:
    """Called when the plugin is being unloaded."""
    # Clean up resources, unregister hooks, etc.
    return True  # Return True on success, False on failure
```

## Services and Dependencies

Plugins can use services provided by the core application and define dependencies on other plugins.

### Using Services

Services are global objects that provide functionality:

```python
def some_method(self):
    # Get a service from the plugin manager
    hook_registry = self.manager.get_service("hook_registry")
    config_manager = self.manager.get_service("config_manager")
    
    # Use the services
    # ...
```

### Available Services

The following services are available to plugins:

| Service Name | Description |
|--------------|-------------|
| `hook_registry` | Registry for creating and using hooks |
| `config_manager` | Manager for plugin configurations |
| `sandbox_manager` | Manager for plugin sandboxing |
| `template_manager` | Manager for template operations |
| `filter_manager` | Manager for filter operations |
| `ui_manager` | Manager for UI components |
| `plugin_manager` | The plugin manager itself |

### Plugin Dependencies

Plugins can depend on other plugins. Dependencies are specified in the manifest:

```json
{
  "id": "my_plugin",
  "dependencies": ["other_plugin", "another_plugin"]
}
```

To access another plugin:

```python
def some_method(self):
    # Get another plugin instance
    other_plugin = self.manager.get_plugin("other_plugin")
    
    # Use the plugin if available
    if other_plugin and other_plugin.is_enabled():
        other_plugin.some_public_method()
```

## Best Practices

### Plugin Design

1. **Single Responsibility**: Each plugin should have a clear, focused purpose
2. **Minimal Dependencies**: Limit dependencies on other plugins
3. **Graceful Degradation**: Handle cases where dependencies or services are unavailable
4. **Clear Configuration**: Provide clear descriptions and defaults for configuration options
5. **Error Handling**: Catch and log exceptions to prevent plugin failures from affecting the application

### Security

1. **Request Minimal Permissions**: Only request the permissions your plugin actually needs
2. **Validate Inputs**: Validate all inputs, especially those from external sources
3. **Use Sandboxed Methods**: Use the `@sandboxed` decorator for methods that process external data
4. **Secure Credentials**: Do not hardcode sensitive information like API keys

### Performance

1. **Efficient Hook Usage**: Register only for hooks your plugin actually needs
2. **Lazy Loading**: Load resources only when needed
3. **Clean Up Resources**: Release resources in the `cleanup()` method
4. **Batch Processing**: Process data in batches when possible

## Examples

### Task Operation Plugin

```python
from clickup_json_manager.plugins.plugin_interface import TaskOperationPlugin
from clickup_json_manager.plugins.hooks.task_hooks import TaskHooks

class TaskAutoTagPlugin(TaskOperationPlugin):
    def __init__(self, plugin_id, manager):
        super().__init__(plugin_id, manager)
    
    def initialize(self) -> bool:
        hook_registry = self.manager.get_service("hook_registry")
        if hook_registry:
            hook_registry.get_hook(TaskHooks.TASK_CREATED).register(
                self.plugin_id, self.on_task_created
            )
        return super().initialize()
    
    def on_task_created(self, task):
        # Auto-tag tasks based on content
        description = task.get("description", "").lower()
        title = task.get("name", "").lower()
        
        tags = task.get("tags", [])
        
        if "bug" in title or "bug" in description:
            tags.append("bug")
        
        if "feature" in title or "feature" in description:
            tags.append("feature")
        
        # Update the task with new tags
        if len(tags) > len(task.get("tags", [])):
            task["tags"] = list(set(tags))  # Remove duplicates
            # Task would now be updated in the template
```

### Integration Plugin

```python
from clickup_json_manager.plugins.plugin_interface import IntegrationPlugin
from clickup_json_manager.plugins.hooks.task_hooks import TaskHooks

class SlackNotificationPlugin(IntegrationPlugin):
    def __init__(self, plugin_id, manager):
        super().__init__(plugin_id, manager)
        self.slack_client = None
    
    def get_config_schema(self):
        return {
            "webhook_url": {
                "type": "string",
                "description": "Slack webhook URL",
                "required": True
            },
            "channel": {
                "type": "string",
                "description": "Slack channel name",
                "default": "#general"
            },
            "notify_on_create": {
                "type": "boolean",
                "description": "Send notification when tasks are created",
                "default": True
            },
            "notify_on_complete": {
                "type": "boolean",
                "description": "Send notification when tasks are completed",
                "default": True
            }
        }
    
    def initialize(self) -> bool:
        # Initialize Slack client
        config = self.get_config()
        if not config.get("webhook_url"):
            return False
        
        # In a real plugin, this would use a proper Slack library
        self.slack_client = {
            "webhook_url": config.get("webhook_url"),
            "channel": config.get("channel", "#general")
        }
        
        # Register hooks
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
        if self.slack_client:
            message = f"New task created: {task.get('name')} ({task.get('id')})"
            self.send_slack_message(message)
    
    def on_status_change(self, task, old_status, new_status):
        if new_status == "complete" and self.slack_client:
            message = f"Task completed: {task.get('name')} ({task.get('id')})"
            self.send_slack_message(message)
    
    def send_slack_message(self, message):
        # In a real plugin, this would use a proper Slack API call
        print(f"Sending to Slack ({self.slack_client['channel']}): {message}")
```

This documentation provides a comprehensive reference for plugin developers. For more specific examples and tutorials, see the examples directory in the plugin SDK.

## Support and Feedback

If you encounter issues or have suggestions for improving the plugin API, please:

1. Check the GitHub repository for existing issues
2. Submit a new issue with details about your problem or suggestion
3. Consider contributing with a pull request

The plugin API is continuously evolving, and your feedback helps improve it for all developers. 