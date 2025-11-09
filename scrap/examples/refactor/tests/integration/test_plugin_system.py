#!/usr/bin/env python3
"""
Integration tests for Plugin System interactions with Core, CLI, and Dashboard modules.

These tests verify the proper integration between the Plugin System and other modules,
ensuring plugins can be discovered, loaded, activated, and interact correctly with
the application's core functionality.
"""
import unittest
import tempfile
import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, List, Any, Optional, Set, Tuple

# Import plugin system components
from refactor.plugins.plugin_manager import PluginManager, PluginInfo, Plugin
# Commenting out imports that don't exist
# from refactor.plugins.plugin_loader import PluginLoader
# from refactor.plugins.plugin_registry import PluginRegistry
# from refactor.plugins.plugin_config import PluginConfig
from refactor.plugins.hooks.hook_system import HookRegistry
from refactor.common.exceptions import PluginError

# Import core components
from refactor.core.services.task_service import TaskService
from refactor.core.repositories.task_repository import TaskRepository

# Import CLI components
from refactor.cli.registry import CommandRegistry
# from refactor.cli.command_executor import CommandExecutor  # This doesn't exist, comment out
from refactor.cli.command import Command

# Import dashboard components
from refactor.dashboard.dashboard_manager import DashboardManager
from refactor.dashboard.dashboard_component import Component as BaseComponent

# Import storage components
from refactor.storage.providers.json_storage_provider import JsonStorageProvider
from refactor.storage.serialization.json_serializer import JsonSerializer

# Import core interfaces
from refactor.core.interfaces.core_manager import CoreManager, CoreManagerError
from refactor.core.entities.task_entity import TaskEntity, TaskStatus, TaskPriority
from refactor.core.entities.space_entity import SpaceEntity
from refactor.core.entities.folder_entity import FolderEntity
from refactor.core.entities.list_entity import ListEntity

# Comment out imports that don't exist
# from refactor.dashboard.renderers.console_renderer import ConsoleRenderer


class MockCoreManager(CoreManager):
    """Mock implementation of CoreManager for testing."""
    
    def __init__(self, task_repository):
        self.task_repository = task_repository
        self.initialized = False
        self.file_path = None
    
    def initialize(self, file_path: str) -> None:
        self.file_path = file_path
        self.initialized = True
    
    def save(self) -> None:
        pass
    
    def create_task(self, name, description="", status=None, priority=None, tags=None, parent_id=None, list_id=None):
        return self.task_repository.add(TaskEntity(
            id="tsk_" + name.lower().replace(" ", "_"),
            name=name,
            description=description,
            status=status or TaskStatus.TO_DO,
            priority=priority or TaskPriority.NORMAL,
            tags=tags or [],
            parent_id=parent_id
        ))
    
    def get_task(self, task_id: str) -> TaskEntity:
        return self.task_repository.get(task_id)
    
    def get_task_by_name(self, name: str) -> Optional[TaskEntity]:
        try:
            return self.task_repository.get_by_name(name)
        except:
            return None
    
    def update_task(self, task_id, name=None, description=None, status=None, priority=None):
        task = self.task_repository.get(task_id)
        if name is not None:
            task.name = name
        if description is not None:
            task.description = description
        if status is not None:
            task.status = status
        if priority is not None:
            task.priority = priority
        return self.task_repository.update(task)
    
    def delete_task(self, task_id: str, cascade: bool = True) -> bool:
        return self.task_repository.delete(task_id)
    
    def update_task_status(self, task_id, status, comment=None):
        task = self.task_repository.get(task_id)
        task.status = status
        return self.task_repository.update(task)
    
    # Add minimal implementations of the remaining abstract methods
    def add_comment(self, task_id, text, author):
        return {"id": "cmt_1", "text": text, "author": author}
        
    def add_tag(self, task_id, tag):
        task = self.task_repository.get(task_id)
        if tag not in task.tags:
            task.tags.append(tag)
        return self.task_repository.update(task)
        
    def remove_tag(self, task_id, tag):
        task = self.task_repository.get(task_id)
        if tag in task.tags:
            task.tags.remove(tag)
        return self.task_repository.update(task)
        
    def add_dependency(self, task_id, depends_on_id):
        return self.task_repository.get(task_id)
        
    def remove_dependency(self, task_id, depends_on_id):
        return self.task_repository.get(task_id)
        
    def get_subtasks(self, task_id):
        return self.task_repository.get_subtasks(task_id)
        
    def get_dependencies(self, task_id):
        return []
        
    def get_blocking_tasks(self, task_id):
        return []
        
    def create_checklist(self, task_id, name):
        return {"id": "cl_1", "name": name, "items": []}
        
    def add_checklist_item(self, task_id, checklist_id, name, checked=False):
        return {"id": "cli_1", "name": name, "checked": checked}
        
    def check_checklist_item(self, task_id, checklist_id, item_id, checked):
        return {"id": item_id, "checked": checked}
        
    def search_tasks(self, query, **filters):
        return []
        
    def find_by_status(self, status):
        return []
        
    def find_by_priority(self, priority):
        return []
        
    def find_by_tag(self, tag):
        return []
        
    def find_related_to(self, task_id):
        return []
        
    def create_space(self, name, description=""):
        return SpaceEntity(id="spc_1", name=name, description=description)
        
    def create_folder(self, name, space_id, description=""):
        return FolderEntity(id="fld_1", name=name, space_id=space_id, description=description)
        
    def create_list(self, name, folder_id, description=""):
        return ListEntity(id="lst_1", name=name, folder_id=folder_id, description=description)
        
    def get_spaces(self):
        return []
        
    def get_folders(self, space_id):
        return []
        
    def get_lists(self, folder_id):
        return []
        
    def get_tasks_in_list(self, list_id):
        return []

    # --- ADD DUMMY IMPLEMENTATIONS FOR MISSING ABSTRACT METHODS ---
    def add_task_to_list(self, task_id: str, list_id: str) -> None:
        pass

    def update_folder_colors(self, folder_id: str, color_mapping: Dict[str, str]) -> None:
        pass

    def update_list_colors(self, list_id: str, color_mapping: Dict[str, str]) -> None:
        pass

    def update_space_colors(self, space_id: str, color_mapping: Dict[str, str]) -> None:
        pass
    # --- END OF DUMMY IMPLEMENTATIONS ---


