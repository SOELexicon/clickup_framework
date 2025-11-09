"""
WebhooksAPI - High-level API for ClickUp webhook operations

Provides convenient methods for managing webhooks within workspaces.
"""

from typing import Dict, Any, List, Optional


class WebhooksAPI:
    """
    High-level API for ClickUp webhook operations.

    Wraps ClickUpClient methods for creating, updating, and managing webhooks.

    Usage:
        from clickup_framework import ClickUpClient
        from clickup_framework.resources import WebhooksAPI

        client = ClickUpClient()
        webhooks = WebhooksAPI(client)

        # Create a webhook
        webhook = webhooks.create(
            team_id="team_id",
            endpoint="https://myapp.com/webhook",
            events=["taskCreated", "taskUpdated"]
        )

        # Update webhook
        webhooks.update(webhook['id'], events=["taskCreated"])

        # Delete webhook
        webhooks.delete(webhook['id'])
    """

    def __init__(self, client):
        """
        Initialize WebhooksAPI.

        Args:
            client: ClickUpClient instance
        """
        self.client = client

    def get_all(self, team_id: str) -> Dict[str, Any]:
        """
        Get all webhooks for a workspace.

        Args:
            team_id: Workspace/team ID

        Returns:
            Webhooks list (raw dict)

        Example:
            webhooks_list = webhooks.get_all("team_id")
            for webhook in webhooks_list.get('webhooks', []):
                print(f"{webhook['id']}: {webhook['endpoint']}")
        """
        return self.client.get_webhooks(team_id)

    def create(
        self,
        team_id: str,
        endpoint: str,
        events: List[str],
        space_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        list_id: Optional[str] = None,
        task_id: Optional[str] = None,
        **webhook_data
    ) -> Dict[str, Any]:
        """
        Create a webhook.

        Args:
            team_id: Workspace/team ID
            endpoint: Webhook URL endpoint
            events: List of event types to subscribe to
                   (taskCreated, taskUpdated, taskDeleted, taskCommentPosted, etc.)
            space_id: Limit to specific space
            folder_id: Limit to specific folder
            list_id: Limit to specific list
            task_id: Limit to specific task
            **webhook_data: Additional webhook configuration

        Returns:
            Created webhook object (raw dict)

        Example:
            # Workspace-wide webhook
            webhook = webhooks.create(
                team_id="team_id",
                endpoint="https://myapp.com/clickup-webhook",
                events=["taskCreated", "taskUpdated", "taskDeleted"]
            )

            # List-specific webhook
            list_webhook = webhooks.create(
                team_id="team_id",
                endpoint="https://myapp.com/list-webhook",
                events=["taskCreated"],
                list_id="list_id"
            )
        """
        data = {**webhook_data}

        if space_id:
            data["space_id"] = space_id
        if folder_id:
            data["folder_id"] = folder_id
        if list_id:
            data["list_id"] = list_id
        if task_id:
            data["task_id"] = task_id

        return self.client.create_webhook(team_id, endpoint, events, **data)

    def update(
        self,
        webhook_id: str,
        endpoint: Optional[str] = None,
        events: Optional[List[str]] = None,
        status: Optional[str] = None,
        **updates
    ) -> Dict[str, Any]:
        """
        Update a webhook.

        Args:
            webhook_id: Webhook ID
            endpoint: New webhook URL endpoint
            events: New list of event types
            status: Webhook status (active, paused)
            **updates: Additional fields to update

        Returns:
            Updated webhook object (raw dict)

        Example:
            # Update events
            webhooks.update(
                webhook_id="webhook_id",
                events=["taskCreated", "taskCommentPosted"]
            )

            # Pause webhook
            webhooks.update(webhook_id="webhook_id", status="paused")

            # Reactivate webhook
            webhooks.update(webhook_id="webhook_id", status="active")
        """
        data = {**updates}

        if endpoint is not None:
            data["endpoint"] = endpoint
        if events is not None:
            data["events"] = events
        if status is not None:
            data["status"] = status

        return self.client.update_webhook(webhook_id, **data)

    def delete(self, webhook_id: str) -> Dict[str, Any]:
        """
        Delete a webhook.

        Args:
            webhook_id: Webhook ID

        Returns:
            Empty dict on success

        Example:
            webhooks.delete("webhook_id")
        """
        return self.client.delete_webhook(webhook_id)
