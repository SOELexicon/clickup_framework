"""
Attachments API - Low-level API for ClickUp attachment endpoints.
"""

import os
from pathlib import Path
from typing import Dict, Any
from .base import BaseAPI
from ..exceptions import (
    ClickUpAPIError,
    ClickUpAuthError,
    ClickUpNotFoundError,
)


class AttachmentsAPI(BaseAPI):
    """Low-level API for attachment operations."""

    def create_task_attachment(self, task_id: str, file_path: str, **params) -> Dict[str, Any]:
        """
        Create task attachment by uploading a file.

        Args:
            task_id: Task ID
            file_path: Path to file to upload
            **params: Additional query parameters (custom_task_ids, team_id)

        Returns:
            Attachment info

        Note:
            This method requires the file to be accessible on the local filesystem.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = Path(file_path).name

        # Temporarily remove Content-Type header for multipart/form-data
        original_headers = self.client.session.headers.copy()
        self.client.session.headers.pop('Content-Type', None)

        try:
            url = f"{self.client.BASE_URL}/task/{task_id}/attachment"
            self.client.rate_limiter.acquire()

            with open(file_path, 'rb') as f:
                files = {'attachment': (file_name, f)}
                response = self.client.session.post(
                    url,
                    files=files,
                    params=params,
                    timeout=self.client.timeout
                )

            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 401:
                # Extract actual error message from API response
                try:
                    error_data = response.json()
                    message = error_data.get("err", error_data.get("error", "Invalid or expired API token"))
                except:
                    message = response.text or "Invalid or expired API token"
                raise ClickUpAuthError(message)
            elif response.status_code == 404:
                raise ClickUpNotFoundError("task", task_id)
            else:
                try:
                    error_data = response.json()
                    message = error_data.get("err", error_data.get("error", "Unknown error"))
                except:
                    message = response.text or "Unknown error"
                raise ClickUpAPIError(response.status_code, message)
        finally:
            # Restore Content-Type header
            self.client.session.headers.update(original_headers)

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
            Uses POST /task/{task_id}/attachment with multipart/form-data.
            Sends the complete attachment JSON objects, not just IDs.
        """
        if not attachment_metadata:
            return {"success": True, "note": "No attachments to link"}

        # Temporarily remove Content-Type header for multipart/form-data
        original_headers = self.client.session.headers.copy()
        self.client.session.headers.pop('Content-Type', None)

        try:
            import json
            url = f"{self.client.BASE_URL}/task/{task_id}/attachment"
            self.client.rate_limiter.acquire()

            # Try sending attachment metadata as separate multipart fields
            # Use data for parent_id/type, files for attachment JSON
            data = {
                'parent_id': str(comment_id),
                'type': '2'
            }

            files = []
            # Add each attachment object as a JSON content-type field
            for idx, att_data in enumerate(attachment_metadata):
                att_json = json.dumps(att_data)
                files.append((f'attachment[{idx}]', (None, att_json, 'application/json')))

            response = self.client.session.post(
                url,
                data=data,
                files=files,
                timeout=self.client.timeout
            )

            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 401:
                try:
                    error_data = response.json()
                    message = error_data.get("err", error_data.get("error", "Invalid or expired API token"))
                except:
                    message = response.text or "Invalid or expired API token"
                raise ClickUpAuthError(message)
            else:
                try:
                    error_data = response.json()
                    message = error_data.get("err", error_data.get("error", "Unknown error"))
                except:
                    message = response.text or "Unknown error"
                raise ClickUpAPIError(response.status_code, message)
        finally:
            # Restore Content-Type header
            self.client.session.headers.update(original_headers)

