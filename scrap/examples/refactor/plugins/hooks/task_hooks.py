"""
Task: tsk_3f55d115 - Update Plugins Module Comments
Document: refactor/plugins/hooks/task_hooks.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)

Used By:
    - TaskService: Executes these hooks during task lifecycle events
    - CommandSystem: Uses task hooks for CLI command validation
    - TaskManager: Triggers hooks during task processing
    - PluginManager: Allows plugins to register with these hook points

Purpose:
    Defines hook points for extending task-related operations in the
    ClickUp JSON Manager. Creates a comprehensive set of extension points
    for the task lifecycle, relationship management, validation, and rendering.

Requirements:
    - Hook points must be registered with detailed documentation
    - Hooks must be defined for all critical task operations
    - Hook naming must follow the established namespacing convention
    - CRITICAL: Task validation hooks must not bypass core validation
    - CRITICAL: Task rendering hooks must not break output formatting

Task Hook Definitions

This module defines hook points for extending task-related operations in the
ClickUp JSON Manager.
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, TypeVar, Union

from .hook_system import Hook, HookRegistry, registry


class TaskHooks:
    """
    Task operation hook points.
    
    These hooks allow plugins to extend or modify task-related operations
    such as task creation, status changes, relationship management, etc.
    """
    
    # Task CRUD operations
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_DELETED = "task.deleted"
    
    # Task status transitions
    PRE_STATUS_CHANGE = "task.pre_status_change"
    POST_STATUS_CHANGE = "task.post_status_change"
    
    # Task relationship operations
    PRE_RELATIONSHIP_ADD = "task.pre_relationship_add"
    POST_RELATIONSHIP_ADD = "task.post_relationship_add"
    PRE_RELATIONSHIP_REMOVE = "task.pre_relationship_remove"
    POST_RELATIONSHIP_REMOVE = "task.post_relationship_remove"
    
    # Task validation
    VALIDATE_TASK = "task.validate"
    VALIDATE_STATUS_TRANSITION = "task.validate_status_transition"
    VALIDATE_RELATIONSHIP = "task.validate_relationship"
    
    # Task rendering
    RENDER_TASK = "task.render"
    RENDER_TASK_DETAILS = "task.render_details"
    RENDER_TASK_LIST = "task.render_list"
    
    # Task search and filtering
    FILTER_TASKS = "task.filter"
    SEARCH_TASKS = "task.search"
    
    # Task export/import
    PRE_EXPORT_TASK = "task.pre_export"
    POST_IMPORT_TASK = "task.post_import"


# Create hooks in the registry
def _register_task_hooks() -> None:
    """Register all task hooks in the global registry."""
    
    # Task CRUD operations
    registry.create_hook(
        TaskHooks.TASK_CREATED,
        "Called after a task is created. Plugins can perform additional "
        "operations or validations on the newly created task."
    )
    
    registry.create_hook(
        TaskHooks.TASK_UPDATED,
        "Called after a task is updated. Plugins can perform additional "
        "operations or validations on the updated task."
    )
    
    registry.create_hook(
        TaskHooks.TASK_DELETED,
        "Called before a task is deleted. Plugins can perform cleanup "
        "operations or validations before deletion."
    )
    
    # Task status transitions
    registry.create_hook(
        TaskHooks.PRE_STATUS_CHANGE,
        "Called before a task's status changes. Plugins can validate the "
        "status transition and prevent it by returning False."
    )
    
    registry.create_hook(
        TaskHooks.POST_STATUS_CHANGE,
        "Called after a task's status changes. Plugins can perform additional "
        "operations or validations after the status change."
    )
    
    # Task relationship operations
    registry.create_hook(
        TaskHooks.PRE_RELATIONSHIP_ADD,
        "Called before a relationship is added between tasks. Plugins can "
        "validate the relationship and prevent it by returning False."
    )
    
    registry.create_hook(
        TaskHooks.POST_RELATIONSHIP_ADD,
        "Called after a relationship is added between tasks. Plugins can "
        "perform additional operations or validations after the relationship is added."
    )
    
    registry.create_hook(
        TaskHooks.PRE_RELATIONSHIP_REMOVE,
        "Called before a relationship is removed between tasks. Plugins can "
        "validate the removal and prevent it by returning False."
    )
    
    registry.create_hook(
        TaskHooks.POST_RELATIONSHIP_REMOVE,
        "Called after a relationship is removed between tasks. Plugins can "
        "perform additional operations or validations after the relationship is removed."
    )
    
    # Task validation
    registry.create_hook(
        TaskHooks.VALIDATE_TASK,
        "Called to validate a task. Plugins can perform additional validations "
        "and return validation errors."
    )
    
    registry.create_hook(
        TaskHooks.VALIDATE_STATUS_TRANSITION,
        "Called to validate a status transition. Plugins can perform additional "
        "validations and return validation errors."
    )
    
    registry.create_hook(
        TaskHooks.VALIDATE_RELATIONSHIP,
        "Called to validate a relationship between tasks. Plugins can perform "
        "additional validations and return validation errors."
    )
    
    # Task rendering
    registry.create_hook(
        TaskHooks.RENDER_TASK,
        "Called when rendering a task. Plugins can modify the task representation "
        "before it is rendered."
    )
    
    registry.create_hook(
        TaskHooks.RENDER_TASK_DETAILS,
        "Called when rendering task details. Plugins can add custom sections "
        "to the task details view."
    )
    
    registry.create_hook(
        TaskHooks.RENDER_TASK_LIST,
        "Called when rendering a list of tasks. Plugins can modify the list or "
        "add custom columns."
    )
    
    # Task search and filtering
    registry.create_hook(
        TaskHooks.FILTER_TASKS,
        "Called when filtering tasks. Plugins can add custom filters or modify "
        "existing filters."
    )
    
    registry.create_hook(
        TaskHooks.SEARCH_TASKS,
        "Called when searching for tasks. Plugins can add custom search criteria "
        "or modify search results."
    )
    
    # Task export/import
    registry.create_hook(
        TaskHooks.PRE_EXPORT_TASK,
        "Called before a task is exported. Plugins can modify the task data "
        "before export."
    )
    
    registry.create_hook(
        TaskHooks.POST_IMPORT_TASK,
        "Called after a task is imported. Plugins can perform additional "
        "operations or validations on the imported task."
    )


# Register all hooks
_register_task_hooks() 