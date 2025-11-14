"""
Members API - Low-level API for ClickUp member endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class MembersAPI(BaseAPI):
    """Low-level API for member operations."""

    def get_task_members(self, task_id: str) -> Dict[str, Any]:
        """Get task members."""
        return self._request("GET", f"task/{task_id}/member")

    def get_list_members(self, list_id: str) -> Dict[str, Any]:
        """Get list members."""
        return self._request("GET", f"list/{list_id}/member")

