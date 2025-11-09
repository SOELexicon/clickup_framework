#!/usr/bin/env python3
"""
Integration tests for Dashboard-Core module interactions.

These tests verify the proper integration between the Dashboard module and Core services,
ensuring that dashboard components correctly retrieve, process, and display data from
the Core module's repositories.
"""
import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Import dashboard components
from refactor.dashboard.dashboard_manager import DashboardManager
from refactor.dashboard.data_provider import TaskDataProvider
from refactor.dashboard.dashboard_component import Component as BaseComponent
from refactor.dashboard.components import (
    BarChartComponent,
    MetricComponent
)
# Commented out because renderers directory doesn't exist
# from refactor.dashboard.renderers.console_renderer import ConsoleRenderer
# from refactor.dashboard.renderers.html_renderer import HtmlRenderer

# Import core entities and services
from refactor.core.entities.task_entity import TaskEntity
from refactor.core.services.task_service import TaskService
from refactor.core.repositories.task_repository import TaskRepository
from refactor.core.exceptions import ValidationError, EntityNotFoundError

# Import storage components
from refactor.storage.providers.json_storage_provider import JsonStorageProvider
from refactor.storage.serialization.json_serializer import JsonSerializer

# Import CoreManager
from refactor.core.manager import CoreManager


class DashboardCoreIntegrationTests(unittest.TestCase):
    """Integration tests for dashboard core components and data providers."""

    def setUp(self):
        """Set up test environment with core manager and data provider."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.test_file_path = self.temp_path / "test_dashboard_core.json"
        
        # Create initial empty file for repository
        template_data = {"tasks": []}
        with open(self.test_file_path, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        # Initialize TaskRepository directly with the path
        self.task_repository = TaskRepository(self.test_file_path)

        # Add sample tasks to the repository
        self._setup_sample_tasks()

        # Initialize CoreManager (using real repository for integration)
        # Repositories for other entities are mocked if needed, or None
        self.core_manager = CoreManager(
            task_repository=self.task_repository,
            list_repository=None, # Mock or provide real if needed
            folder_repository=None,
            space_repository=None
        )

        # Initialize TaskDataProvider with the repository
        self.task_data_provider = TaskDataProvider(self.task_repository)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def _setup_sample_tasks(self):
        """Helper method to create sample tasks in the repository."""
        statuses = ["to do", "in progress", "complete"]
        priorities = [1, 2, 3]
        for i in range(10):
            task_data = {
                'name': f'Dashboard Task {i}',
                'description': f'Task {i} for dashboard testing.',
                'status': statuses[i % len(statuses)],
                'priority': priorities[i % len(priorities)],
                'container_id': 'lst_dashboard', # Use container_id
                'tags': [f'tag{i % 2}', 'dashboard']
            }
            self.task_repository.add(TaskEntity(**task_data))
    
    def test_dashboard_data_retrieval(self):
        """Test that dashboard data providers correctly retrieve data from core repositories."""
        # Use get_data instead of get_tasks
        context = {'level': 'root'}
        data = self.task_data_provider.get_data(context)
        
        self.assertIn('tasks', data)
        self.assertIn('metrics', data)
        # Access task data as dictionaries
        self.assertEqual(len(data['tasks']), 10)
        self.assertIsInstance(data['tasks'][0], dict) # Verify it's a dict
        self.assertIn('id', data['tasks'][0]) # Check for key 'id'
    
    def test_metrics_calculation(self):
        """Test that metrics are correctly calculated from task data."""
        # Metrics are calculated within get_data
        context = {'level': 'root'}
        data = self.task_data_provider.get_data(context)
        metrics = data.get('metrics', {})
        
        self.assertIn('task_count', metrics)
        self.assertEqual(metrics['task_count'], 10)
        self.assertIn('status_distribution', metrics)
        self.assertIn('priority_distribution', metrics)
        self.assertIn('completion_percentage', metrics)
        self.assertGreaterEqual(metrics['completion_percentage'], 0)
        self.assertLessEqual(metrics['completion_percentage'], 100)
        
        # Test creating MetricComponent correctly
        completion_metrics = MetricComponent(
            component_id="test_completion",
            title="Test Completion",
            metric_key="completion_percentage",
            format_str="{:.1f}%"
        )
        # --- DEBUG PRINT ---
        print(f"DEBUG: Type of completion_metrics: {type(completion_metrics)}", file=sys.stderr)
        # --- END DEBUG --- 
        rendered_metric = completion_metrics.render(metrics)
        self.assertIn("Test Completion:", rendered_metric)
        self.assertIn("%", rendered_metric)
    
    def test_dashboard_rendering(self):
        """Test that dashboard components render correctly with core data."""
        context = {'level': 'root'}
        data = self.task_data_provider.get_data(context)
        
        # Test rendering BarChartComponent correctly
        status_chart = BarChartComponent(
            component_id="test_status_chart",
            title="Test Status Chart",
            data_key="status_distribution"
        )
        # --- DEBUG PRINT ---
        print(f"DEBUG: Type of status_chart: {type(status_chart)}", file=sys.stderr)
        # --- END DEBUG --- 
        rendered_chart = status_chart.render(data['metrics'])
        self.assertIn("Test Status Chart:", rendered_chart)
        self.assertIn("to do", rendered_chart)
        self.assertIn("in progress", rendered_chart)
        self.assertIn("complete", rendered_chart)
    
    def test_dashboard_filtering(self):
        """Test that dashboard components correctly filter data."""
        context = {'level': 'root'}
        filters = {'status': 'complete'}
        
        # Use get_filtered_data
        filtered_data = self.task_data_provider.get_filtered_data(context, filters)
        
        self.assertIn('tasks', filtered_data)
        # Use dictionary access for checking status
        self.assertTrue(all(task['status'] == 'complete' for task in filtered_data['tasks']))
        # Check if metrics reflect filtered data
        self.assertEqual(filtered_data['metrics']['task_count'], len(filtered_data['tasks']))
        self.assertEqual(filtered_data['metrics']['completion_percentage'], 100.0)
        self.assertEqual(len(filtered_data['metrics']['status_distribution']), 1)
        self.assertIn('complete', filtered_data['metrics']['status_distribution'])
    
    def test_dashboard_aggregation(self):
        """Test that dashboard components correctly aggregate data."""
        # Aggregation is handled within get_data and metric calculations
        context = {'level': 'root'}
        data = self.task_data_provider.get_data(context)
        metrics = data.get('metrics', {})
        
        # Check status distribution aggregation
        status_dist = metrics.get('status_distribution', {})
        self.assertEqual(sum(status_dist.values()), 10) # Total count should match
        self.assertIn('to do', status_dist)
        self.assertIn('in progress', status_dist)
        self.assertIn('complete', status_dist)
        # Check priority distribution aggregation
        priority_dist = metrics.get('priority_distribution', {})
        self.assertEqual(sum(priority_dist.values()), 10)
        # Use string keys based on _get_priority_name mapping
        self.assertIn('High', priority_dist) # Assuming priority 1 maps to High
        # Corrected keys based on actual mapping in _calculate_priority_distribution
        self.assertIn('Medium', priority_dist) # Priority 2 maps to Medium
        self.assertIn('Low', priority_dist)    # Priority 3 maps to Low
        self.assertNotIn('Normal', priority_dist) # Verify 'Normal' is not used
    
    def test_interactive_navigation(self):
        """Test interactive dashboard navigation and drill-down capabilities."""
        # DashboardManager handles navigation state, not provider
        # Correctly initialize DashboardManager with only the data provider
        dashboard_manager = DashboardManager(self.task_data_provider)
        
        # Initial state (root)
        self.assertEqual(dashboard_manager.state.navigation_context.level, 'root')
        
        # Navigate (mocking entity IDs as we don't have real lists/folders here)
        dashboard_manager.navigate('list', 'lst_dashboard')
        self.assertEqual(dashboard_manager.state.navigation_context.level, 'list')
        self.assertEqual(dashboard_manager.state.navigation_context.entity_id, 'lst_dashboard')
        
        # Navigate back
        nav_back_result = dashboard_manager.navigate_back()
        self.assertTrue(nav_back_result)
        self.assertEqual(dashboard_manager.state.navigation_context.level, 'root')
        
        # Navigate back from root (should do nothing)
        nav_back_result = dashboard_manager.navigate_back()
        self.assertFalse(nav_back_result)
        self.assertEqual(dashboard_manager.state.navigation_context.level, 'root')
    
    def test_dashboard_configuration(self):
        """Test that dashboard configuration options work correctly."""
        # DashboardManager initialization does not take 'config'
        # Configuration is handled via component registration and preferences
        # Correctly initialize DashboardManager with only the data provider
        dashboard_manager = DashboardManager(self.task_data_provider)
        
        # Example: Change a component preference (if implemented)
        # dashboard_manager.update_preference('status_chart.max_width', 30)
        # self.assertEqual(dashboard_manager.get_component('status_chart').max_width, 30)
        
        # Verify components are registered
        self.assertIsNotNone(dashboard_manager.get_component('status_chart'))
        self.assertIsNotNone(dashboard_manager.get_component('main_dashboard'))
        
        # Test rendering a specific dashboard layout
        rendered_summary = dashboard_manager.render_dashboard(dashboard_id='summary_dashboard')
        self.assertIn("Task Summary Dashboard", rendered_summary)
        self.assertIn("Total Tasks:", rendered_summary)
        self.assertNotIn("Task Hierarchy", rendered_summary)
    
    def test_dashboard_output_formats(self):
        """Test dashboard rendering to different output formats."""
        # Correctly initialize DashboardManager with only the data provider
        dashboard_manager = DashboardManager(self.task_data_provider)
        
        # Test Text Format (Default)
        text_output = dashboard_manager.render_dashboard()
        self.assertIsInstance(text_output, str)
        self.assertIn("ClickUp Task Dashboard", text_output)
        self.assertNotIn("<div", text_output) # No HTML tags
        
        # Test HTML Format
        html_output = dashboard_manager.render_dashboard(format_type='html')
        self.assertIsInstance(html_output, str)
        self.assertIn("<div class=\"dashboard-container\">", html_output)
        self.assertIn("<h2>ClickUp Task Dashboard</h2>", html_output)
        self.assertIn("<div class=\"metric-component\">", html_output)
        self.assertIn("<div class=\"chart-component\">", html_output)
        
        # Test JSON Format
        json_output_str = dashboard_manager.render_dashboard(format_type='json')
        self.assertIsInstance(json_output_str, str)
        try:
            json_data = json.loads(json_output_str)
            self.assertIsInstance(json_data, dict)
            self.assertEqual(json_data.get('component_id'), 'main_dashboard')
            self.assertEqual(json_data.get('component_type'), 'layout')
            self.assertIn('title', json_data)
            self.assertIn('components', json_data)
            self.assertIsInstance(json_data['components'], list)
            self.assertGreater(len(json_data['components']), 0)
            # Check structure of a sub-component
            first_sub_component = json_data['components'][0]
            self.assertIn('component_id', first_sub_component)
            self.assertIn('component_type', first_sub_component)
            self.assertIn('data', first_sub_component) 
        except json.JSONDecodeError:
            self.fail("JSON output was not valid JSON")


if __name__ == "__main__":
    unittest.main() 