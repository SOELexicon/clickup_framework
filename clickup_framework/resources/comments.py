"""
CommentsAPI - High-level API for ClickUp comment operations

Provides convenient methods for managing comments across tasks, lists, and views.
"""

from typing import Dict, Any, Optional


class CommentsAPI:
    """
    High-level API for ClickUp comment operations.

    Wraps ClickUpClient methods for creating, updating, and managing comments
    across tasks, lists, views, and threaded conversations.

    Usage:
        from clickup_framework import ClickUpClient
        from clickup_framework.resources import CommentsAPI

        client = ClickUpClient()
        comments = CommentsAPI(client)

        # Task comments
        comments.create_task_comment("task_id", "Great work!")

        # List comments
        comments.create_list_comment("list_id", "Sprint review notes")

        # Threaded replies
        comments.create_reply("comment_id", "Thanks for the feedback!")
    """

    def __init__(self, client):
        """
        Initialize CommentsAPI.

        Args:
            client: ClickUpClient instance
        """
        self.client = client

    # Task comments
    def get_task_comments(self, task_id: str) -> Dict[str, Any]:
        """Get all comments on a task."""
        return self.client.get_task_comments(task_id)

    def create_task_comment(self, task_id: str, comment_text: str, notify_all: bool = False) -> Dict[str, Any]:
        """
        Create a comment on a task.

        Args:
            task_id: Task ID
            comment_text: Comment text
            notify_all: Notify all assignees (default: False)

        Returns:
            Created comment (raw dict)
        """
        # Use existing method from client
        return self.client.create_task_comment(task_id, comment_text)

    # View comments
    def get_view_comments(self, view_id: str, **params) -> Dict[str, Any]:
        """
        Get chat comments for a view.

        Args:
            view_id: View ID
            **params: Additional query parameters

        Returns:
            Comments list (raw dict)
        """
        return self.client.get_view_comments(view_id, **params)

    def create_view_comment(self, view_id: str, comment_text: str, notify_all: bool = False) -> Dict[str, Any]:
        """
        Create a chat comment on a view.

        Args:
            view_id: View ID
            comment_text: Comment text
            notify_all: Notify all members (default: False)

        Returns:
            Created comment (raw dict)
        """
        return self.client.create_view_comment(view_id, comment_text, notify_all)

    # List comments
    def get_list_comments(self, list_id: str, **params) -> Dict[str, Any]:
        """
        Get comments for a list.

        Args:
            list_id: List ID
            **params: Additional query parameters

        Returns:
            Comments list (raw dict)
        """
        return self.client.get_list_comments(list_id, **params)

    def create_list_comment(self, list_id: str, comment_text: str, notify_all: bool = False) -> Dict[str, Any]:
        """
        Create a comment on a list.

        Args:
            list_id: List ID
            comment_text: Comment text
            notify_all: Notify all members (default: False)

        Returns:
            Created comment (raw dict)
        """
        return self.client.create_list_comment(list_id, comment_text, notify_all)

    # Comment management
    def update(self, comment_id: str, comment_text: str, **params) -> Dict[str, Any]:
        """
        Update a comment.

        Args:
            comment_id: Comment ID
            comment_text: New comment text
            **params: Additional query parameters

        Returns:
            Updated comment (raw dict)
        """
        return self.client.update_comment(comment_id, comment_text, **params)

    def delete(self, comment_id: str) -> Dict[str, Any]:
        """
        Delete a comment.

        Args:
            comment_id: Comment ID

        Returns:
            Empty dict on success
        """
        return self.client.delete_comment(comment_id)

    # Threaded comments
    def get_replies(self, comment_id: str) -> Dict[str, Any]:
        """
        Get threaded/reply comments for a comment.

        Args:
            comment_id: Parent comment ID

        Returns:
            Reply comments list (raw dict)
        """
        return self.client.get_threaded_comments(comment_id)

    def create_reply(self, comment_id: str, comment_text: str, notify_all: bool = False) -> Dict[str, Any]:
        """
        Create a threaded reply to a comment.

        Args:
            comment_id: Parent comment ID
            comment_text: Reply text
            notify_all: Notify all participants (default: False)

        Returns:
            Created reply (raw dict)
        """
        return self.client.create_threaded_comment(comment_id, comment_text, notify_all)
