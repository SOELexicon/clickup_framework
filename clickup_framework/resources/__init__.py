"""
Resources Module

High-level APIs for ClickUp operations with automatic formatting.

Phase 3: Resource APIs - Complete ✅

Provides convenient, high-level interfaces for ClickUp operations:
- TasksAPI: Task CRUD, comments, checklists, custom fields
- ListsAPI: List management and task queries
- WorkspacesAPI: Workspace, space, folder, and search operations
- TimeAPI: Time tracking with automatic formatting
- DocsAPI: Placeholder for future Docs API implementation

Each API accepts a ClickUpClient instance and provides:
- Automatic response formatting (via detail_level parameter)
- Convenience methods for common operations
- Type hints for better IDE support
- Comprehensive docstrings

Usage:
    from clickup_framework import ClickUpClient
    from clickup_framework.resources import TasksAPI, ListsAPI

    client = ClickUpClient()
    tasks = TasksAPI(client)
    lists = ListsAPI(client)

    # Get formatted task
    task = tasks.get("task_id", detail_level="summary")

    # Create and update tasks
    new_task = tasks.create(list_id="list_id", name="My Task")
    tasks.update_status(new_task['id'], "in progress")
"""

from .tasks import TasksAPI
from .lists import ListsAPI
from .workspaces import WorkspacesAPI
from .time import TimeAPI
from .docs import DocsAPI

__all__ = [
    "TasksAPI",
    "ListsAPI",
    "WorkspacesAPI",
    "TimeAPI",
    "DocsAPI",
]
