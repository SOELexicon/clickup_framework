"""
Tests for DocHierarchyFormatter.
"""

import pytest
from clickup_framework.components.doc_hierarchy import DocHierarchyFormatter
from clickup_framework.components.options import FormatOptions


class TestDocHierarchyFormatter:
    """Tests for DocHierarchyFormatter class."""

    def test_organize_docs_with_pages(self, sample_docs_with_pages):
        """Test organizing docs with their pages."""
        formatter = DocHierarchyFormatter()
        docs = sample_docs_with_pages['docs']
        pages_by_doc = sample_docs_with_pages['pages']

        organized = formatter.organize_docs_with_pages(docs, pages_by_doc)

        # Should attach pages to docs
        doc_1 = [d for d in organized if d['id'] == 'doc_1'][0]
        assert len(doc_1['_pages']) == 2
        assert doc_1['_pages'][0]['name'] == 'Authentication'  # Sorted alphabetically

    def test_organize_by_parent_child(self, sample_docs_with_pages):
        """Test organizing docs by parent-child relationships."""
        formatter = DocHierarchyFormatter()
        docs = sample_docs_with_pages['docs']

        root_docs = formatter.organize_by_parent_child(docs)

        # Should have 1 root doc (doc_1)
        assert len(root_docs) == 1
        assert root_docs[0]['id'] == 'doc_1'

        # doc_2 should be a child of doc_1
        assert len(root_docs[0]['_children']) == 1
        assert root_docs[0]['_children'][0]['id'] == 'doc_2'

    def test_organize_excludes_orphaned_when_requested(self, sample_docs_with_pages):
        """Test excluding orphaned docs."""
        formatter = DocHierarchyFormatter()
        docs = sample_docs_with_pages['docs'].copy()

        # Add an orphaned doc
        docs.append({
            'id': 'doc_orphan',
            'name': 'Orphaned Doc',
            'parent_id': 'nonexistent_parent'
        })

        root_docs = formatter.organize_by_parent_child(docs, include_orphaned=False)

        # Should only have doc_1 (orphan excluded)
        assert len(root_docs) == 1
        assert root_docs[0]['id'] == 'doc_1'

    def test_format_docs_hierarchy(self, sample_docs_with_pages):
        """Test formatting docs as hierarchy."""
        formatter = DocHierarchyFormatter()
        docs = sample_docs_with_pages['docs']
        pages_by_doc = sample_docs_with_pages['pages']

        options = FormatOptions(colorize_output=False)
        result = formatter.format_docs_hierarchy(docs, pages_by_doc, options)

        # Should include docs and pages
        assert "API Documentation" in result
        assert "User Guide" in result
        assert "Introduction" in result
        assert "Authentication" in result
        assert "Quick Start" in result

        # Should use tree characters
        assert "├─" in result or "└─" in result

    def test_format_docs_hierarchy_with_header(self, sample_docs_with_pages):
        """Test formatting hierarchy with header."""
        formatter = DocHierarchyFormatter()
        docs = sample_docs_with_pages['docs']
        pages_by_doc = sample_docs_with_pages['pages']

        result = formatter.format_docs_hierarchy(
            docs,
            pages_by_doc,
            header="My Documentation"
        )

        assert "My Documentation" in result
        assert "API Documentation" in result

    def test_format_flat_list(self, sample_docs_with_pages):
        """Test formatting docs as a flat list."""
        formatter = DocHierarchyFormatter()
        docs = sample_docs_with_pages['docs']
        pages_by_doc = sample_docs_with_pages['pages']

        options = FormatOptions(colorize_output=False)
        result = formatter.format_flat_list(docs, pages_by_doc, options)

        # Should include all docs and pages
        assert "API Documentation" in result
        assert "User Guide" in result
        assert "Introduction" in result

        # Should be simpler formatting (indentation but no complex tree)
        assert isinstance(result, str)

    def test_format_flat_list_with_header(self, sample_docs_with_pages):
        """Test formatting flat list with header."""
        formatter = DocHierarchyFormatter()
        docs = sample_docs_with_pages['docs']
        pages_by_doc = sample_docs_with_pages['pages']

        result = formatter.format_flat_list(
            docs,
            pages_by_doc,
            header="All Documentation"
        )

        assert "All Documentation" in result
        assert "API Documentation" in result

    def test_get_doc_count(self, sample_docs_with_pages):
        """Test getting doc and page counts."""
        formatter = DocHierarchyFormatter()
        docs = sample_docs_with_pages['docs']
        pages_by_doc = sample_docs_with_pages['pages']

        # Organize first to attach pages
        organized = formatter.organize_docs_with_pages(docs, pages_by_doc)
        counts = formatter.get_doc_count(organized)

        assert counts['total_docs'] == 2
        assert counts['total_pages'] == 3

    def test_empty_docs_list(self):
        """Test formatting empty docs list."""
        formatter = DocHierarchyFormatter()
        result = formatter.format_docs_hierarchy([], {})

        # Should return empty or minimal output
        assert isinstance(result, str)

    def test_docs_without_pages(self):
        """Test formatting docs without any pages."""
        formatter = DocHierarchyFormatter()
        docs = [
            {
                'id': 'doc_empty',
                'name': 'Empty Doc'
            }
        ]

        result = formatter.format_docs_hierarchy(docs, {})

        assert "Empty Doc" in result

    def test_format_respects_options(self, sample_docs_with_pages):
        """Test that formatting respects format options."""
        formatter = DocHierarchyFormatter()
        docs = sample_docs_with_pages['docs']
        pages_by_doc = sample_docs_with_pages['pages']

        options = FormatOptions(
            show_ids=True,
            colorize_output=False
        )
        result = formatter.format_docs_hierarchy(docs, pages_by_doc, options)

        # With show_ids, doc IDs should be visible
        assert "doc_1" in result
        assert isinstance(result, str)

    def test_nested_doc_structure(self):
        """Test deeply nested doc structure."""
        docs = [
            {'id': 'doc_root', 'name': 'Root Doc'},
            {'id': 'doc_child', 'name': 'Child Doc', 'parent_id': 'doc_root'},
            {'id': 'doc_grandchild', 'name': 'Grandchild Doc', 'parent_id': 'doc_child'}
        ]

        formatter = DocHierarchyFormatter()
        root_docs = formatter.organize_by_parent_child(docs)

        # Should have proper nesting
        assert len(root_docs) == 1
        assert root_docs[0]['id'] == 'doc_root'
        assert len(root_docs[0]['_children']) == 1
        assert root_docs[0]['_children'][0]['id'] == 'doc_child'
        assert len(root_docs[0]['_children'][0]['_children']) == 1

    def test_multiple_root_docs(self):
        """Test formatting with multiple root docs."""
        docs = [
            {'id': 'doc_a', 'name': 'Doc A'},
            {'id': 'doc_b', 'name': 'Doc B'},
            {'id': 'doc_c', 'name': 'Doc C'}
        ]

        formatter = DocHierarchyFormatter()
        result = formatter.format_docs_hierarchy(docs, {})

        # All docs should appear
        assert "Doc A" in result
        assert "Doc B" in result
        assert "Doc C" in result

    def test_pages_sorted_alphabetically(self):
        """Test that pages are sorted alphabetically."""
        docs = [{'id': 'doc_1', 'name': 'Test Doc'}]
        pages = {
            'doc_1': [
                {'id': 'p1', 'name': 'Zebra'},
                {'id': 'p2', 'name': 'Alpha'},
                {'id': 'p3', 'name': 'Middle'}
            ]
        }

        formatter = DocHierarchyFormatter()
        organized = formatter.organize_docs_with_pages(docs, pages)

        # Pages should be sorted
        page_names = [p['name'] for p in organized[0]['_pages']]
        assert page_names == ['Alpha', 'Middle', 'Zebra']
