"""
Low-level API classes for ClickUp endpoints.

These classes contain the raw API methods organized by endpoint type.
The ClickUpClient uses these classes to organize its methods.
"""

from .base import BaseAPI
from .tasks import TasksAPI
from .lists import ListsAPI
from .folders import FoldersAPI
from .spaces import SpacesAPI
from .workspaces import WorkspacesAPI
from .goals import GoalsAPI
from .guests import GuestsAPI
from .tags import TagsAPI
from .time_tracking import TimeTrackingAPI
from .time_tracking_legacy import TimeTrackingLegacyAPI
from .members import MembersAPI
from .roles import RolesAPI
from .templates import TemplatesAPI
from .checklists import ChecklistsAPI
from .comments import CommentsAPI
from .custom_fields import CustomFieldsAPI
from .views import ViewsAPI
from .webhooks import WebhooksAPI
from .docs import DocsAPI
from .attachments import AttachmentsAPI
from .auth import AuthAPI
from .users import UsersAPI
from .groups import GroupsAPI
from .search import SearchAPI

__all__ = [
    "BaseAPI",
    "TasksAPI",
    "ListsAPI",
    "FoldersAPI",
    "SpacesAPI",
    "WorkspacesAPI",
    "GoalsAPI",
    "GuestsAPI",
    "TagsAPI",
    "TimeTrackingAPI",
    "TimeTrackingLegacyAPI",
    "MembersAPI",
    "RolesAPI",
    "TemplatesAPI",
    "ChecklistsAPI",
    "CommentsAPI",
    "CustomFieldsAPI",
    "ViewsAPI",
    "WebhooksAPI",
    "DocsAPI",
    "AttachmentsAPI",
    "AuthAPI",
    "UsersAPI",
    "GroupsAPI",
    "SearchAPI",
]

