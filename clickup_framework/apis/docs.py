"""
Docs API - Low-level API for ClickUp docs endpoints (v3).
"""

from typing import Dict, Any, Optional
from .base import BaseAPI


class DocsAPI(BaseAPI):
    """Low-level API for docs operations (v3 endpoints)."""

    def get_workspace_docs(self, workspace_id: str, **params) -> Dict[str, Any]:
        """Get all docs in a workspace."""
        return self._request("GET", f"/v3/workspaces/{workspace_id}/docs", params=params)

    def create_doc(self, workspace_id: str, name: str, **doc_data) -> Dict[str, Any]:
        """Create a new doc in workspace."""
        data = {"name": name, **doc_data}
        return self._request("POST", f"/v3/workspaces/{workspace_id}/docs", json=data)

    def get_doc(self, workspace_id: str, doc_id: str) -> Dict[str, Any]:
        """Get doc by ID."""
        return self._request("GET", f"/v3/workspaces/{workspace_id}/docs/{doc_id}")

    def get_doc_pages(self, workspace_id: str, doc_id: str, **params) -> Dict[str, Any]:
        """Get all pages belonging to a doc."""
        return self._request("GET", f"/v3/workspaces/{workspace_id}/docs/{doc_id}/pages", params=params)

    def create_page(self, workspace_id: str, doc_id: str, name: str, content: Optional[str] = None, **page_data) -> Dict[str, Any]:
        """Create a new page in a doc."""
        data = {"name": name}
        if content:
            data["content"] = content
        data.update(page_data)
        return self._request("POST", f"/v3/workspaces/{workspace_id}/docs/{doc_id}/pages", json=data)

    def get_page(self, workspace_id: str, doc_id: str, page_id: str) -> Dict[str, Any]:
        """Get page by ID."""
        return self._request("GET", f"/v3/workspaces/{workspace_id}/docs/{doc_id}/pages/{page_id}")

    def update_page(self, workspace_id: str, doc_id: str, page_id: str, **updates) -> Dict[str, Any]:
        """Update a page."""
        return self._request("PUT", f"/v3/workspaces/{workspace_id}/docs/{doc_id}/pages/{page_id}", json=updates)

    def set_page_icon(self, workspace_id: str, doc_id: str, page_id: str, icon: str, icon_type: str = "emoji") -> Dict[str, Any]:
        """
        Set page icon (emoji or custom).

        Args:
            workspace_id: Workspace ID
            doc_id: Doc ID
            page_id: Page ID
            icon: Icon value (emoji character or custom icon ID)
            icon_type: Type of icon ("emoji" or "custom")

        Returns:
            Updated page data
        """
        data = {}
        if icon_type == "emoji":
            data["icon_emoji"] = icon
        else:
            data["icon_id"] = icon

        return self.update_page(workspace_id, doc_id, page_id, **data)

    def set_page_color(self, workspace_id: str, doc_id: str, page_id: str, color: Optional[str] = None, cover_image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Set page color or cover image.

        Args:
            workspace_id: Workspace ID
            doc_id: Doc ID
            page_id: Page ID
            color: Color value (hex code or color name)
            cover_image_url: URL to cover image

        Returns:
            Updated page data
        """
        data = {}
        if color:
            data["color"] = color
        if cover_image_url:
            data["cover_image"] = cover_image_url

        return self.update_page(workspace_id, doc_id, page_id, **data)

    def add_page_attachment(self, workspace_id: str, doc_id: str, page_id: str, file_path: str) -> Dict[str, Any]:
        """
        Add attachment to a page.

        Args:
            workspace_id: Workspace ID
            doc_id: Doc ID
            page_id: Page ID
            file_path: Path to file to attach

        Returns:
            Attachment data
        """
        # Use the attachments API through the client
        # This requires access to the client's attachments API
        # For now, we'll structure it to be called through the client
        raise NotImplementedError("Page attachments should be added via client.create_page_attachment()")

    def delete_page(self, workspace_id: str, doc_id: str, page_id: str) -> Dict[str, Any]:
        """
        Delete a page.

        Args:
            workspace_id: Workspace ID
            doc_id: Doc ID
            page_id: Page ID

        Returns:
            Deletion confirmation
        """
        return self._request("DELETE", f"/v3/workspaces/{workspace_id}/docs/{doc_id}/pages/{page_id}")

    def delete_doc(self, workspace_id: str, doc_id: str) -> Dict[str, Any]:
        """
        Delete a doc.

        Args:
            workspace_id: Workspace ID
            doc_id: Doc ID

        Returns:
            Deletion confirmation
        """
        return self._request("DELETE", f"/v3/workspaces/{workspace_id}/docs/{doc_id}")

