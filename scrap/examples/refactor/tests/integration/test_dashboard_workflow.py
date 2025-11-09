#!/usr/bin/env python3
"""
Integration tests for Dashboard Generation Workflow.

These tests verify the complete dashboard generation lifecycle, including data
fetching, metrics calculation, rendering to different formats, and interactive 
navigation across all integrated components.
"""
# Standard library imports
import unittest
import tempfile
import json
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Core components
from refactor.core.entities.task_entity import TaskEntity
from refactor.core.services.task_service import TaskService
from refactor.core.repositories.task_repository import TaskRepository

# Dashboard components
from refactor.dashboard.dashboard_manager import DashboardManager
from refactor.dashboard.data_provider import TaskDataProvider
from refactor.dashboard.dashboard_component import Component as BaseComponent
from refactor.dashboard.components import (
    BarChartComponent,
    MetricComponent as CompletionMetrics
)

# Storage components
from refactor.storage.providers.json_storage_provider import JsonStorageProvider
from refactor.storage.serialization.json_serializer import JsonSerializer


class DashboardGenerationWorkflowTests(unittest.TestCase):
    """Integration tests for the complete dashboard generation workflow."""

    def setUp(self):
        """Set up test environment with temporary test files and sample task data."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a test file path
        self.test_file_path = self.temp_path / "test_dashboard_workflow.json"
        
        # Create initial empty file for repository
        self.test_file_path.touch()
        with open(self.test_file_path, 'w') as f:
            json.dump({"tasks": {}}, f)
        
        # Create output directory for dashboard export tests
        self.output_dir = self.temp_path / "dashboard_output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize storage components
        self.serializer = JsonSerializer()
        self.storage_provider = JsonStorageProvider()
        
        # Initialize repository and service
        self.task_repository = TaskRepository(self.test_file_path)
        self.task_service = TaskService(self.task_repository)
        
        # Initialize dashboard components
        self.task_data_provider = TaskDataProvider(self.task_service)
        self.dashboard_manager = DashboardManager(self.task_repository)
        
        # Create initial template structure
        template_data = {
            "spaces": [
                {
                    "id": "spc_test001",
                    "name": "Test Space"
                }
            ],
            "folders": [
                {
                    "id": "fld_test001",
                    "name": "Test Folder",
                    "space_id": "spc_test001"
                }
            ],
            "lists": [
                {
                    "id": "lst_test001",
                    "name": "Test List",
                    "folder_id": "fld_test001"
                }
            ],
            "tasks": [],
            "relationships": []
        }
        
        with open(self.test_file_path, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        # Set up sample task data with various attributes
        self._setup_sample_tasks()

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def _setup_sample_tasks(self):
        """Create sample tasks with different attributes for dashboard testing."""
        # Create a set of tasks with different statuses, priorities, and tags
        status_options = ["to do", "in progress", "in review", "complete"]
        priority_options = [1, 2, 3, 4]  # Urgent, High, Normal, Low
        
        # Create 40 tasks with varied attributes for thorough testing
        for i in range(40):
            status = status_options[i % 4]
            priority = priority_options[i % 4]
            
            # Determine tags based on task number
            tags = ["test", f"tag{i % 5}"]
            if i % 3 == 0:
                tags.append("important")
            if i % 7 == 0:
                tags.append("bug")
            if status == "complete":
                tags.append("done")
            
            # Create task with varying attributes
            self.task_service.create_task(**{
                "name": f"Task {i+1}",
                "description": f"Description for task {i+1}",
                "status": status,
                "priority": priority,
                "container_id": "lst_test001",
                "tags": tags
            })
        
        # Create a project structure with parent and child tasks
        parent_task = self.task_service.create_task(**{
            "name": "Project Alpha",
            "description": "Main project task",
            "status": "in progress",
            "priority": 2,
            "container_id": "lst_test001",
            "tags": ["project", "alpha"]
        })
        
        # Add subtasks to the project
        for i in range(5):
            subtask_status = "complete" if i < 2 else "in progress" if i < 4 else "to do"
            
            self.task_service.create_task(**{
                "name": f"Alpha Subtask {i+1}",
                "description": f"Subtask {i+1} for Project Alpha",
                "status": subtask_status,
                "priority": 2,
                "container_id": "lst_test001",
                "parent_id": parent_task.id,
                "tags": ["subtask", "alpha"]
            })
        
        # Create tasks with different creation dates for timeline testing
        current_time = time.time()
        one_day = 86400  # seconds in a day
        
        for i in range(10):
            days_ago = 30 - (i * 3)  # Tasks spread over the last 30 days
            timestamp = current_time - (days_ago * one_day)
            
            status = "complete" if i < 6 else "in progress" if i < 8 else "to do"
            
            task = TaskEntity(
                id=f"tsk_timeline{i+1}",
                name=f"Timeline Task {i+1}",
                description=f"Task created {days_ago} days ago",
                status=status,
                priority=2,
                container_id="lst_test001",
                tags=["timeline"],
                created_at=int(timestamp),
                updated_at=int(timestamp + one_day)
            )
            
            self.task_repository.save(task)
        
        # Add relationships between tasks for dependency visualization testing
        for i in range(1, 5):
            # Create chain: Task 1 -> Task 2 -> Task 3 -> Task 4 -> Task 5
            if i < 5:
                self.task_service.add_relationship(f"tsk_timeline{i}", f"tsk_timeline{i+1}", "blocks")
                self.task_service.add_relationship(f"tsk_timeline{i+1}", f"tsk_timeline{i}", "depends_on")
    
    def test_dashboard_data_aggregation(self):
        """Test dashboard data aggregation from multiple sources."""
        # Create a dashboard with multiple data sources
        self.dashboard_manager.add_component(BarChartComponent(self.task_data_provider))
        self.dashboard_manager.add_component(BarChartComponent(self.task_data_provider))
        self.dashboard_manager.add_component(CompletionMetrics(self.task_data_provider))
        
        # Create a filtered data provider (only "important" tasks)
        important_provider = TaskDataProvider(
            self.task_service,
            filters={"tags": ["important"]}
        )
        self.dashboard_manager.add_component(
            BarChartComponent(important_provider, title="Important Tasks Status")
        )
        
        # Create a console renderer
        console_renderer = ConsoleRenderer()
        
        # Render the dashboard
        dashboard_output = self.dashboard_manager.render(console_renderer)
        
        # Verify that data from both providers appears in the output
        self.assertIn("Task Status Distribution", dashboard_output)
        self.assertIn("Task Priority Distribution", dashboard_output)
        self.assertIn("Important Tasks Status", dashboard_output)
        
        # Verify that aggregated metrics are included
        self.assertIn("Completion Metrics", dashboard_output)
        
        # Verify that the filtered provider shows only a subset of tasks
        all_tasks_status = self.task_data_provider.get_aggregated_data(group_by="status")
        important_tasks_status = important_provider.get_aggregated_data(group_by="status")
        
        # Important tasks should be fewer than all tasks
        self.assertLess(
            sum(len(tasks) for tasks in important_tasks_status.values()),
            sum(len(tasks) for tasks in all_tasks_status.values())
        )
    
    def test_dashboard_metrics_calculation(self):
        """Test dashboard metrics calculation and statistics."""
        # Create a completion metrics component
        completion_metrics = CompletionMetrics(self.task_data_provider)
        
        # Calculate metrics
        metrics = completion_metrics.calculate_metrics()
        
        # Verify expected metrics are present
        self.assertIn("total_tasks", metrics)
        self.assertIn("completed_tasks", metrics)
        self.assertIn("completion_percentage", metrics)
        self.assertIn("status_counts", metrics)
        self.assertIn("priority_counts", metrics)
        
        # Verify metrics make mathematical sense
        self.assertEqual(
            metrics["total_tasks"],
            sum(metrics["status_counts"].values())
        )
        
        self.assertEqual(
            metrics["total_tasks"],
            sum(metrics["priority_counts"].values())
        )
        
        # Calculate expected completion percentage
        expected_percentage = (metrics["completed_tasks"] / metrics["total_tasks"]) * 100
        self.assertAlmostEqual(metrics["completion_percentage"], expected_percentage)
        
        # Verify status counts
        status_counts = metrics["status_counts"]
        self.assertEqual(metrics["completed_tasks"], status_counts.get("complete", 0))
        
        # Add burndown chart for trend analysis
        burndown_chart = BurndownChart(self.task_data_provider)
        
        # Calculate burndown data
        burndown_data = burndown_chart.calculate_data()
        
        # Verify burndown data structure
        self.assertIn("dates", burndown_data)
        self.assertIn("remaining_tasks", burndown_data)
        self.assertIn("ideal_burndown", burndown_data)
        
        # Verify burndown data makes logical sense
        self.assertEqual(len(burndown_data["dates"]), len(burndown_data["remaining_tasks"]))
        self.assertEqual(len(burndown_data["dates"]), len(burndown_data["ideal_burndown"]))
        
        # First day should have the highest number of remaining tasks
        self.assertEqual(
            max(burndown_data["remaining_tasks"]),
            burndown_data["remaining_tasks"][0]
        )
    
    def test_filtering_and_grouping(self):
        """Test filtering and grouping of dashboard data."""
        # Test filtering by different criteria
        filter_tests = [
            {"status": "complete"},
            {"priority": 1},  # Urgent
            {"tags": ["important"]},
            {"status": "in progress", "priority": 2}  # High priority in-progress tasks
        ]
        
        for filters in filter_tests:
            # Create filtered data provider
            filtered_provider = TaskDataProvider(
                self.task_service,
                filters=filters
            )
            
            # Get filtered tasks
            filtered_tasks = filtered_provider.get_tasks()
            
            # Verify filter was applied correctly
            if "status" in filters:
                for task in filtered_tasks:
                    self.assertEqual(task.status, filters["status"])
            
            if "priority" in filters:
                for task in filtered_tasks:
                    self.assertEqual(task.priority, filters["priority"])
            
            if "tags" in filters:
                for task in filtered_tasks:
                    for tag in filters["tags"]:
                        self.assertIn(tag, task.tags)
        
        # Test grouping by different attributes
        grouping_tests = ["status", "priority", "tags"]
        
        for group_by in grouping_tests:
            # Create data provider with grouping
            grouped_provider = TaskDataProvider(
                self.task_service,
                aggregation={"group_by": group_by}
            )
            
            # Get grouped data
            grouped_data = grouped_provider.get_aggregated_data()
            
            # Verify data was grouped correctly
            if group_by == "status":
                self.assertIn("to do", grouped_data)
                self.assertIn("in progress", grouped_data)
                self.assertIn("in review", grouped_data)
                self.assertIn("complete", grouped_data)
            
            elif group_by == "priority":
                self.assertIn(1, grouped_data)
                self.assertIn(2, grouped_data)
                self.assertIn(3, grouped_data)
                self.assertIn(4, grouped_data)
        
        # Test combined filtering and grouping
        filtered_grouped_provider = TaskDataProvider(
            self.task_service,
            filters={"tags": ["important"]},
            aggregation={"group_by": "status"}
        )
        
        filtered_grouped_data = filtered_grouped_provider.get_aggregated_data()
        
        # Verify combined filtering and grouping
        for status, tasks in filtered_grouped_data.items():
            for task in tasks:
                self.assertIn("important", task.tags)
                self.assertEqual(task.status, status)
    
    def test_dashboard_view_customization(self):
        """Test dashboard view customization features."""
        # Create a dashboard with custom configuration
        custom_dashboard = DashboardManager(
            config={
                "title": "Custom Test Dashboard",
                "theme": "dark",
                "layout": "grid",
                "show_filters": True,
                "date_range": {
                    "start": int(time.time()) - (30 * 86400),  # 30 days ago
                    "end": int(time.time())
                }
            }
        )
        
        # Add components
        custom_dashboard.add_component(BarChartComponent(self.task_data_provider))
        custom_dashboard.add_component(BarChartComponent(self.task_data_provider))
        
        # Render the dashboard
        console_renderer = ConsoleRenderer()
        output = custom_dashboard.render(console_renderer)
        
        # Verify custom configuration was applied
        self.assertIn("Custom Test Dashboard", output)
        
        # Test view switching (summary vs detailed)
        detail_dashboard = DashboardManager(
            config={"view_mode": "detailed"}
        )
        
        # Add components for both views
        detail_dashboard.add_component(
            CompletionMetrics(self.task_data_provider),
            view="summary"
        )
        
        detail_dashboard.add_component(
            BarChartComponent(self.task_data_provider),
            view="detailed"
        )
        
        # Test summary view
        detail_dashboard.set_view("summary")
        summary_output = detail_dashboard.render(console_renderer)
        self.assertIn("Completion Metrics", summary_output)
        self.assertNotIn("Task Status Distribution", summary_output)
        
        # Test detailed view
        detail_dashboard.set_view("detailed")
        detailed_output = detail_dashboard.render(console_renderer)
        self.assertIn("Task Status Distribution", detailed_output)
        self.assertNotIn("Completion Metrics", detailed_output)
        
        # Test custom component ordering
        ordered_dashboard = DashboardManager()
        
        # Add components with specific order
        ordered_dashboard.add_component(
            BarChartComponent(self.task_data_provider),
            order=2
        )
        
        ordered_dashboard.add_component(
            CompletionMetrics(self.task_data_provider),
            order=1
        )
        
        # Verify components are ordered correctly
        components = ordered_dashboard.get_components()
        self.assertEqual(components[0].title, "Completion Metrics")
        self.assertEqual(components[1].title, "Task Status Distribution")
    
    def test_rendering_to_different_formats(self):
        """Test rendering dashboard to different output formats."""
        # Create a dashboard with multiple components
        render_dashboard = DashboardManager(
            config={"title": "Format Test Dashboard"}
        )
        
        # Add components
        render_dashboard.add_component(BarChartComponent(self.task_data_provider))
        render_dashboard.add_component(CompletionMetrics(self.task_data_provider))
        
        # Test console rendering
        console_renderer = ConsoleRenderer()
        console_output = render_dashboard.render(console_renderer)
        
        # Verify console output format
        self.assertIsInstance(console_output, str)
        self.assertIn("Format Test Dashboard", console_output)
        self.assertIn("Task Status Distribution", console_output)
        
        # Test HTML rendering
        html_renderer = HtmlRenderer()
        html_output = render_dashboard.render(html_renderer)
        
        # Verify HTML output format
        self.assertIsInstance(html_output, str)
        self.assertIn("<html", html_output)
        self.assertIn("<title>Format Test Dashboard</title>", html_output)
        self.assertIn("</html>", html_output)
        
        # Test JSON rendering
        json_renderer = JsonRenderer()
        json_output = render_dashboard.render(json_renderer)
        
        # Verify JSON output format
        self.assertIsInstance(json_output, str)
        json_data = json.loads(json_output)
        self.assertIn("title", json_data)
        self.assertEqual(json_data["title"], "Format Test Dashboard")
        self.assertIn("components", json_data)
        
        # Test rendering to file
        html_file_path = self.output_dir / "dashboard.html"
        render_dashboard.render_to_file(html_renderer, html_file_path)
        
        # Verify file was created with content
        self.assertTrue(html_file_path.exists())
        with open(html_file_path, 'r') as f:
            file_content = f.read()
            self.assertIn("<html", file_content)
            self.assertIn("Format Test Dashboard", file_content)
        
        # Test JSON file export
        json_file_path = self.output_dir / "dashboard.json"
        render_dashboard.render_to_file(json_renderer, json_file_path)
        
        # Verify JSON file was created
        self.assertTrue(json_file_path.exists())
        with open(json_file_path, 'r') as f:
            json_data = json.load(f)
            self.assertEqual(json_data["title"], "Format Test Dashboard")
    
    def test_performance_with_large_datasets(self):
        """Test dashboard performance with large datasets."""
        # Create a larger test dataset (500 tasks)
        self._create_large_dataset(500)
        
        # Create a simple dashboard
        perf_dashboard = DashboardManager()
        perf_dashboard.add_component(BarChartComponent(self.task_data_provider))
        perf_dashboard.add_component(CompletionMetrics(self.task_data_provider))
        
        # Measure rendering time
        console_renderer = ConsoleRenderer()
        
        start_time = time.time()
        perf_dashboard.render(console_renderer)
        end_time = time.time()
        
        # Verify rendering time is reasonable (under 1 second for 500 tasks)
        self.assertLess(end_time - start_time, 1.0)
        
        # Test performance of different renderers
        renderers = [
            ConsoleRenderer(),
            HtmlRenderer(),
            JsonRenderer()
        ]
        
        for renderer in renderers:
            start_time = time.time()
            perf_dashboard.render(renderer)
            end_time = time.time()
            
            # Each renderer should be reasonably fast
            self.assertLess(end_time - start_time, 2.0)
        
        # Test performance of filtered datasets
        filtered_provider = TaskDataProvider(
            self.task_service,
            filters={"tags": ["important"]}
        )
        
        filtered_dashboard = DashboardManager()
        filtered_dashboard.add_component(BarChartComponent(filtered_provider))
        
        # Filtered dataset should render faster than full dataset
        start_time = time.time()
        filtered_dashboard.render(console_renderer)
        filtered_time = time.time() - start_time
        
        start_time = time.time()
        perf_dashboard.render(console_renderer)
        full_time = time.time() - start_time
        
        # Filtered should be faster (or at least not significantly slower)
        self.assertLessEqual(filtered_time, full_time * 1.1)
    
    def test_interactive_dashboard_navigation(self):
        """Test interactive dashboard navigation and drill-down capabilities."""
        # Create an interactive dashboard
        interactive_dashboard = DashboardManager(
            interactive=True,
            initial_view="summary"
        )
        
        # Add components to different views
        interactive_dashboard.add_component(
            CompletionMetrics(self.task_data_provider),
            view="summary"
        )
        
        interactive_dashboard.add_component(
            BarChartComponent(self.task_data_provider),
            view="details"
        )
        
        interactive_dashboard.add_component(
            BarChartComponent(self.task_data_provider),
            view="details"
        )
        
        # Verify initial view is set
        self.assertEqual(interactive_dashboard.current_view, "summary")
        
        # Test navigation between views
        interactive_dashboard.navigate_to("details")
        self.assertEqual(interactive_dashboard.current_view, "details")
        
        # Verify correct components are shown in each view
        summary_components = interactive_dashboard.get_components_for_view("summary")
        self.assertEqual(len(summary_components), 1)
        self.assertEqual(summary_components[0].title, "Completion Metrics")
        
        details_components = interactive_dashboard.get_components_for_view("details")
        self.assertEqual(len(details_components), 2)
        
        # Test task drill-down
        parent_task = self.task_service.get_task_by_name("Project Alpha")
        
        # Navigate to task-specific view
        interactive_dashboard.drill_down(parent_task.id)
        
        # Verify view changed to task-specific view
        self.assertEqual(interactive_dashboard.current_view, f"task_{parent_task.id}")
        
        # Add task-specific component to drill-down view
        task_provider = TaskDataProvider(
            self.task_service,
            filters={"parent_id": parent_task.id}
        )
        
        interactive_dashboard.add_component(
            BarChartComponent(task_provider, title="Subtask Status"),
            view=f"task_{parent_task.id}"
        )
        
        # Verify task-specific component is available
        task_view_components = interactive_dashboard.get_components()
        self.assertEqual(len(task_view_components), 1)
        self.assertEqual(task_view_components[0].title, "Subtask Status")
        
        # Test navigation back to main views
        interactive_dashboard.navigate_to("summary")
        self.assertEqual(interactive_dashboard.current_view, "summary")
        
        # Test breadcrumb tracking
        self.assertEqual(len(interactive_dashboard.navigation_history), 3)
        self.assertEqual(interactive_dashboard.navigation_history[0], "summary")
        self.assertEqual(interactive_dashboard.navigation_history[1], "details")
        self.assertEqual(interactive_dashboard.navigation_history[2], f"task_{parent_task.id}")
        
        # Test navigation back functionality
        interactive_dashboard.navigate_back()
        self.assertEqual(interactive_dashboard.current_view, f"task_{parent_task.id}")
        
        interactive_dashboard.navigate_back()
        self.assertEqual(interactive_dashboard.current_view, "details")
    
    def _create_large_dataset(self, num_tasks):
        """Helper method to create a larger dataset for performance testing."""
        status_options = ["to do", "in progress", "in review", "complete"]
        priority_options = [1, 2, 3, 4]
        
        for i in range(num_tasks):
            status = status_options[i % 4]
            priority = priority_options[i % 4]
            
            # Add some variety to tags
            tags = ["test"]
            if i % 5 == 0:
                tags.append("important")
            if i % 10 == 0:
                tags.append("bug")
            if i % 7 == 0:
                tags.append("feature")
            
            self.task_service.create_task(**{
                "name": f"Performance Task {i+1}",
                "description": f"Performance testing task {i+1}",
                "status": status,
                "priority": priority,
                "container_id": "lst_test001",
                "tags": tags
            })


if __name__ == "__main__":
    unittest.main() 