class PluginSystemIntegrationTests(unittest.TestCase):
    """Integration tests for Plugin System interaction with other modules."""

    def setUp(self):
        """Set up test environment with temporary test directories and files."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a plugin directory structure
        self.plugins_dir = self.temp_path / "plugins"
        self.plugins_dir.mkdir(exist_ok=True)
        
        # Create a data directory for plugin configuration and storage
        self.data_dir = self.temp_path / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # Create a test file path for task storage
        self.test_file_path = self.temp_path / "test_plugin_system.json"
        
        # Initialize empty template structure
        template_data = {
            "spaces": [
                {
                    "id": "spc_test001",
                    "name": "Test Space"
                }
            ],
            "folders": [
                {
                    "id": "fld_test001",
                    "name": "Test Folder",
                    "space_id": "spc_test001"
                }
            ],
            "lists": [
                {
                    "id": "lst_test001",
                    "name": "Test List",
                    "folder_id": "fld_test001"
                }
            ],
            "tasks": [],
            "relationships": []
        }
        
        with open(self.test_file_path, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        # Initialize storage components
        self.serializer = JsonSerializer()
        self.storage_provider = JsonStorageProvider()
        
        # Initialize repository and service
        self.task_repository = TaskRepository(self.test_file_path)
        self.task_service = TaskService(self.task_repository)
        
        # Create core manager
        self.core_manager = MockCoreManager(self.task_repository)
        
        # Initialize CLI components
        self.command_registry = CommandRegistry()
        # self.command_executor = CommandExecutor(self.command_registry)  # Comment out as it doesn't exist
        
        # Initialize dashboard components
        self.dashboard_manager = DashboardManager(self.core_manager)
        
        # Initialize plugin system components
        # Updated to use the actual PluginManager API
        self.hook_registry = HookRegistry()
        self.plugin_manager = PluginManager([str(self.plugins_dir)])
        
        # Setup test plugins
        self._setup_test_plugins()

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def _setup_test_plugins(self):
        """Set up test plugin files and directories."""
        # Create a basic test plugin
        basic_plugin_dir = self.plugins_dir / "basic_plugin"
        basic_plugin_dir.mkdir(exist_ok=True)
        
        # Create manifest.json metadata file
        plugin_metadata = {
            "id": "basic_plugin",
            "name": "Basic Plugin",
            "version": "1.0.0",
            "description": "A basic test plugin",
            "author": "Test Author",
            "entry_point": "plugin",
            "min_app_version": "0.1.0"
        }
        
        with open(basic_plugin_dir / "manifest.json", "w") as f:
            json.dump(plugin_metadata, f, indent=2)
        
        with open(basic_plugin_dir / "__init__.py", "w") as f:
            f.write("# Basic Plugin Package\n")
        
        with open(basic_plugin_dir / "plugin.py", "w") as f:
            f.write("""
import refactor.plugins.hooks as hooks
from refactor.plugins.plugin_manager import Plugin

class BasicPlugin(Plugin):
    def __init__(self, plugin_id, manager):
        super().__init__(plugin_id, manager)
        self.name = "basic_plugin"
        self.version = "1.0.0"
        self.description = "A basic test plugin"
    
    def initialize(self) -> bool:
        # Called when plugin is enabled
        return True
    
    def cleanup(self) -> bool:
        # Called when plugin is disabled
        return True

def get_plugin_class():
    return BasicPlugin
