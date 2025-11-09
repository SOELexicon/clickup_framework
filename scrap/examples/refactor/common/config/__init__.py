"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/config/__init__.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CoreManager: Uses for application configuration management
    - PluginSystem: Loads plugin configuration through this package
    - CommandSystem: Accesses command configurations
    - RESTfulAPI: Manages API configuration settings
    - StorageManager: Configures storage backends

Purpose:
    Provides a flexible configuration management system that supports
    multiple configuration sources with override capabilities, type validation,
    and hierarchical configuration structures.

Requirements:
    - Must support multiple configuration sources
    - Must respect configuration hierarchies with proper overrides
    - Configuration sources should be pluggable
    - CRITICAL: Must provide secure handling of sensitive configuration
    - CRITICAL: Must validate configuration values for type safety

Configuration Package

This package provides a configuration management system for the ClickUp JSON Manager.
"""

from .config_manager import (
    ConfigManager,
    ConfigurationSource,
    FileConfigurationSource,
    DictConfigurationSource,
    EnvironmentConfigurationSource,
    create_default_config
)

__all__ = [
    'ConfigManager',
    'ConfigurationSource',
    'FileConfigurationSource',
    'DictConfigurationSource',
    'EnvironmentConfigurationSource',
    'create_default_config'
]
