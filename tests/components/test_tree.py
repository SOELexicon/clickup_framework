"""
Tests for TreeFormatter.
"""

import pytest
from clickup_framework.components.tree import TreeFormatter


class TestTreeFormatter:
    """Tests for TreeFormatter class."""

    def test_build_tree_simple(self):
        """Test building a simple tree."""
        items = [
            {'id': '1', 'name': 'Item 1'},
            {'id': '2', 'name': 'Item 2'}
        ]

        def format_fn(item):
            return item['name']

        def get_children_fn(item):
            return []

        result = TreeFormatter.build_tree(items, format_fn, get_children_fn)

        assert len(result) == 2
        assert "Item 1" in result[0]
        assert "Item 2" in result[1]
        assert "├─" in result[0]  # First item
        assert "└─" in result[1]  # Last item

    def test_build_tree_with_children(self):
        """Test building a tree with children."""
        parent = {'id': '1', 'name': 'Parent', 'children': [
            {'id': '1.1', 'name': 'Child 1', 'children': []},
            {'id': '1.2', 'name': 'Child 2', 'children': []}
        ]}

        items = [parent]

        def format_fn(item):
            return item['name']

        def get_children_fn(item):
            return item.get('children', [])

        result = TreeFormatter.build_tree(items, format_fn, get_children_fn)

        # Should have parent + 2 children
        assert len(result) == 3
        assert any("Parent" in line for line in result)
        assert any("Child 1" in line for line in result)
        assert any("Child 2" in line for line in result)

        # Check indentation
        parent_line = [l for l in result if "Parent" in l][0]
        child_lines = [l for l in result if "Child" in l]

        # Children should be indented more than parent
        assert len(child_lines[0]) > len(parent_line)

    def test_build_tree_nested_hierarchy(self):
        """Test building a deeply nested tree."""
        grandparent = {'id': '1', 'name': 'Grandparent', 'children': [
            {'id': '1.1', 'name': 'Parent', 'children': [
                {'id': '1.1.1', 'name': 'Child', 'children': []}
            ]}
        ]}

        items = [grandparent]

        def format_fn(item):
            return item['name']

        def get_children_fn(item):
            return item.get('children', [])

        result = TreeFormatter.build_tree(items, format_fn, get_children_fn)

        # Should have 3 levels
        assert len(result) == 3
        assert any("Grandparent" in line for line in result)
        assert any("Parent" in line for line in result)
        assert any("Child" in line for line in result)

    def test_render_with_header(self):
        """Test rendering with header."""
        items = [{'id': '1', 'name': 'Item 1'}]

        def format_fn(item):
            return item['name']

        def get_children_fn(item):
            return []

        result = TreeFormatter.render(items, format_fn, get_children_fn, header="My Tree")

        assert "My Tree" in result
        assert "Item 1" in result

    def test_render_without_header(self):
        """Test rendering without header."""
        items = [{'id': '1', 'name': 'Item 1'}]

        def format_fn(item):
            return item['name']

        def get_children_fn(item):
            return []

        result = TreeFormatter.render(items, format_fn, get_children_fn)

        assert "Item 1" in result
        # Should start with tree character
        assert "└─" in result or "├─" in result

    def test_format_container_tree(self):
        """Test formatting a container tree."""
        containers = [
            {
                'id': 'c1',
                'name': 'Container 1',
                'sub_containers': [],
                'items': [
                    {'id': 'i1', 'name': 'Item 1'},
                    {'id': 'i2', 'name': 'Item 2'}
                ]
            }
        ]

        def format_container_fn(container):
            return container['name']

        def format_item_fn(item):
            return item['name']

        def get_sub_containers_fn(container):
            return container.get('sub_containers', [])

        def get_items_fn(container):
            return container.get('items', [])

        result = TreeFormatter.format_container_tree(
            containers,
            format_container_fn,
            format_item_fn,
            get_sub_containers_fn,
            get_items_fn
        )

        assert len(result) == 3  # Container + 2 items
        assert any("Container 1" in line for line in result)
        assert any("Item 1" in line for line in result)
        assert any("Item 2" in line for line in result)

    def test_tree_uses_box_drawing_characters(self):
        """Test that tree uses Unicode box-drawing characters."""
        items = [
            {'id': '1', 'name': 'Item 1'},
            {'id': '2', 'name': 'Item 2'}
        ]

        def format_fn(item):
            return item['name']

        def get_children_fn(item):
            return []

        result = TreeFormatter.build_tree(items, format_fn, get_children_fn)

        # Should use box-drawing characters
        tree_str = "\n".join(result)
        assert "├─" in tree_str or "└─" in tree_str
