"""
Comments API - Low-level API for ClickUp comment endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class CommentsAPI(BaseAPI):
    """Low-level API for comment operations."""

    def create_task_comment(self, task_id: str, comment_text: str = None, comment_data: Dict[str, Any] = None, attachment_urls: list = None) -> Dict[str, Any]:
        """
        Add comment to a task.

        Args:
            task_id: Task ID
            comment_text: Plain text comment (backward compatible)
            comment_data: Rich text comment data (new format with "comment" or "comment_text" key)
            attachment_urls: List of attachment URLs to include in comment for preview (optional)

        Returns:
            Created comment
        """
        # Determine payload format
        if comment_data:
            payload = comment_data
        elif comment_text is not None:
            payload = {"comment_text": comment_text}
        else:
            raise ValueError("Either comment_text or comment_data must be provided")

        # If attachment URLs are provided, include them in the comment for preview
        # ClickUp displays image previews when images are referenced in the comment body
        # Based on ClickUp's behavior, we need to include the image URL directly in the comment
        # The GUI automatically embeds images when they're attached, so we replicate that behavior
        if attachment_urls:
            # For both comment_text and rich text formats, we'll append image references
            # ClickUp may render these as previews if the URLs point to ClickUp attachments
            images_text = "\n\n" + "\n".join([f"![image]({url})" for url in attachment_urls])
            
            if "comment_text" in payload:
                # Simple: append markdown image syntax to comment text
                payload["comment_text"] = f"{payload['comment_text']}{images_text}"
            elif "comment" in payload:
                # For rich text format, we need to add image segments
                if isinstance(payload["comment"], list):
                    # Add newline separator
                    payload["comment"].append({"text": "\n\n"})
                    # Add each image as a link (ClickUp may render as preview)
                    for url in attachment_urls:
                        # Try multiple formats that ClickUp might recognize
                        # Format 1: Plain URL (ClickUp might auto-detect as image)
                        payload["comment"].append({
                            "text": url,
                            "attributes": {"link": url}
                        })
                        # Format 2: Add newline after each image
                        payload["comment"].append({"text": "\n"})
                else:
                    # Fallback: convert to comment_text format with markdown
                    original = str(payload.get("comment", ""))
                    payload = {"comment_text": f"{original}{images_text}"}

        response = self._request(
            "POST", f"task/{task_id}/comment", json=payload
        )
        # API response doesn't include comment_text, add it for convenience
        if 'comment_text' not in response and comment_text:
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

    def update_comment(self, comment_id: str, comment_text: str = None, comment_data: Dict[str, Any] = None, **params) -> Dict[str, Any]:
        """
        Update a comment.

        Args:
            comment_id: Comment ID
            comment_text: Plain text comment (backward compatible)
            comment_data: Rich text comment data (new format)
            **params: Additional query parameters

        Returns:
            Updated comment
        """
        # Determine payload format
        if comment_data:
            payload = comment_data
        elif comment_text is not None:
            payload = {"comment_text": comment_text}
        else:
            raise ValueError("Either comment_text or comment_data must be provided")

        return self._request("PUT", f"comment/{comment_id}", json=payload, params=params)

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

