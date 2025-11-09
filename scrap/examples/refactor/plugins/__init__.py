"""
Plugins Package.

This package provides the plugin system for extending the functionality
of the ClickUp JSON Manager. Plugins can add new features, modify existing
behavior, and integrate with other systems.
"""

# Import default registries and utility functions to make them available
# at the package level
from refactor.plugins.core_plugin import (
    global_plugin_registry,
    global_hook_registry,
    register_plugin_path,
    load_plugins,
    unload_plugins
)

__all__ = [
    'global_plugin_registry',
    'global_hook_registry',
    'register_plugin_path',
    'load_plugins',
    'unload_plugins'
] 