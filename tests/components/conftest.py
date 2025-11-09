"""
Test fixtures for component tests.

Provides sample task data for testing display components.
"""

import pytest


@pytest.fixture
def sample_task():
    """Single task with basic information."""
    return {
        'id': 'task_123',
        'name': 'Implement new feature',
        'status': {'status': 'in progress'},
        'priority': {'priority': '2'},
        'description': 'Add support for hierarchical task display',
        'tags': [
            {'name': 'feature'},
            {'name': 'priority-high'}
        ],
        'assignees': [
            {'id': 'user_1', 'username': 'john_doe'}
        ],
        'date_created': '2024-01-01T10:00:00Z',
        'date_updated': '2024-01-02T15:30:00Z',
        'due_date': '2024-01-15T23:59:59Z',
        'custom_type': 'feature'
    }


@pytest.fixture
def sample_task_minimal():
    """Minimal task with only required fields."""
    return {
        'id': 'task_456',
        'name': 'Fix bug',
        'status': {'status': 'to do'},
        'priority': {'priority': '4'}
    }


@pytest.fixture
def sample_task_completed():
    """Completed task."""
    return {
        'id': 'task_789',
        'name': 'Completed task',
        'status': {'status': 'complete'},
        'priority': {'priority': '3'},
        'custom_type': 'task'
    }


@pytest.fixture
def sample_hierarchical_tasks():
    """Tasks with parent-child relationships."""
    return [
        {
            'id': 'parent_1',
            'name': 'Parent Task',
            'status': {'status': 'in progress'},
            'priority': {'priority': '1'},
            'parent': None,
            'custom_type': 'project'
        },
        {
            'id': 'child_1',
            'name': 'Child Task 1',
            'status': {'status': 'to do'},
            'priority': {'priority': '2'},
            'parent': 'parent_1',
            'custom_type': 'task'
        },
        {
            'id': 'child_2',
            'name': 'Child Task 2',
            'status': {'status': 'complete'},
            'priority': {'priority': '3'},
            'parent': 'parent_1',
            'custom_type': 'task'
        },
        {
            'id': 'grandchild_1',
            'name': 'Grandchild Task',
            'status': {'status': 'to do'},
            'priority': {'priority': '2'},
            'parent': 'child_1',
            'custom_type': 'task'
        },
        {
            'id': 'orphan_1',
            'name': 'Orphaned Task',
            'status': {'status': 'to do'},
            'priority': {'priority': '4'},
            'parent': None,
            'custom_type': 'task'
        }
    ]


@pytest.fixture
def sample_container_tasks():
    """Tasks with container (space/folder/list) information."""
    return [
        {
            'id': 'task_1',
            'name': 'Task in List A',
            'status': {'status': 'to do'},
            'priority': {'priority': '2'},
            'space': {'id': 'space_1', 'name': 'Engineering'},
            'folder': {'id': 'folder_1', 'name': 'Backend'},
            'list': {'id': 'list_a', 'name': 'API Development'},
            'custom_type': 'task'
        },
        {
            'id': 'task_2',
            'name': 'Task in List B',
            'status': {'status': 'in progress'},
            'priority': {'priority': '1'},
            'space': {'id': 'space_1', 'name': 'Engineering'},
            'folder': {'id': 'folder_1', 'name': 'Backend'},
            'list': {'id': 'list_b', 'name': 'Database'},
            'custom_type': 'feature'
        },
        {
            'id': 'task_3',
            'name': 'Task in Different Folder',
            'status': {'status': 'complete'},
            'priority': {'priority': '3'},
            'space': {'id': 'space_1', 'name': 'Engineering'},
            'folder': {'id': 'folder_2', 'name': 'Frontend'},
            'list': {'id': 'list_c', 'name': 'UI Components'},
            'custom_type': 'bug'
        },
        {
            'id': 'task_4',
            'name': 'Task in Different Space',
            'status': {'status': 'to do'},
            'priority': {'priority': '4'},
            'space': {'id': 'space_2', 'name': 'Product'},
            'folder': {'id': 'folder_3', 'name': 'Design'},
            'list': {'id': 'list_d', 'name': 'Mockups'},
            'custom_type': 'task'
        }
    ]


