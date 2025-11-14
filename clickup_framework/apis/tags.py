"""
Tags API - Low-level API for ClickUp tag endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class TagsAPI(BaseAPI):
    """Low-level API for tag operations."""

    def get_space_tags(self, space_id: str) -> Dict[str, Any]:
        """Get all tags in a space."""
        return self._request("GET", f"space/{space_id}/tag")

    def create_space_tag(self, space_id: str, tag_name: str, tag_fg: str = "#000000", tag_bg: str = "#FFFFFF") -> Dict[str, Any]:
        """Create a tag in a space."""
        data = {"tag": {"name": tag_name, "tag_fg": tag_fg, "tag_bg": tag_bg}}
        return self._request("POST", f"space/{space_id}/tag", json=data)

    def update_space_tag(self, space_id: str, tag_name: str, **tag_updates) -> Dict[str, Any]:
        """Update a tag in a space."""
        return self._request("PUT", f"space/{space_id}/tag/{tag_name}", json=tag_updates)

    def delete_space_tag(self, space_id: str, tag_name: str) -> Dict[str, Any]:
        """Delete a tag from a space."""
        return self._request("DELETE", f"space/{space_id}/tag/{tag_name}")

    def add_task_tag(self, task_id: str, tag_name: str, **params) -> Dict[str, Any]:
        """Add a tag to a task."""
        return self._request("POST", f"task/{task_id}/tag/{tag_name}", params=params)

    def remove_task_tag(self, task_id: str, tag_name: str, **params) -> Dict[str, Any]:
        """Remove a tag from a task."""
        return self._request("DELETE", f"task/{task_id}/tag/{tag_name}", params=params)

