"""
Core Plugin System Package.

This package provides the foundation for the plugin system used throughout
the Core Module. It includes interfaces for creating plugins, a hook system
for event handling, and a registry for managing plugins.
"""

from refactor.plugins.core_plugin.interface import (
    CorePluginInterface,
    PluginContext,
    TaskPluginInterface,
    SearchPluginInterface,
    VisualizationPluginInterface,
    ImportExportPluginInterface,
    NotificationPluginInterface
)

from refactor.plugins.core_plugin.hook_system import (
    HookRegistry,
    HookSpecification,
    HookCaller,
    global_hook_registry,
    register_hook,
    hook_impl,
    hook_caller
)

from refactor.plugins.core_plugin.registry import (
    PluginRegistry,
    global_plugin_registry,
    register_plugin_path,
    register_plugin_class,
    get_plugin,
    get_plugins_with_capability,
    load_plugins,
    unload_plugins
)

# Convenience direct imports of example plugins
from refactor.plugins.core_plugin.example_plugin import (
    ExampleCorePlugin,
    ExampleTaskPlugin,
    ExampleSearchPlugin
)

__all__ = [
    # Interface classes
    'CorePluginInterface',
    'PluginContext',
    'TaskPluginInterface',
    'SearchPluginInterface',
    'VisualizationPluginInterface',
    'ImportExportPluginInterface',
    'NotificationPluginInterface',
    
    # Hook system
    'HookRegistry',
    'HookSpecification',
    'HookCaller',
    'global_hook_registry',
    'register_hook',
    'hook_impl',
    'hook_caller',
    
    # Plugin registry
    'PluginRegistry',
    'global_plugin_registry',
    'register_plugin_path',
    'register_plugin_class',
    'get_plugin',
    'get_plugins_with_capability',
    'load_plugins',
    'unload_plugins',
    
    # Example plugins
    'ExampleCorePlugin',
    'ExampleTaskPlugin',
    'ExampleSearchPlugin'
] 