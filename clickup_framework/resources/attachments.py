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
