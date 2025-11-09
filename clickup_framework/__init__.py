"""
ClickUp Framework

A modular, token-efficient framework for ClickUp API interactions.
Provides 90-95% token reduction through intelligent formatting and progressive disclosure.

Usage:
    from clickup_framework import ClickUpClient
    from clickup_framework.resources import TasksAPI

    client = ClickUpClient()
    tasks = TasksAPI(client)
    formatted_task = tasks.get(task_id, detail_level="summary")
"""

__version__ = "1.0.0-alpha"
__author__ = "ClickUp Skills Development Team"

from .client import ClickUpClient
from .exceptions import (
    ClickUpError,
    ClickUpAPIError,
    ClickUpAuthError,
    ClickUpRateLimitError,
    ClickUpNotFoundError,
)

__all__ = [
    "ClickUpClient",
    "ClickUpError",
    "ClickUpAPIError",
    "ClickUpAuthError",
    "ClickUpRateLimitError",
    "ClickUpNotFoundError",
]
