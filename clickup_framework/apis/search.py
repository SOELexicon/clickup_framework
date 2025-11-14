"""
Search API - Low-level API for ClickUp search endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class SearchAPI(BaseAPI):
    """Low-level API for search operations."""

    def search(self, team_id: str, query: str, **filters) -> Dict[str, Any]:
        """Search workspace."""
        params = {"query": query, **filters}
        return self._request("GET", f"team/{team_id}/search", params=params)

