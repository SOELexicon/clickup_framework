"""
Templates API - Low-level API for ClickUp template endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class TemplatesAPI(BaseAPI):
    """Low-level API for template operations."""

    def get_custom_task_types(self, team_id: str) -> Dict[str, Any]:
        """Get custom task types for a workspace."""
        return self._request("GET", f"team/{team_id}/custom_item")

    def get_task_templates(self, team_id: str) -> Dict[str, Any]:
        """Get task templates for a workspace."""
        return self._request("GET", f"team/{team_id}/taskTemplate")

