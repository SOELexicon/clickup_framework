"""
Doc Hierarchy Organization Module

Provides utilities for organizing docs and their pages in hierarchical structures.
"""

from typing import List, Dict, Any, Optional
from clickup_framework.components.options import FormatOptions
from clickup_framework.components.doc_formatter import RichDocFormatter
from clickup_framework.components.tree import TreeFormatter


class DocHierarchyFormatter:
    """
    Organizes and formats docs and pages in hierarchical structures.

    Supports:
        - Doc with nested pages
        - Parent-child doc relationships
        - Rich formatting with emojis and colors
    """

    def __init__(self, formatter: Optional[RichDocFormatter] = None):
        """
        Initialize the doc hierarchy formatter.

        Args:
            formatter: Doc formatter to use (creates default if not provided)
        """
        self.formatter = formatter or RichDocFormatter()

    def organize_docs_with_pages(
        self,
        docs: List[Dict[str, Any]],
        pages_by_doc: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Organize docs with their pages attached.

        Args:
            docs: List of doc dictionaries
            pages_by_doc: Dictionary mapping doc IDs to their pages

        Returns:
            List of docs with nested pages
        """
        # Attach pages to each doc
        for doc in docs:
            doc_id = doc.get('id')
            doc['_pages'] = pages_by_doc.get(doc_id, [])

            # Sort pages by name
            doc['_pages'].sort(key=lambda p: p.get('name', '').lower())

        return docs

    def organize_by_parent_child(
        self,
        docs: List[Dict[str, Any]],
        include_orphaned: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Organize docs into a parent-child hierarchy.

        Args:
            docs: Flat list of docs
            include_orphaned: Whether to include orphaned docs

        Returns:
            List of root docs with nested children
        """
        # Build doc map
        doc_map = {doc['id']: doc for doc in docs if doc.get('id')}

        # Find root docs (no parent or parent not in list)
        root_docs = []
        for doc in docs:
            parent_id = doc.get('parent_id')
            if not parent_id or parent_id not in doc_map:
                if include_orphaned or not parent_id:
                    root_docs.append(doc)

        # Build children lists for each doc
        for doc in docs:
            doc['_children'] = []

        for doc in docs:
            parent_id = doc.get('parent_id')
            if parent_id and parent_id in doc_map:
                doc_map[parent_id]['_children'].append(doc)

        # Sort root docs by name
        root_docs.sort(key=lambda d: d.get('name', '').lower())

        return root_docs

    def format_docs_hierarchy(
        self,
        docs: List[Dict[str, Any]],
        pages_by_doc: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        options: Optional[FormatOptions] = None,
        header: Optional[str] = None
    ) -> str:
        """
        Format docs and their pages in a hierarchical tree view.

        Args:
            docs: List of docs
            pages_by_doc: Optional dictionary mapping doc IDs to their pages
            options: Format options
            header: Optional header text

        Returns:
            Formatted hierarchy string
        """
        if options is None:
            options = FormatOptions()

        if pages_by_doc is None:
            pages_by_doc = {}

        # Attach pages to docs
        docs_with_pages = self.organize_docs_with_pages(docs, pages_by_doc)

        # Organize into parent-child hierarchy if needed
        root_docs = self.organize_by_parent_child(docs_with_pages)

        # Define functions for tree building
        def format_doc_fn(doc):
            return self.formatter.format_doc(doc, options)

        def get_children_fn(doc):
            # First get child docs
            children = doc.get('_children', [])
            # Then get pages as special items
            pages = doc.get('_pages', [])

            # Sort children docs by name
            children.sort(key=lambda d: d.get('name', '').lower())

            # Return children docs followed by pages
            # We'll handle pages specially in the tree builder
            return children

        # Build tree structure with custom handling for pages
        lines = []

        if header:
            lines.append(header)
            lines.append("")

        # Build the tree with docs and pages
        doc_lines = self._build_doc_tree(
            root_docs,
            format_doc_fn,
            get_children_fn,
            options
        )
        lines.extend(doc_lines)

        return "\n".join(lines)

    def _build_doc_tree(
        self,
        docs: List[Dict[str, Any]],
        format_doc_fn,
        get_children_fn,
        options: FormatOptions,
        prefix: str = "",
        is_last: bool = True
    ) -> List[str]:
        """
        Recursively build a tree structure with docs and pages.

        Args:
            docs: List of docs to display
            format_doc_fn: Function to format each doc
            get_children_fn: Function to get children docs
            options: Format options
            prefix: Current indentation prefix
            is_last: Whether this is the last item in its level

        Returns:
            List of formatted lines
        """
        lines = []

        for i, doc in enumerate(docs):
            is_last_doc = (i == len(docs) - 1)

            # Determine the branch character
            branch = "└─" if is_last_doc else "├─"

            # Format the current doc
            formatted = format_doc_fn(doc)
            lines.append(f"{prefix}{branch}{formatted}")

            # Calculate the prefix for children
            if is_last_doc:
                child_prefix = prefix + "  "
            else:
                child_prefix = prefix + "│ "

            # Get child docs
            children = get_children_fn(doc)

            # Get pages
            pages = doc.get('_pages', [])

            # Total items (children + pages)
            total_items = len(children) + len(pages)

            # Recursively format child docs
            if children:
                child_lines = self._build_doc_tree(
                    children,
                    format_doc_fn,
                    get_children_fn,
                    options,
                    child_prefix,
                    False
                )
                lines.extend(child_lines)

            # Format pages
            if pages:
                for j, page in enumerate(pages):
                    is_last_page = (j == len(pages) - 1)

                    page_branch = "└─" if is_last_page else "├─"
                    formatted_page = self.formatter.format_page(page, options)
                    lines.append(f"{child_prefix}{page_branch}{formatted_page}")

        return lines

    def get_doc_count(self, docs: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get counts of docs and pages.

        Args:
            docs: List of docs

        Returns:
            Dictionary with doc and page counts
        """
        counts = {
            'total_docs': len(docs),
            'total_pages': 0,
        }

        for doc in docs:
            pages = doc.get('_pages', [])
            counts['total_pages'] += len(pages)

        return counts

    def format_flat_list(
        self,
        docs: List[Dict[str, Any]],
        pages_by_doc: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        options: Optional[FormatOptions] = None,
        header: Optional[str] = None
    ) -> str:
        """
        Format docs and pages as a flat list (no tree structure).

        Args:
            docs: List of docs
            pages_by_doc: Optional dictionary mapping doc IDs to their pages
            options: Format options
            header: Optional header text

        Returns:
            Formatted list string
        """
        if options is None:
            options = FormatOptions()

        if pages_by_doc is None:
            pages_by_doc = {}

        lines = []

        if header:
            lines.append(header)
            lines.append("")

        # Sort docs by name
        sorted_docs = sorted(docs, key=lambda d: d.get('name', '').lower())

        for doc in sorted_docs:
            # Format doc
            formatted_doc = self.formatter.format_doc(doc, options)
            lines.append(formatted_doc)

            # Format pages for this doc
            doc_id = doc.get('id')
            pages = pages_by_doc.get(doc_id, [])

            if pages:
                sorted_pages = sorted(pages, key=lambda p: p.get('name', '').lower())
                for page in sorted_pages:
                    formatted_page = self.formatter.format_page(page, options)
                    lines.append(f"  {formatted_page}")

                # Add spacing between docs
                lines.append("")

        return "\n".join(lines)
