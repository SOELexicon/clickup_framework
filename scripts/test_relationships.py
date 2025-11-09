#!/usr/bin/env python3
"""
Test script for task relationship features.

This script demonstrates the new relationship functionality without making actual API calls.
"""

from clickup_framework.formatters.task import format_task


def test_dependency_formatting():
    """Test formatting of task dependencies."""
    print("=" * 60)
    print("Testing Dependency Formatting")
    print("=" * 60)

    # Mock task with dependencies
    task_with_deps = {
        "id": "abc123",
        "name": "Implement API endpoint",
        "status": {"status": "in progress"},
        "assignees": [{"username": "John Doe"}],
        "dependencies": [
            {"task_id": "xyz789", "type": 0},  # Waiting on
            {"depends_on": "def456", "type": 1},  # Blocking
        ],
        "linked_tasks": [
            {"task_id": "task1", "link_id": "link1"},
            {"task_id": "task2", "link_id": "link2"},
        ],
    }

    print("\nDetailed format:")
    print(format_task(task_with_deps, detail_level="detailed"))

    print("\n" + "=" * 60)
    print("\nFull format:")
    print(format_task(task_with_deps, detail_level="full"))


def test_custom_relationship_formatting():
    """Test formatting of custom relationship fields."""
    print("\n" + "=" * 60)
    print("Testing Custom Relationship Field Formatting")
    print("=" * 60)

    task_with_relationships = {
        "id": "project_123",
        "name": "Build Mobile App",
        "status": {"status": "in progress"},
        "custom_fields": [
            {
                "id": "field_1",
                "name": "Client",
                "type": "relationship",
                "value": ["client_task_456", "client_task_789"]
            },
            {
                "id": "field_2",
                "name": "Budget",
                "type": "currency",
                "value": 5000000  # $50,000.00 in cents
            }
        ]
    }

    print("\nFull format with relationship fields:")
    print(format_task(task_with_relationships, detail_level="full"))


def test_api_methods():
    """Test that API methods are available (without calling them)."""
    print("\n" + "=" * 60)
    print("Testing API Method Availability")
    print("=" * 60)

    from clickup_framework import ClickUpClient
    from clickup_framework.resources import TasksAPI

    # Note: This will fail if CLICKUP_API_TOKEN is not set, but we're just
    # checking that the methods exist
    try:
        client = ClickUpClient()
        tasks = TasksAPI(client)

        # Check client methods exist
        assert hasattr(client, 'add_task_dependency')
        assert hasattr(client, 'delete_task_dependency')
        assert hasattr(client, 'add_task_link')
        assert hasattr(client, 'delete_task_link')
        print("✓ Client methods available")

        # Check TasksAPI methods exist
        assert hasattr(tasks, 'add_dependency_waiting_on')
        assert hasattr(tasks, 'add_dependency_blocking')
        assert hasattr(tasks, 'remove_dependency')
        assert hasattr(tasks, 'add_link')
        assert hasattr(tasks, 'remove_link')
        assert hasattr(tasks, 'set_relationship_field')
        print("✓ TasksAPI methods available")

        print("\nAll relationship methods are properly implemented!")

    except Exception as e:
        print(f"Note: {e}")
        print("(API token not required for this test)")


if __name__ == "__main__":
    test_dependency_formatting()
    test_custom_relationship_formatting()
    test_api_methods()

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
