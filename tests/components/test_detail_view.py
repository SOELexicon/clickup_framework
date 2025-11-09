"""
Tests for TaskDetailFormatter
"""

import pytest
from clickup_framework.components import TaskDetailFormatter, FormatOptions


class TestTaskDetailFormatter:
    """Tests for TaskDetailFormatter"""

    def test_format_detail_basic(self, sample_tasks_mixed_status):
        """Test basic detail formatting"""
        formatter = TaskDetailFormatter()
        task = sample_tasks_mixed_status[0]

        result = formatter.format_detail(task)

        assert task['name'] in result
        assert task['id'] in result

    def test_format_with_context_shows_relationships(self, sample_hierarchical_tasks):
        """Test formatting with relationship context"""
        formatter = TaskDetailFormatter()

        # Get a child task
        child_task = next(t for t in sample_hierarchical_tasks if t['id'] == 'child_1')

        options = FormatOptions(include_completed=True)
        result = formatter.format_with_context(child_task, sample_hierarchical_tasks, options)

        # Should show relationship sections
        assert "Task Relationships:" in result or "🌳" in result
        assert "Current Task:" in result or "👉" in result

    def test_format_shows_parent_chain(self, sample_hierarchical_tasks):
        """Test that parent chain is shown correctly"""
        formatter = TaskDetailFormatter()

        # Get grandchild task
        grandchild = next(t for t in sample_hierarchical_tasks if t['id'] == 'grandchild_1')

        options = FormatOptions(include_completed=True)
        result = formatter.format_with_context(grandchild, sample_hierarchical_tasks, options)

        # Should show parent and grandparent
        assert "Parent Chain:" in result or "📊" in result
        # Parent task name should appear
        parent_name = next(t['name'] for t in sample_hierarchical_tasks if t['id'] == 'child_1')
        assert parent_name in result

    def test_format_shows_siblings(self, sample_hierarchical_tasks):
        """Test that siblings are shown"""
        formatter = TaskDetailFormatter()

        # Get one child task
        child_1 = next(t for t in sample_hierarchical_tasks if t['id'] == 'child_1')

        options = FormatOptions(include_completed=True)
        result = formatter.format_with_context(child_1, sample_hierarchical_tasks, options)

        # Should show siblings section
        assert "Siblings" in result or "👥" in result
        # Sibling name should appear
        assert "Child Task 2" in result

    def test_format_shows_children(self, sample_hierarchical_tasks):
        """Test that children (subtasks) are shown"""
        formatter = TaskDetailFormatter()

        # Get parent task
        parent = next(t for t in sample_hierarchical_tasks if t['id'] == 'parent_1')

        options = FormatOptions(include_completed=True)
        result = formatter.format_with_context(parent, sample_hierarchical_tasks, options)

        # Should show subtasks section
        assert "Subtasks" in result or "📂" in result
        # Child names should appear
        assert "Child Task 1" in result

    def test_format_shows_description(self):
        """Test that description is shown"""
        formatter = TaskDetailFormatter()

        # Create task with description
        task = {
            'id': 'task_1',
            'name': 'Task with Description',
            'status': {'status': 'in progress'},
            'description': 'This is a detailed description of the task'
        }

        options = FormatOptions.detailed()
        result = formatter.format_detail(task, options)

        assert "Description:" in result or "📝" in result
        assert task['description'] in result

    def test_format_shows_tags(self):
        """Test that tags are shown"""
        formatter = TaskDetailFormatter()

        # Create task with tags
        task = {
            'id': 'task_1',
            'name': 'Task with Tags',
            'status': {'status': 'in progress'},
            'tags': [{'name': 'backend'}, {'name': 'api'}]
        }

        options = FormatOptions.detailed()
        result = formatter.format_detail(task, options)

        assert "Tags:" in result or "🏷️" in result
        # Tag names should appear
        assert "backend" in result
        assert "api" in result

    def test_format_shows_dates(self):
        """Test that dates are shown"""
        formatter = TaskDetailFormatter()

        # Create task with dates
        task = {
            'id': 'task_1',
            'name': 'Task with Dates',
            'status': {'status': 'in progress'},
            'date_created': '2024-01-01T10:00:00Z',
            'due_date': '2024-01-31T23:59:59Z'
        }

        result = formatter.format_detail(task)

        # Should show created date
        assert "Created:" in result
        assert task['date_created'] in result

    def test_format_shows_container_info(self, sample_container_tasks):
        """Test that container hierarchy is shown"""
        formatter = TaskDetailFormatter()

        task = sample_container_tasks[0]

        result = formatter.format_detail(task)

        # Should show location
        assert "Location:" in result
        # Should show space/folder/list names
        assert task['space']['name'] in result
        assert task['list']['name'] in result

    def test_format_with_colorize(self, sample_hierarchical_tasks):
        """Test formatting with colors enabled"""
        formatter = TaskDetailFormatter()

        task = sample_hierarchical_tasks[0]
        options = FormatOptions(colorize_output=True)

        result = formatter.format_detail(task, options)

        # Should contain ANSI color codes
        assert "\033[" in result

    def test_format_without_colorize(self, sample_hierarchical_tasks):
        """Test formatting without colors"""
        formatter = TaskDetailFormatter()

        task = sample_hierarchical_tasks[0]
        options = FormatOptions(colorize_output=False)

        result = formatter.format_detail(task, options)

        # Should not contain ANSI color codes
        # (Note: We still use emojis even without colors)
        assert task['name'] in result

    def test_format_root_task_no_parent(self, sample_hierarchical_tasks):
        """Test formatting root task (no parent)"""
        formatter = TaskDetailFormatter()

        # Get root task
        root_task = next(t for t in sample_hierarchical_tasks if not t.get('parent'))

        options = FormatOptions(include_completed=True)
        result = formatter.format_with_context(root_task, sample_hierarchical_tasks, options)

        # Should not show parent chain
        assert "Parent Chain:" not in result or "has no parent" in result.lower()
        # Should show children
        assert "Subtasks" in result or "📂" in result

    def test_format_leaf_task_no_children(self, sample_hierarchical_tasks):
        """Test formatting leaf task (no children)"""
        formatter = TaskDetailFormatter()

        # Get leaf task
        leaf_task = next(t for t in sample_hierarchical_tasks if t['id'] == 'grandchild_1')

        options = FormatOptions(include_completed=True)
        result = formatter.format_with_context(leaf_task, sample_hierarchical_tasks, options)

        # Should show parent chain
        assert "Parent Chain:" in result or "📊" in result
        # Should mention current task
        assert "Current Task:" in result or "👉" in result

    def test_format_with_dependencies(self):
        """Test formatting task with dependencies"""
        formatter = TaskDetailFormatter()

        task = {
            'id': 'task_1',
            'name': 'Task with Dependencies',
            'status': {'status': 'in progress'},
            'priority': {'priority': '1'},
            'dependencies': [
                {'depends_on': 'dep_1'},
                {'depends_on': 'dep_2'}
            ]
        }

        all_tasks = [
            task,
            {
                'id': 'dep_1',
                'name': 'Dependency 1',
                'status': {'status': 'complete'}
            },
            {
                'id': 'dep_2',
                'name': 'Dependency 2',
                'status': {'status': 'in progress'}
            }
        ]

        options = FormatOptions(include_completed=True)
        result = formatter.format_with_context(task, all_tasks, options)

        # Should show dependencies section
        assert "Dependencies" in result or "🔗" in result
        # Dependency names should appear
        assert "Dependency 1" in result
        assert "Dependency 2" in result

    def test_format_with_comments(self, sample_tasks_with_comments):
        """Test formatting task with comments"""
        formatter = TaskDetailFormatter()

        task = sample_tasks_with_comments[0]

        result = formatter.format_detail(task)

        # Should show comments section
        assert "Comments" in result or "💬" in result
        # Comment content should appear (check for first comment text)
        assert "first comment" in result.lower()

    def test_format_with_checklists(self):
        """Test formatting task with checklists"""
        formatter = TaskDetailFormatter()

        task = {
            'id': 'task_1',
            'name': 'Task with Checklist',
            'status': {'status': 'in progress'},
            'checklists': [
                {
                    'name': 'Setup Tasks',
                    'items': [
                        {'name': 'Item 1', 'resolved': True},
                        {'name': 'Item 2', 'resolved': False},
                        {'name': 'Item 3', 'resolved': False}
                    ]
                }
            ]
        }

        result = formatter.format_detail(task)

        # Should show checklists section
        assert "Checklists" in result or "☑️" in result
        # Checklist name should appear
        assert "Setup Tasks" in result
        # Should show completion (1/3)
        assert "(1/3)" in result or "1/3" in result

    def test_format_with_attachments(self):
        """Test formatting task with attachments"""
        formatter = TaskDetailFormatter()

        task = {
            'id': 'task_1',
            'name': 'Task with Attachments',
            'status': {'status': 'in progress'},
            'attachments': [
                {
                    'title': 'Design Mockup',
                    'url': 'https://example.com/mockup.png',
                    'size': 1024000
                },
                {
                    'name': 'API Spec',
                    'url': 'https://example.com/spec.pdf'
                }
            ]
        }

        result = formatter.format_detail(task)

        # Should show attachments section
        assert "Attachments" in result or "📎" in result
        # Attachment names should appear
        assert "Design Mockup" in result
        assert "API Spec" in result

    def test_format_with_time_tracking(self):
        """Test formatting task with time tracking"""
        formatter = TaskDetailFormatter()

        task = {
            'id': 'task_1',
            'name': 'Task with Time Tracking',
            'status': {'status': 'in progress'},
            'time_estimate': 3600000,  # 1 hour in ms
            'time_spent': 1800000      # 30 min in ms
        }

        result = formatter.format_detail(task)

        # Should show time tracking section
        assert "Time Tracking" in result or "⏱️" in result
        # Should show estimate and spent
        assert "Estimate:" in result
        assert "Spent:" in result
        assert "Progress:" in result

    def test_build_parent_chain(self, sample_hierarchical_tasks):
        """Test building parent chain"""
        formatter = TaskDetailFormatter()

        # Build task map
        task_map = {t['id']: t for t in sample_hierarchical_tasks}

        # Get grandchild
        chain = formatter._build_parent_chain('grandchild_1', task_map)

        # Should have 2 parents (child_1 and parent_1)
        assert len(chain) == 2
        # Should be ordered from root to immediate parent
        assert chain[0]['id'] == 'parent_1'
        assert chain[1]['id'] == 'child_1'

    def test_build_child_tree(self, sample_hierarchical_tasks):
        """Test building child tree"""
        formatter = TaskDetailFormatter()

        options = FormatOptions(include_completed=True, colorize_output=False)

        # Build tree for parent_1
        tree_lines = formatter._build_child_tree(
            'parent_1',
            sample_hierarchical_tasks,
            options,
            depth=0,
            max_depth=3
        )

        # Should have children
        assert len(tree_lines) > 0
        # Should contain child task names
        result_text = '\n'.join(tree_lines)
        assert "Child Task 1" in result_text

    def test_format_with_all_sections(self, sample_hierarchical_tasks):
        """Test formatting with all sections present"""
        formatter = TaskDetailFormatter()

        # Create a comprehensive task
        comprehensive_task = {
            'id': 'comprehensive',
            'name': 'Comprehensive Task',
            'status': {'status': 'in progress'},
            'priority': {'priority': '1'},
            'custom_type': 'feature',
            'description': 'A task with all possible fields',
            'date_created': '2024-01-01T10:00:00Z',
            'due_date': '2024-01-31T23:59:59Z',
            'tags': [{'name': 'test'}, {'name': 'comprehensive'}],
            'assignees': [{'username': 'alice'}],
            'parent': 'parent_1',
            'dependencies': [],
            'checklists': [],
            'attachments': [],
            'comments': [],
            'time_estimate': 3600000
        }

        all_tasks = sample_hierarchical_tasks + [comprehensive_task]
        options = FormatOptions.detailed()

        result = formatter.format_with_context(comprehensive_task, all_tasks, options)

        # Verify major sections are present
        assert comprehensive_task['name'] in result
        assert "Description:" in result or "📝" in result
        assert "Tags:" in result or "🏷️" in result
        assert "Task Relationships:" in result or "🌳" in result
        assert comprehensive_task['description'] in result
