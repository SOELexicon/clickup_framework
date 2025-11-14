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

