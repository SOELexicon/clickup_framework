"""
AttachmentsAPI - High-level API for ClickUp attachment operations

Provides convenient methods for attachment operations.
"""

from typing import Dict, Any


class AttachmentsAPI:
    """
    High-level API for ClickUp attachment operations.

    Wraps ClickUpClient methods for managing task attachments.

    Usage:
        from clickup_framework import ClickUpClient
        from clickup_framework.resources import AttachmentsAPI

        client = ClickUpClient()
        attachments = AttachmentsAPI(client)

        # Upload a file to a task
        result = attachments.create("task_id", "/path/to/file.pdf")
    """

    def __init__(self, client):
        """
        Initialize AttachmentsAPI.

        Args:
            client: ClickUpClient instance
        """
        self.client = client

    def create(self, task_id: str, file_path: str, **params) -> Dict[str, Any]:
        """
        Upload a file attachment to a task.

        Args:
            task_id: Task ID
            file_path: Path to file to upload
            **params: Additional query parameters (custom_task_ids, team_id)

        Returns:
            Attachment info (raw dict)

        Example:
            attachment = attachments.create("task_id", "/path/to/document.pdf")
            print(f"Uploaded: {attachment['title']}")
        """
        return self.client.create_task_attachment(task_id, file_path, **params)

    def link_attachments_to_comment(self, comment_id: str, attachment_ids: list) -> Dict[str, Any]:
        """
        Link attachments to a comment (required for inline image preview rendering).

        Args:
            comment_id: Comment ID to link attachments to
            attachment_ids: List of attachment IDs to link

        Returns:
            Response from API

        Note:
            This is required for inline images to render previews in comments.
            The GUI performs this as a third step after uploading and creating the comment.

        Example:
            # After creating comment with inline images
            attachments.link_attachments_to_comment(
                comment_id="90150171709926",
                attachment_ids=["6522259a-2b14-4d52-9582-0be9371be82f.png"]
            )
        """
        return self.client.attachments.link_attachments_to_comment(comment_id, attachment_ids)
