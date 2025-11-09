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

# Get version from setuptools_scm generated file
try:
    from clickup_framework._version import version as __version__
except ImportError:
    # Fallback version if _version.py doesn't exist (e.g., in dev mode before install)
    try:
        from setuptools_scm import get_version
        __version__ = get_version(root='..', relative_to=__file__)
    except (ImportError, LookupError):
        __version__ = "0.0.0+unknown"

__author__ = "ClickUp Skills Development Team"

from .client import ClickUpClient
from .context import ContextManager, get_context_manager
from .exceptions import (
    ClickUpError,
    ClickUpAPIError,
    ClickUpAuthError,
    ClickUpRateLimitError,
    ClickUpNotFoundError,
)

__all__ = [
    "ClickUpClient",
    "ContextManager",
    "get_context_manager",
    "ClickUpError",
    "ClickUpAPIError",
    "ClickUpAuthError",
    "ClickUpRateLimitError",
    "ClickUpNotFoundError",
]