""")
        
        # Create a CLI integration plugin
        cli_plugin_dir = self.plugins_dir / "cli_plugin"
        cli_plugin_dir.mkdir(exist_ok=True)
        
        with open(cli_plugin_dir / "__init__.py", "w") as f:
            f.write("# CLI Plugin Package\n")
        
        with open(cli_plugin_dir / "plugin.py", "w") as f:
            f.write("""
import refactor.plugins.hooks as hooks

class CLIPlugin:
    def __init__(self):
        self.name = "cli_plugin"
        self.version = "1.0.0"
        self.description = "A CLI integration test plugin"
        self.author = "Test Author"
        self.min_app_version = "0.1.0"
    
    def register_hooks(self, hook_registry):
        hook_registry.register_hook("cli_command_executed", self.on_command_executed)
    
    def register_commands(self, command_registry):
        command_registry.register_command("plugin-count-tasks", self.count_tasks_command)
        command_registry.register_command("plugin-list-tags", self.list_tags_command)
    
    def on_command_executed(self, command, args, result):
        # Hook handler for command executed event
        return result
    
    def count_tasks_command(self, args, task_service=None):
        # Command to count tasks
        if task_service:
            tasks = task_service.get_all()
            return f"Total tasks: {len(tasks)}"
        return "Task service not available"
    
    def list_tags_command(self, args, task_service=None):
        # Command to list all unique tags
        if task_service:
            tasks = task_service.get_all()
            tags = set()
            for task in tasks:
                tags.update(task.tags)
            return f"Tags: {', '.join(sorted(tags))}"
        return "Task service not available"
    
    def activate(self):
        # Called when plugin is activated
        return True
    
    def deactivate(self):
        # Called when plugin is deactivated
        return True

def get_plugin_class():
    return CLIPlugin
""")
        
        # Create a dashboard integration plugin
        dashboard_plugin_dir = self.plugins_dir / "dashboard_plugin"
        dashboard_plugin_dir.mkdir(exist_ok=True)
        
        with open(dashboard_plugin_dir / "__init__.py", "w") as f:
            f.write("# Dashboard Plugin Package\n")
        
        with open(dashboard_plugin_dir / "plugin.py", "w") as f:
            f.write("""
import refactor.plugins.hooks as hooks

class DashboardPlugin:
    def __init__(self):
        self.name = "dashboard_plugin"
        self.version = "1.0.0"
        self.description = "A dashboard integration test plugin"
        self.author = "Test Author"
        self.min_app_version = "0.1.0"
    
    def register_hooks(self, hook_registry):
        hook_registry.register_hook("dashboard_component_added", self.on_component_added)
    
    def register_components(self, dashboard_manager):
        from refactor.dashboard.dashboard_component import Component as BaseComponent
        
        class TaskSummaryComponent(BaseComponent):
            def __init__(self, task_service=None):
                super().__init__("task_summary")
                self.title = "Task Summary"
                self.task_service = task_service
            
            def render(self, renderer):
                if not self.task_service:
                    return renderer.render_text("Task service not available")
                
                tasks = self.task_service.get_all()
                status_counts = {}
                for task in tasks:
                    status = task.status
                    if status not in status_counts:
                        status_counts[status] = 0
                    status_counts[status] += 1
                
                summary = "Task Summary:\\n"
                for status, count in status_counts.items():
                    summary += f"- {status}: {count}\\n"
                
                return renderer.render_text(summary)
        
        if hasattr(dashboard_manager, 'task_service'):
            dashboard_manager.add_component(TaskSummaryComponent(dashboard_manager.task_service))
        else:
            dashboard_manager.add_component(TaskSummaryComponent())
    
    def on_component_added(self, component, dashboard_manager):
        # Hook handler for component added event
        return component
    
    def activate(self):
        # Called when plugin is activated
        return True
    
    def deactivate(self):
        # Called when plugin is deactivated
        return True

def get_plugin_class():
    return DashboardPlugin
""")
        
        # Create a plugin with incompatible version
        incompatible_plugin_dir = self.plugins_dir / "incompatible_plugin"
        incompatible_plugin_dir.mkdir(exist_ok=True)
        
        with open(incompatible_plugin_dir / "__init__.py", "w") as f:
            f.write("# Incompatible Plugin Package\n")
        
        with open(incompatible_plugin_dir / "plugin.py", "w") as f:
            f.write("""
class IncompatiblePlugin:
    def __init__(self):
        self.name = "incompatible_plugin"
        self.version = "1.0.0"
        self.description = "An incompatible test plugin"
        self.author = "Test Author"
        self.min_app_version = "99.0.0"  # Incompatible version

def get_plugin_class():
    return IncompatiblePlugin