@pytest.fixture
def sample_tasks_with_comments():
    """Tasks with comments."""
    return [
        {
            'id': 'task_c1',
            'name': 'Task with comments',
            'status': {'status': 'in progress'},
            'priority': {'priority': '2'},
            'comments': [
                {
                    'id': 'comment_1',
                    'comment_text': 'This is the first comment',
                    'user': {'id': 'user_1', 'username': 'john'},
                    'date': '2024-01-01T10:00:00Z'
                },
                {
                    'id': 'comment_2',
                    'comment_text': 'This is a longer comment that should be truncated if the limit is set appropriately',
                    'user': {'id': 'user_2', 'username': 'jane'},
                    'date': '2024-01-02T11:00:00Z'
                }
            ],
            'custom_type': 'task'
        }
    ]


@pytest.fixture
def sample_tasks_mixed_status():
    """Tasks with various statuses for filtering tests."""
    return [
        {'id': 'task_s1', 'name': 'To Do Task', 'status': {'status': 'to do'}, 'priority': {'priority': '1'}},
        {'id': 'task_s2', 'name': 'In Progress Task', 'status': {'status': 'in progress'}, 'priority': {'priority': '2'}},
        {'id': 'task_s3', 'name': 'Complete Task', 'status': {'status': 'complete'}, 'priority': {'priority': '3'}},
        {'id': 'task_s4', 'name': 'Blocked Task', 'status': {'status': 'blocked'}, 'priority': {'priority': '1'}},
        {'id': 'task_s5', 'name': 'Another To Do', 'status': {'status': 'to do'}, 'priority': {'priority': '4'}},
    ]


@pytest.fixture
def sample_doc():
    """Single doc with basic information."""
    return {
        'id': 'doc_123',
        'name': 'Project Documentation',
        'date_created': '2024-01-01T10:00:00Z',
        'date_updated': '2024-01-05T15:30:00Z',
        'creator': {
            'id': 'user_1',
            'username': 'john_doe',
            'email': 'john@example.com'
        }
    }


@pytest.fixture
def sample_page():
    """Single page with basic information."""
    return {
        'id': 'page_456',
        'name': 'Getting Started',
        'content': '# Getting Started\n\nWelcome to our documentation. This guide will help you get started.',
        'date_created': '2024-01-02T10:00:00Z',
        'date_updated': '2024-01-03T12:00:00Z',
        'creator': {
            'id': 'user_1',
            'username': 'john_doe',
            'email': 'john@example.com'
        }
    }


@pytest.fixture
def sample_docs_with_pages():
    """Docs with pages for hierarchy testing."""
    return {
        'docs': [
            {
                'id': 'doc_1',
                'name': 'API Documentation',
                'date_created': '2024-01-01T10:00:00Z',
                'date_updated': '2024-01-05T15:30:00Z',
                'creator': {'id': 'user_1', 'username': 'john_doe'}
            },
            {
                'id': 'doc_2',
                'name': 'User Guide',
                'parent_id': 'doc_1',
                'date_created': '2024-01-02T10:00:00Z',
                'date_updated': '2024-01-04T12:00:00Z',
                'creator': {'id': 'user_2', 'username': 'jane_smith'}
            }
        ],
        'pages': {
            'doc_1': [
                {
                    'id': 'page_1',
                    'name': 'Introduction',
                    'content': '# Introduction\n\nAPI documentation intro.',
                    'date_created': '2024-01-01T11:00:00Z',
                    'creator': {'id': 'user_1', 'username': 'john_doe'}
                },
                {
                    'id': 'page_2',
                    'name': 'Authentication',
                    'content': '# Authentication\n\nHow to authenticate.',
                    'date_created': '2024-01-01T12:00:00Z',
                    'creator': {'id': 'user_1', 'username': 'john_doe'}
                }
            ],
            'doc_2': [
                {
                    'id': 'page_3',
                    'name': 'Quick Start',
                    'content': '# Quick Start\n\nGet started quickly.',
                    'date_created': '2024-01-02T11:00:00Z',
                    'creator': {'id': 'user_2', 'username': 'jane_smith'}
                }
            ]
        }
    }
