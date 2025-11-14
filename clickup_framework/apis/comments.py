"""
Comments API - Low-level API for ClickUp comment endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class CommentsAPI(BaseAPI):
    """Low-level API for comment operations."""

    def create_task_comment(self, task_id: str, comment_text: str) -> Dict[str, Any]:
        """Add comment to a task."""
        response = self._request(
            "POST", f"task/{task_id}/comment", json={"comment_text": comment_text}
        )
        # API response doesn't include comment_text, add it for convenience
        if 'comment_text' not in response:
            response['comment_text'] = comment_text
        return response

    def get_task_comments(self, task_id: str) -> Dict[str, Any]:
        """Get all comments on a task."""
        return self._request("GET", f"task/{task_id}/comment")

    def get_view_comments(self, view_id: str, **params) -> Dict[str, Any]:
        """Get chat comments for a view."""
        return self._request("GET", f"view/{view_id}/comment", params=params)

    def create_view_comment(self, view_id: str, comment_text: str, notify_all: bool = False) -> Dict[str, Any]:
        """Create a chat comment on a view."""
        return self._request("POST", f"view/{view_id}/comment", json={
            "comment_text": comment_text,
            "notify_all": notify_all
        })

    def get_list_comments(self, list_id: str, **params) -> Dict[str, Any]:
        """Get comments for a list."""
        return self._request("GET", f"list/{list_id}/comment", params=params)

    def create_list_comment(self, list_id: str, comment_text: str, notify_all: bool = False) -> Dict[str, Any]:
        """Create a comment on a list."""
        return self._request("POST", f"list/{list_id}/comment", json={
            "comment_text": comment_text,
            "notify_all": notify_all
        })

    def update_comment(self, comment_id: str, comment_text: str, **params) -> Dict[str, Any]:
        """Update a comment."""
        return self._request("PUT", f"comment/{comment_id}", json={"comment_text": comment_text}, params=params)

    def delete_comment(self, comment_id: str) -> Dict[str, Any]:
        """Delete a comment."""
        return self._request("DELETE", f"comment/{comment_id}")

    def get_threaded_comments(self, comment_id: str) -> Dict[str, Any]:
        """Get threaded/reply comments for a comment."""
        return self._request("GET", f"comment/{comment_id}/reply")

    def create_threaded_comment(self, comment_id: str, comment_text: str, notify_all: bool = False) -> Dict[str, Any]:
        """Create a threaded reply to a comment."""
        return self._request("POST", f"comment/{comment_id}/reply", json={
            "comment_text": comment_text,
            "notify_all": notify_all
        })

