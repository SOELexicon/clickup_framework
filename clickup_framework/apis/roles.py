"""
Roles API - Low-level API for ClickUp role endpoints.
"""

from typing import Dict, Any, Optional
from .base import BaseAPI


class RolesAPI(BaseAPI):
    """Low-level API for role operations."""

    def get_custom_roles(
        self, team_id: str, include_members: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Get custom roles for a workspace.

        Args:
            team_id: Workspace/team ID
            include_members: ClickUp omits each role's member list unless
                this is explicitly True -- without it, every role's
                `members` field comes back empty regardless of actual
                assignments.
        """
        params = {}
        if include_members is not None:
            params["include_members"] = include_members
        return self._request("GET", f"team/{team_id}/customroles", params=params or None)

