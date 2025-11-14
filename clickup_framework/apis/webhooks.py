"""
Webhooks API - Low-level API for ClickUp webhook endpoints.
"""

from typing import Dict, Any, List
from .base import BaseAPI


class WebhooksAPI(BaseAPI):
    """Low-level API for webhook operations."""

    def get_webhooks(self, team_id: str) -> Dict[str, Any]:
        """Get all webhooks for a workspace."""
        return self._request("GET", f"team/{team_id}/webhook")

    def create_webhook(self, team_id: str, endpoint: str, events: List[str], **webhook_data) -> Dict[str, Any]:
        """
        Create a webhook.

        Args:
            team_id: Workspace/team ID
            endpoint: Webhook URL endpoint
            events: List of event types to subscribe to
            **webhook_data: Additional webhook configuration (space_id, folder_id, list_id, task_id)

        Returns:
            Created webhook object
        """
        data = {"endpoint": endpoint, "events": events, **webhook_data}
        return self._request("POST", f"team/{team_id}/webhook", json=data)

    def update_webhook(self, webhook_id: str, **updates) -> Dict[str, Any]:
        """
        Update a webhook.

        Args:
            webhook_id: Webhook ID
            **updates: Fields to update (endpoint, events, status)

        Returns:
            Updated webhook object
        """
        return self._request("PUT", f"webhook/{webhook_id}", json=updates)

    def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook."""
        return self._request("DELETE", f"webhook/{webhook_id}")

