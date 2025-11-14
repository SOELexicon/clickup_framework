"""
Checklists API - Low-level API for ClickUp checklist endpoints.
"""

from typing import Dict, Any
from .base import BaseAPI


class ChecklistsAPI(BaseAPI):
    """Low-level API for checklist operations."""

    def create_checklist(self, task_id: str, name: str) -> Dict[str, Any]:
        """Create a checklist on a task."""
        response = self._request("POST", f"task/{task_id}/checklist", json={"name": name})
        # API returns {'checklist': {...}}, unwrap it
        return response.get('checklist', response)

    def update_checklist(self, checklist_id: str, **updates) -> Dict[str, Any]:
        """Update a checklist."""
        return self._request("PUT", f"checklist/{checklist_id}", json=updates)

    def delete_checklist(self, checklist_id: str) -> Dict[str, Any]:
        """Delete a checklist."""
        return self._request("DELETE", f"checklist/{checklist_id}")

    def create_checklist_item(self, checklist_id: str, name: str, **item_data) -> Dict[str, Any]:
        """Create a checklist item."""
        data = {"name": name, **item_data}
        response = self._request("POST", f"checklist/{checklist_id}/checklist_item", json=data)
        # API returns {'checklist': {...}} with items array, extract the newly created item
        if 'checklist' in response and 'items' in response['checklist']:
            items = response['checklist']['items']
            # Return the last (newest) item which should be the one we just created
            if items:
                return items[-1]
        return response

    def update_checklist_item(self, checklist_id: str, checklist_item_id: str, **updates) -> Dict[str, Any]:
        """Update a checklist item."""
        response = self._request("PUT", f"checklist/{checklist_id}/checklist_item/{checklist_item_id}", json=updates)
        # API returns {'checklist': {...}} with items array, extract the updated item
        if 'checklist' in response and 'items' in response['checklist']:
            items = response['checklist']['items']
            # Find and return the specific item that was updated
            for item in items:
                if item.get('id') == checklist_item_id:
                    return item
        return response

    def delete_checklist_item(self, checklist_id: str, checklist_item_id: str) -> Dict[str, Any]:
        """Delete a checklist item."""
        return self._request("DELETE", f"checklist/{checklist_id}/checklist_item/{checklist_item_id}")

