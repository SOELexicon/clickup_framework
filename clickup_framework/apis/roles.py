"""
Roles API - Low-level API for ClickUp role endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class RolesAPI(BaseAPI):
    """Low-level API for role operations."""

    def get_custom_roles(self, team_id: str) -> Dict[str, Any]:
        """Get custom roles for a workspace."""
        return self._request("GET", f"team/{team_id}/customroles")

