"""
Resources Module

High-level APIs for ClickUp operations with automatic formatting.

Phase 3: Resource APIs - Extended ✅

Provides convenient, high-level interfaces for ClickUp operations:
- TasksAPI: Task CRUD, comments, checklists, custom fields
- ListsAPI: List management and task queries
- WorkspacesAPI: Workspace, space, folder, custom task types, seats, and plan info
- TimeAPI: Time tracking with automatic formatting, update and delete operations
- DocsAPI: Docs and pages management
- AttachmentsAPI: File upload and attachment management
- AuthAPI: OAuth and user authentication
- CommentsAPI: Comments across tasks, lists, views, and threaded conversations
- CustomFieldsAPI: Custom fields at list, folder, space, and workspace levels
- GroupsAPI: User group management
- UsersAPI: User invitation and management
- ViewsAPI: View management across all hierarchy levels
- WebhooksAPI: Webhook lifecycle management

Each API accepts a ClickUpClient instance and provides:
- Automatic response formatting (via detail_level parameter where applicable)
- Convenience methods for common operations
- Type hints for better IDE support
- Comprehensive docstrings

Usage:
    from clickup_framework import ClickUpClient
    from clickup_framework.resources import (
        TasksAPI, ListsAPI, WorkspacesAPI, CommentsAPI, ViewsAPI
    )

    client = ClickUpClient()
    tasks = TasksAPI(client)
    comments = CommentsAPI(client)
    views = ViewsAPI(client)

    # Get formatted task
    task = tasks.get("task_id", detail_level="summary")

    # Create comment
    comments.create_task_comment("task_id", "Great work!")

    # Create view
    view = views.create_for_list("list_id", "Sprint Board", "board")
"""

from .tasks import TasksAPI
from .lists import ListsAPI
from .workspaces import WorkspacesAPI
from .time import TimeAPI
from .docs import DocsAPI
from .attachments import AttachmentsAPI
from .auth import AuthAPI
from .comments import CommentsAPI
from .custom_fields import CustomFieldsAPI
from .groups import GroupsAPI
from .users import UsersAPI
from .views import ViewsAPI
from .webhooks import WebhooksAPI

__all__ = [
    "TasksAPI",
    "ListsAPI",
    "WorkspacesAPI",
    "TimeAPI",
    "DocsAPI",
    "AttachmentsAPI",
    "AuthAPI",
    "CommentsAPI",
    "CustomFieldsAPI",
    "GroupsAPI",
    "UsersAPI",
    "ViewsAPI",
    "WebhooksAPI",
]