""")
    
    def test_plugin_discovery_and_loading(self):
        """Test that plugins are properly discovered and loaded."""
        # Discover plugins in the test directory
        discovered_plugins = self.plugin_manager.discover_plugins()
        
        # Verify we discovered the test plugin
        self.assertTrue(len(discovered_plugins) > 0)
        self.assertEqual("basic_plugin", discovered_plugins[0].id)
        
        # Load the basic plugin
        loaded = self.plugin_manager.load_plugin("basic_plugin")
        self.assertTrue(loaded)
        
        # Enable the plugin
        enabled = self.plugin_manager.enable_plugin("basic_plugin")
        self.assertTrue(enabled)
        
        # Check if plugin is in enabled list
        self.assertIn("basic_plugin", self.plugin_manager.enabled_plugins)
    
    def test_plugin_hooks(self):
        """Test that plugin hooks work correctly."""
        # Discover and load the test plugin
        self.plugin_manager.discover_plugins()
        self.plugin_manager.load_plugin("basic_plugin")
        self.plugin_manager.enable_plugin("basic_plugin")
        
        # Get the hook registry
        hook_registry = self.hook_registry
        
        # Create a test hook
        test_hook = hook_registry.get_or_create_hook("test_hook", "Test hook for plugin integration testing")
        
        # Register a hook handler from the plugin
        plugin_instance = self.plugin_manager.instances.get("basic_plugin")
        self.assertIsNotNone(plugin_instance, "Plugin instance should exist")
        
        # Define a simple hook handler
        def test_hook_handler(message):
            return f"Plugin processed: {message}"
        
        # Register the handler
        test_hook.register(test_hook_handler, "basic_plugin")
        
        # Execute the hook
        results = test_hook.execute("Hello from test")
        
        # Verify the hook was processed
        self.assertEqual(1, len(results))
        self.assertEqual("Plugin processed: Hello from test", results[0])
    
    def test_plugin_activation_and_lifecycle(self):
        """Test plugin activation, deactivation, and lifecycle management."""
        # Initialize plugin system
        self.plugin_manager.initialize(
            core_services={"task_service": self.task_service},
            cli_services={"command_registry": self.command_registry},
            dashboard_services={"dashboard_manager": self.dashboard_manager}
        )
        
        # Discover plugins
        self.plugin_manager.discover_plugins()
        
        # Get a plugin instance
        basic_plugin = self.plugin_manager.get_plugin("basic_plugin")
        self.assertIsNotNone(basic_plugin)
        
        # Test plugin activation
        self.plugin_manager.activate_plugin("basic_plugin")
        self.assertTrue(self.plugin_manager.is_plugin_active("basic_plugin"))
        
        # Test plugin deactivation
        self.plugin_manager.deactivate_plugin("basic_plugin")
        self.assertFalse(self.plugin_manager.is_plugin_active("basic_plugin"))
        
        # Test activating all plugins
        self.plugin_manager.activate_all_plugins()
        self.assertTrue(self.plugin_manager.is_plugin_active("basic_plugin"))
        self.assertTrue(self.plugin_manager.is_plugin_active("cli_plugin"))
        self.assertTrue(self.plugin_manager.is_plugin_active("dashboard_plugin"))
        
        # Test deactivating all plugins
        self.plugin_manager.deactivate_all_plugins()
        self.assertFalse(self.plugin_manager.is_plugin_active("basic_plugin"))
        self.assertFalse(self.plugin_manager.is_plugin_active("cli_plugin"))
        self.assertFalse(self.plugin_manager.is_plugin_active("dashboard_plugin"))
    
    def test_plugin_hook_registration_and_invocation(self):
        """Test that plugin hooks are properly registered and invoked."""
        # Initialize plugin system
        self.plugin_manager.initialize(
            core_services={"task_service": self.task_service},
            cli_services={"command_registry": self.command_registry},
            dashboard_services={"dashboard_manager": self.dashboard_manager}
        )
        
        # Discover and activate plugins
        self.plugin_manager.discover_plugins()
        self.plugin_manager.activate_all_plugins()
        
        # Verify hooks were registered
        hooks = self.hook_registry.get_all_hooks()
        
        self.assertIn("task_created", hooks)
        self.assertIn("task_updated", hooks)
        self.assertIn("dashboard_rendered", hooks)
        self.assertIn("cli_command_executed", hooks)
        self.assertIn("dashboard_component_added", hooks)
        
        # Create a test task to trigger hooks
        task = self.task_service.create_task({
            "name": "Test Hook Task",
            "description": "Testing hooks",
            "status": "to do",
            "list_id": "lst_test001",
            "tags": ["test"]
        })
        
        # Verify the hook modified the task as expected
        self.assertIn("plugin-tagged", task.tags)
        
        # Test dashboard rendering hook
        dashboard_output = "Test Dashboard Output"
        modified_output = self.hook_registry.execute_hook("dashboard_rendered", dashboard_output)
        
        self.assertIn("Modified by Basic Plugin", modified_output)
    
    def test_plugin_configuration_management(self):
        """Test plugin configuration storage and retrieval."""
        # Initialize plugin system
        self.plugin_manager.initialize(
            core_services={"task_service": self.task_service},
            cli_services={"command_registry": self.command_registry},
            dashboard_services={"dashboard_manager": self.dashboard_manager}
        )
        
        # Discover and activate plugins
        self.plugin_manager.discover_plugins()
        self.plugin_manager.activate_all_plugins()
        
        # Set configuration for a plugin
        config_data = {
            "setting1": "value1",
            "setting2": 42,
            "nested": {
                "option1": True,
                "option2": "test"
            }
        }
        
        self.plugin_manager.set_plugin_config("basic_plugin", config_data)
        
        # Get the configuration
        retrieved_config = self.plugin_manager.get_plugin_config("basic_plugin")
        
        # Verify configuration was correctly stored and retrieved
        self.assertEqual(retrieved_config, config_data)
        self.assertEqual(retrieved_config["setting1"], "value1")
        self.assertEqual(retrieved_config["setting2"], 42)
        self.assertTrue(retrieved_config["nested"]["option1"])
        
        # Update a specific setting
        self.plugin_manager.update_plugin_config("basic_plugin", {"setting1": "updated_value"})
        
        # Verify the update worked
        updated_config = self.plugin_manager.get_plugin_config("basic_plugin")
        self.assertEqual(updated_config["setting1"], "updated_value")
        self.assertEqual(updated_config["setting2"], 42)  # Other settings preserved
        
        # Test configuration persistence by creating a new manager instance
        new_plugin_config = PluginConfig(self.data_dir / "plugin_config.json")
        new_hook_registry = HookRegistry()
        new_plugin_registry = PluginRegistry()
        new_plugin_loader = PluginLoader(
            self.plugins_dir,
            new_plugin_registry,
            new_hook_registry
        )
        new_plugin_manager = PluginManager(
            new_plugin_loader,
            new_plugin_registry,
            new_hook_registry,
            new_plugin_config
        )
        
        # Load the configuration
        loaded_config = new_plugin_manager.get_plugin_config("basic_plugin")
        
        # Verify configuration was persisted
        self.assertEqual(loaded_config["setting1"], "updated_value")
        self.assertEqual(loaded_config["setting2"], 42)
    
    def test_plugin_command_integration_with_cli(self):
        """Test that plugin commands are properly integrated with CLI."""
        # Initialize PluginManager
        self.plugin_dir = self.temp_path / "plugins"
        self.plugin_dir.mkdir()
        # Add test plugin directory to manager's search paths
        self.plugin_manager = PluginManager(plugin_dirs=[str(self.plugin_dir)])

        # Initialize CoreManager
        # Assuming CoreManager now takes plugin_manager
        # Also assuming TaskRepository takes path directly
        self.task_repository = TaskRepository(self.temp_path / "tasks.json") 
        self.core_manager = CoreManager(
            task_repository=self.task_repository, 
            plugin_manager=self.plugin_manager
        )
        
        # Pre-populate with a basic valid plugin for some tests
        self._create_plugin_fixture("basic_plugin", {
            "id": "basic_plugin",
            "name": "Basic Plugin",
            "version": "1.0.0",
            "description": "A basic test plugin",
            "entry_point": "basic_plugin:BasicPlugin"
        })
        with open(self.plugin_dir / "basic_plugin" / "basic_plugin.py", "w") as f:
            f.write("""
