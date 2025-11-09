"""
Unit tests for the visualization plugin.
"""
import os
import sys
import unittest
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from refactor.plugins.sample.visualization.visualization_plugin import VisualizationPlugin, ASCIIChartRenderer


class MockLogger:
    """Mock logger for testing."""
    def __init__(self):
        self.logs = []
    
    def info(self, message):
        self.logs.append(('INFO', message))
    
    def warning(self, message):
        self.logs.append(('WARNING', message))
    
    def error(self, message):
        self.logs.append(('ERROR', message))


class TestVisualizationPlugin(unittest.TestCase):
    """Test cases for the VisualizationPlugin."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'render_backend': 'ascii',  # Use ASCII for tests to avoid matplotlib dependency
            'default_charts': ['status_distribution', 'priority_distribution'],
            'chart_theme': 'default',
            'export_formats': ['png'],
            'interactive': True,
            'custom_colors': {
                'to do': '#3498db',
                'in progress': '#f39c12',
                'in review': '#9b59b6',
                'complete': '#2ecc71'
            }
        }
        
        self.plugin = VisualizationPlugin('test_visualization', self.config)
        self.logger = MockLogger()
        self.plugin.initialize({'logger': self.logger})
        
        # Sample tasks for testing
        self.tasks = [
            {
                'id': 'task1',
                'name': 'Task 1',
                'status': 'to do',
                'priority': 1,
                'tags': ['bug', 'critical']
            },
            {
                'id': 'task2',
                'name': 'Task 2',
                'status': 'in progress',
                'priority': 2,
                'tags': ['feature']
            },
            {
                'id': 'task3',
                'name': 'Task 3',
                'status': 'complete',
                'priority': 3,
                'tags': ['documentation'],
                'date_completed': int(datetime.now().timestamp())
            },
            {
                'id': 'task4',
                'name': 'Task 4',
                'status': 'complete',
                'priority': 1,
                'tags': ['bug', 'ui'],
                'date_completed': int(datetime.now().timestamp())
            },
            {
                'id': 'task5',
                'name': 'Task 5',
                'status': 'in review',
                'priority': 2,
                'tags': ['feature', 'backend']
            }
        ]
    
    def test_initialization(self):
        """Test plugin initialization."""
        self.assertEqual(self.plugin.plugin_id, 'test_visualization')
        self.assertEqual(self.plugin.config, self.config)
        self.assertIn('ascii', self.plugin.renderers)
    
    def test_validate_config(self):
        """Test configuration validation."""
        valid, errors = self.plugin.validate_config()
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)
        
        # Test invalid configuration
        invalid_plugin = VisualizationPlugin('test', {'render_backend': 'invalid_backend'})
        valid, errors = invalid_plugin.validate_config()
        self.assertFalse(valid)
        self.assertTrue(any('render_backend' in error for error in errors))
    
    def test_get_available_chart_types(self):
        """Test retrieving available chart types."""
        chart_types = self.plugin.get_available_chart_types()
        self.assertIsInstance(chart_types, list)
        self.assertGreater(len(chart_types), 0)
        
        chart_ids = [chart['id'] for chart in chart_types]
        expected_charts = [
            'status_distribution', 'priority_distribution', 'completion_trend',
            'tag_distribution', 'task_completion_rate', 'task_hierarchy_tree'
        ]
        
        for chart_id in expected_charts:
            self.assertIn(chart_id, chart_ids)
    
    def test_create_status_distribution_chart(self):
        """Test creating a status distribution chart."""
        chart = self.plugin.create_chart('status_distribution', self.tasks)
        
        self.assertIsNotNone(chart)
        self.assertEqual(chart['chart_type'], 'status_distribution')
        self.assertIn('ascii', chart)
        self.assertIn('data', chart)
        
        # Check data content
        data = chart['data']
        self.assertIn('labels', data)
        self.assertIn('values', data)
        
        # Verify all statuses are represented
        statuses = set(task['status'] for task in self.tasks)
        for status in statuses:
            self.assertIn(status, data['labels'])
    
    def test_create_priority_distribution_chart(self):
        """Test creating a priority distribution chart."""
        chart = self.plugin.create_chart('priority_distribution', self.tasks)
        
        self.assertIsNotNone(chart)
        self.assertEqual(chart['chart_type'], 'priority_distribution')
        self.assertIn('ascii', chart)
        self.assertIn('data', chart)
        
        # Check data content
        data = chart['data']
        self.assertIn('labels', data)
        self.assertIn('values', data)
        
        # Verify priorities are represented (converted to labels)
        priorities = set(self.plugin._get_priority_label(task['priority']) for task in self.tasks)
        for priority_label in priorities:
            self.assertIn(priority_label, data['labels'])
    
    def test_create_tag_distribution_chart(self):
        """Test creating a tag distribution chart."""
        chart = self.plugin.create_chart('tag_distribution', self.tasks)
        
        self.assertIsNotNone(chart)
        self.assertEqual(chart['chart_type'], 'tag_distribution')
        self.assertIn('ascii', chart)
        self.assertIn('data', chart)
        
        # Check data content
        data = chart['data']
        self.assertIn('labels', data)
        self.assertIn('values', data)
        
        # Verify at least some tags are represented
        all_tags = set()
        for task in self.tasks:
            all_tags.update(task.get('tags', []))
        
        self.assertGreater(len(all_tags), 0)
        for tag in data['labels']:
            self.assertIn(tag, all_tags)
    
    def test_create_task_completion_rate_chart(self):
        """Test creating a task completion rate chart."""
        chart = self.plugin.create_chart('task_completion_rate', self.tasks)
        
        self.assertIsNotNone(chart)
        self.assertEqual(chart['chart_type'], 'task_completion_rate')
        self.assertIn('ascii', chart)
        self.assertIn('data', chart)
        
        # Check data content
        data = chart['data']
        self.assertIn('completed', data)
        self.assertIn('total', data)
        self.assertIn('rate', data)
        
        # Verify the completion rate calculation
        completed_tasks = sum(1 for task in self.tasks if task.get('status') == 'complete')
        total_tasks = len(self.tasks)
        expected_rate = (completed_tasks / total_tasks) * 100
        
        self.assertEqual(data['completed'], completed_tasks)
        self.assertEqual(data['total'], total_tasks)
        self.assertEqual(data['rate'], expected_rate)
    
    def test_create_task_hierarchy_tree(self):
        """Test creating a task hierarchy tree chart."""
        # Create tasks with parent-child relationships
        hierarchy_tasks = [
            {'id': 'parent1', 'name': 'Parent 1', 'status': 'in progress', 'parent_id': None},
            {'id': 'child1', 'name': 'Child 1', 'status': 'to do', 'parent_id': 'parent1'},
            {'id': 'child2', 'name': 'Child 2', 'status': 'complete', 'parent_id': 'parent1'},
            {'id': 'grandchild1', 'name': 'Grandchild 1', 'status': 'in review', 'parent_id': 'child1'}
        ]
        
        chart = self.plugin.create_chart('task_hierarchy_tree', hierarchy_tasks)
        
        self.assertIsNotNone(chart)
        self.assertEqual(chart['chart_type'], 'task_hierarchy_tree')
        self.assertIn('ascii', chart)
        self.assertIn('data', chart)
        
        # Check tree data structure
        data = chart['data']
        self.assertIn('tree', data)
        
        # Verify tree structure - should have just one root node
        tree = data['tree']
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['id'], 'parent1')
        
        # Check children
        children = tree[0]['children']
        self.assertEqual(len(children), 2)
        
        # Verify child IDs
        child_ids = [child['id'] for child in children]
        self.assertIn('child1', child_ids)
        self.assertIn('child2', child_ids)
        
        # Find the child with grandchildren and verify
        for child in children:
            if child['id'] == 'child1':
                grandchildren = child['children']
                self.assertEqual(len(grandchildren), 1)
                self.assertEqual(grandchildren[0]['id'], 'grandchild1')
    
    def test_ascii_chart_renderer(self):
        """Test the ASCII chart renderer."""
        # Test bar chart
        labels = ['A', 'B', 'C']
        values = [10, 5, 8]
        bar_chart = ASCIIChartRenderer.bar_chart(labels, values, "Test Chart")
        
        self.assertIsInstance(bar_chart, str)
        self.assertIn("Test Chart", bar_chart)
        for label in labels:
            self.assertIn(label, bar_chart)
        
        # Test progress bar
        progress = ASCIIChartRenderer.progress_bar(7, 10)
        self.assertIsInstance(progress, str)
        self.assertIn("70.0%", progress)
    
    def test_invalid_chart_type(self):
        """Test behavior with an invalid chart type."""
        result = self.plugin.create_chart('non_existent_chart', self.tasks)
        self.assertIsNone(result)
        
        # Check that an error was logged
        error_logs = [log for log in self.logger.logs if log[0] == 'ERROR']
        self.assertGreater(len(error_logs), 0)
        self.assertTrue(any('Unknown chart type' in log[1] for log in error_logs))


if __name__ == '__main__':
    unittest.main() 