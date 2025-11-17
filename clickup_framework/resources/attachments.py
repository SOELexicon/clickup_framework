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

    def link_attachments_to_comment(self, task_id: str, comment_id: str, attachment_metadata: list = None, file_paths: list = None) -> Dict[str, Any]:
        """
        Link attachments to a comment (required for inline image preview rendering).

        Args:
            task_id: Task ID that the comment belongs to
            comment_id: Comment ID to link attachments to
            attachment_metadata: List of full attachment JSON objects from upload endpoint
            file_paths: Not used - kept for API compatibility

        Returns:
            Response from API

        Note:
            This is required for inline images to render previews in comments.
            Uses POST /task/{task_id}/attachment endpoint.
            Sends the complete attachment JSON objects.

        Example:
            # After creating comment with inline images
            # attachment_metadata is from image_metadata dict values
            attachments.link_attachments_to_comment(
                task_id="86c6j1vr6",
                comment_id="90150171709926",
                attachment_metadata=[{
                    "id": "abc123.png",
                    "version": "0",
                    "name": "image.png",
                    ...  # full attachment object
                }]
            )
        """
        return self.client.attachments.link_attachments_to_comment(task_id, comment_id, attachment_metadata=attachment_metadata, file_paths=file_paths)
