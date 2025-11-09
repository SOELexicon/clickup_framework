"""
Task: tsk_3f55d115 - Update Plugins Module Comments
Document: refactor/plugins/hooks/__init__.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)

Used By:
    - PluginManager: Accesses hook registry through this package
    - CoreManager: Imports hook types from this package
    - CommandSystem: Uses hook definitions for command extension points
    - CustomPlugins: Import hook interfaces from this package

Purpose:
    Provides the hook system for the ClickUp JSON Manager plugin system,
    allowing plugins to register callbacks for specific events and
    extension points throughout the application.

Requirements:
    - Must export all primary hook interfaces 
    - Must initialize the global hook registry
    - Must provide backward compatible imports
    - CRITICAL: Hook registration must be thread-safe
    - CRITICAL: Hook system must be initialized before plugin loading

ClickUp JSON Manager Hook System

This package contains the hook system for the ClickUp JSON Manager plugin system,
allowing plugins to register callbacks for specific events.
"""

from .hook_system import Hook, HookInfo, HookPriority, HookRegistry, registry
from .task_hooks import TaskHooks
from .notification_hooks import NotificationHooks


__all__ = [
    "Hook",
    "HookInfo",
    "HookPriority",
    "HookRegistry",
    "registry",
    "TaskHooks",
    "NotificationHooks",
] 