from refactor.plugins.plugin_manager import Plugin, PluginStatus

class BasicPlugin(Plugin):
    def initialize(self):
        print(\"BasicPlugin Initialized\")
        self.initialized = True
        return True
    def cleanup(self):
        print(\"BasicPlugin Cleanup\")
        self.initialized = False
        return True
""")

    def tearDown(self):
        """Clean up temporary plugin directory."""
        # Disable plugins before cleanup if necessary
        for plugin_id in list(self.plugin_manager.enabled_plugins):
            self.plugin_manager.disable_plugin(plugin_id)
        self.temp_dir.cleanup()

    def _create_plugin_fixture(self, plugin_id, manifest_data, code=""):
        """Helper to create a plugin structure for testing."""
        plugin_path = self.plugin_dir / plugin_id
        plugin_path.mkdir(exist_ok=True) # Allow overwriting for simplicity
        # Write manifest
        with open(plugin_path / "manifest.json", "w") as f:
            json.dump(manifest_data, f)
        # Write entry point code if provided
        if code:
            # Ensure the containing directory exists before writing the file
            entry_point_module_name = manifest_data["entry_point"].split(':')[0]
            entry_point_file = entry_point_module_name + ".py"
            entry_point_path = plugin_path / entry_point_file
            entry_point_path.parent.mkdir(parents=True, exist_ok=True)
            with open(entry_point_path, "w") as f:
                f.write(code)

    def test_plugin_discovery_and_loading(self):
        """Test that plugins are properly discovered and loaded."""
        # Create another plugin fixture
        self._create_plugin_fixture("another_plugin", {
            "id": "another_plugin",
            "name": "Another Plugin",
            "version": "0.1.0",
            "description": "Another test plugin",
            "entry_point": "another:AnotherPlugin"
            })
        
        # Discover plugins
        discovered_plugins = self.plugin_manager.discover_plugins()
        # Check for at least basic_plugin and another_plugin
        discovered_ids = {p.id for p in discovered_plugins}
        self.assertIn("basic_plugin", discovered_ids)
        self.assertIn("another_plugin", discovered_ids)

        # Load a specific plugin
        load_success = self.plugin_manager.load_plugin("basic_plugin")
        self.assertTrue(load_success)
        plugin_info = self.plugin_manager.get_plugin_info("basic_plugin")
        self.assertEqual(plugin_info.status, PluginStatus.LOADED)
        self.assertIsNotNone(plugin_info.module)

    def test_plugin_activation_and_lifecycle(self):
        """Test plugin activation, deactivation, and lifecycle management."""
        # Discover and load the basic plugin first
        self.plugin_manager.discover_plugins()
        self.plugin_manager.load_plugin("basic_plugin")
        
        # Enable the plugin
        enable_success = self.plugin_manager.enable_plugin("basic_plugin")
        self.assertTrue(enable_success)
        plugin_info = self.plugin_manager.get_plugin_info("basic_plugin")
        self.assertEqual(plugin_info.status, PluginStatus.ENABLED)
        self.assertIn("basic_plugin", self.plugin_manager.enabled_plugins)
        plugin_instance = self.plugin_manager.get_plugin_instance("basic_plugin")
        self.assertIsNotNone(plugin_instance)
        self.assertTrue(plugin_instance.initialized)

        # Disable the plugin
        disable_success = self.plugin_manager.disable_plugin("basic_plugin")
        self.assertTrue(disable_success)
        plugin_info = self.plugin_manager.get_plugin_info("basic_plugin")
        # Assuming disable sets status to DISABLED
        self.assertEqual(plugin_info.status, PluginStatus.DISABLED) 
        self.assertNotIn("basic_plugin", self.plugin_manager.enabled_plugins)
        # Check cleanup effect
        self.assertFalse(plugin_instance.initialized) 
    
    def test_plugin_hook_registration_and_invocation(self):
        """Test that plugin hooks are properly registered and invoked."""
        hook_code = """
from refactor.plugins.plugin_manager import Plugin, PluginStatus
from refactor.plugins.hooks.hook_system import registry

class HookPlugin(Plugin):
    def initialize(self):
        registry.register('test_hook', self.my_hook_handler)
        print(\"HookPlugin Initialized and hook registered\")
        self.initialized = True
        return True

    def my_hook_handler(self, *args, **kwargs):
        print(f\"Hook handled: {args} {kwargs}\")
        kwargs['handled'] = True
        return kwargs

    def cleanup(self):
        registry.unregister('test_hook', self.my_hook_handler)
        print(\"HookPlugin Cleanup\")
        self.initialized = False
        return True
"""
        self._create_plugin_fixture("hook_plugin", {
            "id": "hook_plugin",
            "name": "Hook Plugin",
            "version": "1.0.0",
            "description": "Plugin for testing hooks",
            "entry_point": "hook_plugin_code:HookPlugin"
        }, code=hook_code)
        
        # Discover, load, enable
        self.plugin_manager.discover_plugins()
        self.plugin_manager.load_plugin("hook_plugin")
        self.plugin_manager.enable_plugin("hook_plugin") # Enable calls initialize

        # Trigger the hook
        from refactor.plugins.hooks.hook_system import registry
        results = registry.execute('test_hook', arg1="value1", handled=False)

        # Verify hook was executed
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
        # Assuming execute returns a list of results from handlers
        handler_result = results[0] 
        self.assertIsInstance(handler_result, dict)
        self.assertTrue(handler_result.get('handled'))

    def test_plugin_configuration_management(self):
        """Test plugin configuration storage and retrieval."""
        config_code = """
from refactor.plugins.plugin_manager import Plugin, PluginStatus

class ConfigPlugin(Plugin):
    def get_config_schema(self):
        return {
            'api_key': {'type': 'string', 'required': True},
            'timeout': {'type': 'integer', 'default': 30}
        }

    def validate_config(self, config):
        if not isinstance(config.get('api_key'), str) or len(config.get('api_key', '')) < 10:
            return False, 'API key must be a string of at least 10 characters'
        return True, None

    def initialize(self):
        # config = self.manager.get_plugin_config(self.plugin_id) # Assuming manager provides this
        # print(f\"ConfigPlugin initialized with config: {config}\")
        self.initialized = True
        return True
    
    def cleanup(self):
        self.initialized = False
        return True
"""
        self._create_plugin_fixture("config_plugin", {
            "id": "config_plugin",
            "name": "Config Plugin",
            "version": "1.0.0",
            "description": "Plugin for testing configuration",
            "entry_point": "config_plugin_code:ConfigPlugin"
        }, code=config_code)

        # Discover, load, enable
        self.plugin_manager.discover_plugins()
        self.plugin_manager.load_plugin("config_plugin")
        self.plugin_manager.enable_plugin("config_plugin") # Enable calls initialize

        # TODO: Need a way to SET configuration through PluginManager or ConfigManager
        #       This test remains incomplete until config interaction is clarified.
        pass # Placeholder until config setting is clear

    def test_plugin_command_integration_with_cli(self):
        """Test that plugin commands are properly integrated with CLI."""
        command_code = """
from refactor.plugins.plugin_manager import Plugin, PluginStatus
from refactor.cli.command import Command

class PluginCommand(Command):
    # Basic command structure assumed
    name = 'plugin-cmd'
    description = 'A test command from a plugin'
    
    def configure_parser(self, parser):
        pass # No args for this test command
        
    def execute(self, args):
        print(\"Plugin command executed!\")
        return True

class CommandPlugin(Plugin):
    def initialize(self):
        # Assuming a way to register commands with the core manager or CLI registry
        # This part depends heavily on the actual CLI/Command registration mechanism
        # Example: if core_manager has a command_registry attribute:
        # if hasattr(self.manager, 'core_manager') and hasattr(self.manager.core_manager, 'command_registry'):
        #     self.manager.core_manager.command_registry.register(PluginCommand())
        print(\"CommandPlugin Initialized\")
        self.initialized = True
        return True
        
    def cleanup(self):
        self.initialized = False
        return True
"""
        self._create_plugin_fixture("command_plugin", {
            "id": "command_plugin",
            "name": "Command Plugin",
            "version": "1.0.0",
            "description": "Plugin adding a CLI command",
            "entry_point": "command_plugin_code:CommandPlugin"
        }, code=command_code)

        # Discover, load, enable
        self.plugin_manager.discover_plugins()
        self.plugin_manager.load_plugin("command_plugin")
        self.plugin_manager.enable_plugin("command_plugin") # Enable calls initialize

        # TODO: Need to integrate with CLI execution to test this properly.
        #       This likely requires mocking or running the actual CLI entry point.
        #       Verification would involve checking if 'plugin-cmd' is listed in help
        #       or attempting to execute it.
        pass # Placeholder

    def test_plugin_component_integration_with_dashboard(self):
        """Test that plugin components are properly integrated with Dashboard."""
        component_code = """
from refactor.plugins.plugin_manager import Plugin, PluginStatus
from refactor.dashboard.dashboard_component import Component
        
class PluginComponent(Component):
            def __init__(self):
        super().__init__(component_id='plugin_component', component_type='custom')
        self.title = 'Plugin Component'
        
    def render(self, data, format_type='text'):
        if format_type == 'text':
            return f\"{self.title}: Plugin data!\"
        return '' # Add HTML/JSON rendering if needed
    
    def get_dependencies(self) -> Set[str]:
        return set() # No dependencies for this simple component

class DashboardComponentPlugin(Plugin):
    def initialize(self):
        # Assuming a way to register dashboard components
        # This depends on how DashboardManager exposes registration
        # Example: if core_manager has a dashboard_manager attribute:
        # if hasattr(self.manager, 'core_manager') and hasattr(self.manager.core_manager, 'dashboard_manager'):
        #     self.manager.core_manager.dashboard_manager.register_component(PluginComponent())
        print(\"DashboardComponentPlugin Initialized\")
        self.initialized = True
        return True
    
    def cleanup(self):
        self.initialized = False
        return True
"""
        self._create_plugin_fixture("dashboard_plugin", {
            "id": "dashboard_plugin",
            "name": "Dashboard Plugin",
            "version": "1.0.0",
            "description": "Plugin adding a dashboard component",
            "entry_point": "dashboard_plugin_code:DashboardComponentPlugin"
        }, code=component_code)
        
        # Discover, load, enable
        self.plugin_manager.discover_plugins()
        self.plugin_manager.load_plugin("dashboard_plugin")
        self.plugin_manager.enable_plugin("dashboard_plugin") # Enable calls initialize

        # TODO: Need to integrate with DashboardManager rendering to test.
        #       Verification would involve getting the DashboardManager instance
        #       and checking if 'plugin_component' exists and renders correctly.
        pass # Placeholder

    def test_error_handling_and_isolation(self):
        """Test error handling and plugin isolation during failures."""
        error_code = """
from refactor.plugins.plugin_manager import Plugin, PluginStatus

class ErrorPlugin(Plugin):
    def initialize(self):
        print(\"ErrorPlugin Initialize - Raising error\")
        self.initialized = False # Should not appear initialized
        raise ValueError(\"Initialization Error!\")
        return True # Should not be reached
    
    def cleanup(self):
        # Should not be called if initialize fails
        print(\"ErrorPlugin Cleanup Called - UNEXPECTED\") 
        return True
"""
        self._create_plugin_fixture("error_plugin", {
            "id": "error_plugin",
            "name": "Error Plugin",
            "version": "1.0.0",
            "description": "Plugin designed to fail initialization",
            "entry_point": "error_plugin_code:ErrorPlugin"
        }, code=error_code)

        # Discover and load
        self.plugin_manager.discover_plugins()
        self.plugin_manager.load_plugin("error_plugin")

        # Attempt to enable the failing plugin
        enable_success = self.plugin_manager.enable_plugin("error_plugin")
        self.assertFalse(enable_success, "Enabling a faulty plugin should fail")
        
        # Verify plugin status is ERROR
        plugin_info = self.plugin_manager.get_plugin_info("error_plugin")
        self.assertEqual(plugin_info.status, PluginStatus.ERROR)
        self.assertIn("Initialization Error!", plugin_info.error_message)
        self.assertNotIn("error_plugin", self.plugin_manager.enabled_plugins)
        
        # Ensure other plugins can still be enabled (Load basic if not already)
        # Make sure basic plugin is discovered first
        if "basic_plugin" not in self.plugin_manager.plugins:
             self.plugin_manager.discover_plugins() 
             
        if self.plugin_manager.plugins["basic_plugin"].status == PluginStatus.DISCOVERED:
             self.plugin_manager.load_plugin("basic_plugin")
             
        enable_basic_success = self.plugin_manager.enable_plugin("basic_plugin")
        self.assertTrue(enable_basic_success, "Basic plugin should still enable after error plugin failed")
        self.assertIn("basic_plugin", self.plugin_manager.enabled_plugins)
        # Verify basic plugin instance is initialized
        basic_instance = self.plugin_manager.get_plugin_instance("basic_plugin")
        self.assertTrue(basic_instance.initialized)
    
    def test_compatibility_version_checking(self):
        """Test that plugin version compatibility is correctly checked."""
        compat_code = """from refactor.plugins.plugin_manager import Plugin, PluginStatus
class CompatPlugin(Plugin):
    def initialize(self): self.initialized = True; return True
    def cleanup(self): self.initialized = False; return True
"""
        
        # Plugin requiring higher app version
        self._create_plugin_fixture("compat_plugin_min", {
            "id": "compat_plugin_min",
            "name": "Compat Plugin Min",
            "version": "1.0.0",
            "description": "Tests min app version",
            "entry_point": "compat_plugin_code:CompatPlugin",
            "min_app_version": "99.0.0" # Requires future version
        }, code=compat_code)
        
        # Plugin requiring lower app version
        self._create_plugin_fixture("compat_plugin_max", {
            "id": "compat_plugin_max",
            "name": "Compat Plugin Max",
            "version": "1.0.0",
            "description": "Tests max app version",
            "entry_point": "compat_plugin_code:CompatPlugin",
            "max_app_version": "0.1.0" # Requires past version
        }, code=compat_code)

        self.plugin_manager.discover_plugins()
        self.plugin_manager.load_plugin("compat_plugin_min")
        self.plugin_manager.load_plugin("compat_plugin_max")

        # Attempt to enable incompatible plugins
        # NOTE: This assumes version checking happens during enable_plugin
        # and that the application version is implicitly handled or mocked correctly
        # within the PluginManager's enable logic.
        enable_min_fail = self.plugin_manager.enable_plugin("compat_plugin_min")
        enable_max_fail = self.plugin_manager.enable_plugin("compat_plugin_max")
        
        self.assertFalse(enable_min_fail, "Plugin requiring higher min version should fail")
        self.assertFalse(enable_max_fail, "Plugin requiring lower max version should fail")

        plugin_info_min = self.plugin_manager.get_plugin_info("compat_plugin_min")
        plugin_info_max = self.plugin_manager.get_plugin_info("compat_plugin_max")

        self.assertIsNotNone(plugin_info_min)
        self.assertIsNotNone(plugin_info_max)
        self.assertEqual(plugin_info_min.status, PluginStatus.ERROR)
        self.assertIn("requires minimum application version", plugin_info_min.error_message)
        self.assertEqual(plugin_info_max.status, PluginStatus.ERROR)
        self.assertIn("requires maximum application version", plugin_info_max.error_message)

    def test_plugin_hooks(self):
        """Test that plugin hooks work correctly."""
        # Add hook registration/execution logic based on HookRegistry
        from refactor.plugins.hooks.hook_system import registry as hook_registry

        # Ensure basic plugin is discovered, loaded, and enabled
            self.plugin_manager.discover_plugins()
        self.plugin_manager.load_plugin("basic_plugin")
        self.plugin_manager.enable_plugin("basic_plugin")

        # Mock a hook handler within the test
        mock_handler = MagicMock()
        hook_registry.register("test_hook", mock_handler)
            
        # Execute the hook
        hook_registry.execute("test_hook", arg1="test_value")

        # Assert that the mock handler was called
        mock_handler.assert_called_once_with(arg1="test_value")

        # Cleanup: unregister the hook
        hook_registry.unregister("test_hook", mock_handler)


if __name__ == "__main__":
    # Add the project root to sys.path for discovery
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    unittest.main() 