"""
DocsAPI - High-level API for ClickUp Docs operations

Provides convenient methods for ClickUp Docs and Pages.

ClickUp Docs API documentation:
https://developer.clickup.com/reference/searchdocspublic

Note: The Docs API uses v3 endpoints, unlike most other APIs which use v2.
"""

from typing import Dict, Any, Optional, List


class DocsAPI:
    """
    High-level API for ClickUp Docs and Pages operations.

    The Docs API allows you to:
    - Create and manage docs in workspaces
    - Create and edit pages within docs
    - Retrieve doc content and structure

    Usage:
        from clickup_framework import ClickUpClient
        from clickup_framework.resources import DocsAPI

        client = ClickUpClient()
        docs = DocsAPI(client)

        # Get workspace docs
        docs_list = docs.get_workspace_docs(workspace_id="90151898946")

        # Create doc
        new_doc = docs.create_doc(
            workspace_id="90151898946",
            name="My Document"
        )

        # Create a page in the doc
        page = docs.create_page(
            doc_id=new_doc['id'],
            name="Introduction",
            content="# Welcome\\n\\nThis is the introduction page."
        )

    Formatting limitations:
    - The Docs API has some formatting limitations compared to the product
    - Supported in markdown: normal text, headings 1-4, bulleted lists, numbered lists,
      code blocks (formatting lost), quotes, bold, italic, strikethrough, inline code,
      links, tables (formatting lost), dividers
    - Not supported: alignment, toggle lists, checklists, banners, embeds, advanced blocks
    """

    def __init__(self, client):
        """
        Initialize DocsAPI.

        Args:
            client: ClickUpClient instance
        """
        self.client = client

    # Docs operations
    def get_workspace_docs(
        self,
        workspace_id: str,
        **params
    ) -> Dict[str, Any]:
        """
        Get all docs in a workspace.

        Args:
            workspace_id: Workspace/team ID
            **params: Additional query parameters

        Returns:
            Dict containing list of docs with metadata

        Example:
            docs_list = docs.get_workspace_docs("90151898946")
            for doc in docs_list['docs']:
                print(doc['name'])
        """
        return self.client.get_workspace_docs(workspace_id, **params)

    def create_doc(
        self,
        workspace_id: str,
        name: str,
        parent_id: Optional[str] = None,
        **doc_data
    ) -> Dict[str, Any]:
        """
        Create a new doc in a workspace.

        Args:
            workspace_id: Workspace/team ID
            name: Doc name
            parent_id: Optional parent doc ID (for nested docs)
            **doc_data: Additional doc fields

        Returns:
            Created doc data

        Example:
            new_doc = docs.create_doc(
                workspace_id="90151898946",
                name="Project Documentation"
            )
        """
        if parent_id:
            doc_data['parent_id'] = parent_id
        return self.client.create_doc(workspace_id, name, **doc_data)

    def get_doc(self, workspace_id: str, doc_id: str) -> Dict[str, Any]:
        """
        Get doc by ID.

        Args:
            workspace_id: Workspace/team ID
            doc_id: Doc ID

        Returns:
            Doc data including metadata

        Example:
            doc = docs.get_doc("90151898946", "abc123")
            print(doc['name'])
        """
        return self.client.get_doc(workspace_id, doc_id)

    # Page operations
    def get_doc_pages_list(self, workspace_id: str, doc_id: str) -> Dict[str, Any]:
        """
        Get page listing/index for a doc.

        Args:
            workspace_id: Workspace/team ID
            doc_id: Doc ID

        Returns:
            Page listing data

        Example:
            page_list = docs.get_doc_pages_list("90151898946", "abc123")
        """
        return self.client.get_doc_pages_list(workspace_id, doc_id)

    def get_doc_pages(self, workspace_id: str, doc_id: str, **params) -> List[Dict[str, Any]]:
        """
        Get all pages belonging to a doc.

        Args:
            workspace_id: Workspace/team ID
            doc_id: Doc ID
            **params: Additional query parameters

        Returns:
            List of page dicts

        Example:
            pages = docs.get_doc_pages("90151898946", "abc123")
            for page in pages:
                print(page['name'])
        """
        return self.client.get_doc_pages(workspace_id, doc_id, **params)

    def create_page(
        self,
        workspace_id: str,
        doc_id: str,
        name: str,
        content: Optional[str] = None,
        **page_data
    ) -> Dict[str, Any]:
        """
        Create a new page in a doc.

        Args:
            workspace_id: Workspace/team ID
            doc_id: Doc ID
            name: Page name
            content: Page content (markdown format)
            **page_data: Additional page fields

        Returns:
            Created page data

        Example:
            page = docs.create_page(
                workspace_id="90151898946",
                doc_id="abc123",
                name="Getting Started",
                content="# Getting Started\\n\\nWelcome to our documentation."
            )

        Note: Content should use markdown format. See class docstring for
        formatting limitations.
        """
        return self.client.create_page(workspace_id, doc_id, name, content, **page_data)

    def get_page(self, workspace_id: str, doc_id: str, page_id: str) -> Dict[str, Any]:
        """
        Get page by ID.

        Args:
            workspace_id: Workspace/team ID
            doc_id: Doc ID
            page_id: Page ID

        Returns:
            Page data including content

        Example:
            page = docs.get_page("90151898946", "abc123", "xyz789")
            print(page['content'])
        """
        return self.client.get_page(workspace_id, doc_id, page_id)

    def update_page(
        self,
        workspace_id: str,
        doc_id: str,
        page_id: str,
        name: Optional[str] = None,
        content: Optional[str] = None,
        **updates
    ) -> Dict[str, Any]:
        """
        Update a page.

        Args:
            workspace_id: Workspace/team ID
            doc_id: Doc ID
            page_id: Page ID
            name: New page name (optional)
            content: New page content (optional, markdown format)
            **updates: Additional fields to update

        Returns:
            Updated page data

        Example:
            updated_page = docs.update_page(
                workspace_id="90151898946",
                doc_id="abc123",
                page_id="xyz789",
                name="Updated Title",
                content="# Updated Content\n\nNew information here."
            )

        Note: Content should use markdown format. See class docstring for
        formatting limitations.
        """
        if name is not None:
            updates['name'] = name
        if content is not None:
            updates['content'] = content
        return self.client.update_page(workspace_id, doc_id, page_id, **updates)

    # Convenience methods
    def create_doc_with_pages(
        self,
        workspace_id: str,
        doc_name: str,
        pages: List[Dict[str, str]],
        **doc_data
    ) -> Dict[str, Any]:
        """
        Create a doc and add multiple pages to it.

        Args:
            workspace_id: Workspace/team ID
            doc_name: Doc name
            pages: List of page dicts with 'name' and 'content' keys
            **doc_data: Additional doc fields

        Returns:
            Dict with 'doc' and 'pages' data

        Example:
            result = docs.create_doc_with_pages(
                workspace_id="90151898946",
                doc_name="API Guide",
                pages=[
                    {"name": "Introduction", "content": "# Intro\\n\\nWelcome!"},
                    {"name": "Setup", "content": "# Setup\\n\\nInstallation steps..."},
                ]
            )
        """
        # Create the doc
        doc = self.create_doc(workspace_id, doc_name, **doc_data)
        doc_id = doc['id']

        # Create pages
        created_pages = []
        for page_data in pages:
            page = self.create_page(
                workspace_id=workspace_id,
                doc_id=doc_id,
                name=page_data['name'],
                content=page_data.get('content', '')
            )
            created_pages.append(page)

        return {
            'doc': doc,
            'pages': created_pages
        }
