"""
Dashboard CLI Commands

This module provides commands for interacting with the dashboard.
"""
import sys
import json
import webbrowser
import tempfile
import os
from argparse import ArgumentParser, Namespace
from typing import Dict, Any, List, Optional

from ...core.interfaces.core_manager import CoreManager
from ...dashboard import DashboardManager, TaskDataProvider


class DashboardCommand:
    """
    Command for displaying a dashboard.
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize the dashboard command.
        
        Args:
            core_manager: Core manager instance
        """
        self.core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        Args:
            parser: Argument parser to configure
        """
        parser.add_argument(
            "file_path",
            help="Path to the clickup JSON template file"
        )
        parser.add_argument(
            "--format",
            choices=["text", "html", "json"],
            default="text",
            help="Output format (default: text)"
        )
        parser.add_argument(
            "--dashboard",
            default="main_dashboard",
            help="Dashboard ID to display (default: main_dashboard)"
        )
        parser.add_argument(
            "--level",
            choices=["root", "space", "folder", "list", "task"],
            default="root",
            help="Entity level to show in the dashboard (default: root)"
        )
        parser.add_argument(
            "--entity-id",
            help="Entity ID for focused view"
        )
        parser.add_argument(
            "--hierarchy",
            action="store_true",
            help="Show task hierarchy"
        )
        parser.add_argument(
            "--status-summary",
            action="store_true",
            help="Show status summary"
        )
        parser.add_argument(
            "--completion-metrics",
            action="store_true",
            help="Show completion metrics"
        )
        parser.add_argument(
            "--filter-status",
            help="Filter tasks by status"
        )
        parser.add_argument(
            "--filter-priority",
            type=int,
            help="Filter tasks by priority"
        )
        parser.add_argument(
            "--filter-tags",
            help="Filter tasks by tags (comma-separated)"
        )
        parser.add_argument(
            "--browser",
            action="store_true",
            help="Open HTML dashboard in browser (only with --format html)"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the dashboard command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code
        """
        # Initialize the dashboard manager
        dashboard_manager = DashboardManager(self.core_manager)
        
        # Set up navigation
        dashboard_manager.navigate(args.level, args.entity_id)
        
        # Apply filters if specified
        if args.filter_status:
            dashboard_manager.apply_filter("status", args.filter_status)
            
        if args.filter_priority is not None:
            dashboard_manager.apply_filter("priority", args.filter_priority)
            
        if args.filter_tags:
            tags = [tag.strip() for tag in args.filter_tags.split(",")]
            dashboard_manager.apply_filter("tags", tags)
        
        # Update dashboard preferences based on arguments
        if args.hierarchy:
            dashboard_manager.update_preference("show_hierarchy", True)
            
        if args.status_summary:
            dashboard_manager.update_preference("show_status_summary", True)
            
        if args.completion_metrics:
            dashboard_manager.update_preference("show_completion_metrics", True)
        
        # Render the dashboard
        output = dashboard_manager.render_dashboard(args.dashboard, args.format)
        
        # Handle output based on format and options
        if args.format == "html" and args.browser:
            # Create a temporary HTML file and open in browser
            with tempfile.NamedTemporaryFile(
                suffix=".html", 
                delete=False, 
                mode="w", 
                encoding="utf-8"
            ) as f:
                f.write(output)
                tmp_filename = f.name
            
            # Open the file in the default browser
            webbrowser.open(f"file://{tmp_filename}")
            print(f"Dashboard opened in browser. Temporary file: {tmp_filename}")
            return 0
        else:
            # Print to stdout
            print(output)
            return 0


class InteractiveDashboardCommand:
    """
    Command for launching an interactive dashboard with navigation.
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize the interactive dashboard command.
        
        Args:
            core_manager: Core manager instance
        """
        self.core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        Args:
            parser: Argument parser to configure
        """
        parser.add_argument(
            "file_path",
            help="Path to the clickup JSON template file"
        )
        parser.add_argument(
            "--format",
            choices=["text", "html"],
            default="html",
            help="Output format (default: html)"
        )
        parser.add_argument(
            "--browser",
            action="store_true",
            help="Open HTML dashboard in browser (only with --format html)"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the interactive dashboard command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code
        """
        # Initialize the dashboard manager
        dashboard_manager = DashboardManager(self.core_manager)
        
        # Start at the root level
        dashboard_manager.navigate("root")
        
        if args.format == "html":
            self._run_html_interactive_dashboard(dashboard_manager, args.browser)
            return 0
        else:
            self._run_text_interactive_dashboard(dashboard_manager)
            return 0
    
    def _run_html_interactive_dashboard(
        self, 
        dashboard_manager: DashboardManager, 
        use_browser: bool
    ) -> None:
        """
        Run the HTML interactive dashboard.
        
        Args:
            dashboard_manager: Dashboard manager instance
            use_browser: Whether to open in browser
        """
        # Generate the initial dashboard HTML
        output = dashboard_manager.render_dashboard("main_dashboard", "html")
        
        # Add interactive JavaScript for navigation
        output = self._add_interactive_js(output)
        
        if use_browser:
            # Create a temporary HTML file and open in browser
            with tempfile.NamedTemporaryFile(
                suffix=".html", 
                delete=False, 
                mode="w", 
                encoding="utf-8"
            ) as f:
                f.write(output)
                tmp_filename = f.name
            
            # Open the file in the default browser
            webbrowser.open(f"file://{tmp_filename}")
            print(f"Interactive dashboard opened in browser. Temporary file: {tmp_filename}")
        else:
            # Print the HTML to stdout
            print(output)
    
    def _add_interactive_js(self, html_content: str) -> str:
        """
        Add interactive JavaScript to the HTML content.
        
        Args:
            html_content: Original HTML content
            
        Returns:
            HTML content with interactive JavaScript
        """
        # Define the JavaScript for interactivity
        js_code = """
        <script>
        // Dashboard interaction code
        document.addEventListener('DOMContentLoaded', function() {
            // Set up click handlers for navigation
            setupNavigationHandlers();
            
            // Set up filter controls
            setupFilterControls();
            
            // Set up sorting for tables
            setupTableSorting();
        });
        
        function setupNavigationHandlers() {
            // Add click handlers to navigate between entities
            const taskItems = document.querySelectorAll('.task-name');
            taskItems.forEach(item => {
                item.addEventListener('click', function(e) {
                    const taskId = this.closest('li').dataset.taskId;
                    if (taskId) {
                        navigateToTask(taskId);
                    }
                });
            });
            
            // Add breadcrumb navigation
            const breadcrumbs = document.querySelectorAll('.breadcrumb-item');
            breadcrumbs.forEach(item => {
                item.addEventListener('click', function(e) {
                    const level = this.dataset.level;
                    const entityId = this.dataset.entityId;
                    navigateToEntity(level, entityId);
                });
            });
        }
        
        function setupFilterControls() {
            // Add filter change handlers
            const filterInputs = document.querySelectorAll('.filter-control');
            filterInputs.forEach(input => {
                input.addEventListener('change', function(e) {
                    applyFilter(this.name, this.value);
                });
            });
            
            // Add filter clear buttons
            const clearButtons = document.querySelectorAll('.clear-filter');
            clearButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    const filterName = this.dataset.filter;
                    clearFilter(filterName);
                });
            });
        }
        
        function setupTableSorting() {
            // Add sorting to table headers
            const tableHeaders = document.querySelectorAll('.data-table th');
            tableHeaders.forEach(header => {
                header.addEventListener('click', function(e) {
                    const column = this.dataset.col;
                    sortTable(column);
                });
            });
        }
        
        function navigateToTask(taskId) {
            console.log('Navigate to task:', taskId);
            // In a real implementation, this would update the dashboard view
            alert('Navigation to task ' + taskId + ' would happen here.');
        }
        
        function navigateToEntity(level, entityId) {
            console.log('Navigate to entity:', level, entityId);
            // In a real implementation, this would update the dashboard view
            alert('Navigation to ' + level + ' ' + entityId + ' would happen here.');
        }
        
        function applyFilter(key, value) {
            console.log('Apply filter:', key, value);
            // In a real implementation, this would update the dashboard view
            alert('Filtering by ' + key + '=' + value + ' would happen here.');
        }
        
        function clearFilter(key) {
            console.log('Clear filter:', key);
            // In a real implementation, this would update the dashboard view
            alert('Clearing filter ' + key + ' would happen here.');
        }
        
        function sortTable(column) {
            console.log('Sort by column:', column);
            // In a real implementation, this would update the table sorting
            alert('Sorting by ' + column + ' would happen here.');
        }
        </script>
        """
        
        # Insert the JavaScript before the closing </body> tag
        html_with_js = html_content.replace("</body>", f"{js_code}</body>")
        
        return html_with_js
    
    def _run_text_interactive_dashboard(self, dashboard_manager: DashboardManager) -> None:
        """
        Run the text-based interactive dashboard.
        
        Args:
            dashboard_manager: Dashboard manager instance
        """
        # Print welcome message and instructions
        print("Interactive Dashboard")
        print("====================")
        print("Commands:")
        print("  n <level> <id> - Navigate to entity")
        print("  b            - Navigate back")
        print("  f <key> <value> - Apply filter")
        print("  c <key>      - Clear filter")
        print("  ca           - Clear all filters")
        print("  q            - Quit")
        print("")
        
        # Main interaction loop
        while True:
            # Display the current dashboard
            output = dashboard_manager.render_dashboard("main_dashboard", "text")
            print("\n" + output)
            
            # Get user command
            try:
                cmd = input("> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting interactive dashboard.")
                break
            
            if not cmd:
                continue
            
            parts = cmd.split()
            command = parts[0].lower()
            
            if command == "q":
                break
            elif command == "n" and len(parts) >= 3:
                level = parts[1]
                entity_id = parts[2]
                dashboard_manager.navigate(level, entity_id)
            elif command == "b":
                success = dashboard_manager.navigate_back()
                if not success:
                    print("Already at root level.")
            elif command == "f" and len(parts) >= 3:
                key = parts[1]
                value = " ".join(parts[2:])
                dashboard_manager.apply_filter(key, value)
            elif command == "c" and len(parts) >= 2:
                key = parts[1]
                dashboard_manager.clear_filter(key)
            elif command == "ca":
                dashboard_manager.clear_all_filters()
            else:
                print("Unknown command. Type 'q' to quit.")


class TaskMetricsCommand:
    """
    Command for displaying task metrics and statistics.
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize the task metrics command.
        
        Args:
            core_manager: Core manager instance
        """
        self.core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        Args:
            parser: Argument parser to configure
        """
        parser.add_argument(
            "file_path",
            help="Path to the clickup JSON template file"
        )
        parser.add_argument(
            "--format",
            choices=["text", "json"],
            default="text",
            help="Output format (default: text)"
        )
        parser.add_argument(
            "--filter-status",
            help="Filter tasks by status"
        )
        parser.add_argument(
            "--filter-priority",
            type=int,
            help="Filter tasks by priority"
        )
        parser.add_argument(
            "--filter-tags",
            help="Filter tasks by tags (comma-separated)"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the task metrics command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code
        """
        # Initialize the dashboard manager
        dashboard_manager = DashboardManager(self.core_manager)
        
        # Apply filters if specified
        if args.filter_status:
            dashboard_manager.apply_filter("status", args.filter_status)
            
        if args.filter_priority is not None:
            dashboard_manager.apply_filter("priority", args.filter_priority)
            
        if args.filter_tags:
            tags = [tag.strip() for tag in args.filter_tags.split(",")]
            dashboard_manager.apply_filter("tags", tags)
        
        # Get metrics data
        data_provider = TaskDataProvider(self.core_manager)
        
        # Build context
        context = {
            'level': 'root',
            'entity_id': None,
            'metrics': ['task_count', 'completion_percentage', 'status_distribution', 'priority_distribution']
        }
        
        # Get data
        if dashboard_manager.state.active_filters:
            data = data_provider.get_filtered_data(context, dashboard_manager.state.active_filters)
        else:
            data = data_provider.get_data(context)
        
        # Output metrics
        if args.format == "json":
            metrics_data = {
                'task_count': data.get('task_count', 0),
                'completion_percentage': data.get('completion_percentage', 0),
                'status_distribution': data.get('status_distribution', {}),
                'priority_distribution': data.get('priority_distribution', {})
            }
            
            print(json.dumps(metrics_data, indent=2))
        else:
            print("Task Metrics")
            print("===========")
            print(f"Total Tasks: {data.get('task_count', 0)}")
            print(f"Completion Rate: {data.get('completion_percentage', 0):.1f}%")
            
            print("\nStatus Distribution:")
            status_data = data.get('status_distribution', {})
            for status, count in sorted(status_data.items(), key=lambda x: x[1], reverse=True):
                percent = (count / data.get('task_count', 1) * 100) if data.get('task_count', 0) > 0 else 0
                print(f"  {status}: {count} ({percent:.1f}%)")
            
            print("\nPriority Distribution:")
            priority_data = data.get('priority_distribution', {})
            for priority, count in sorted(priority_data.items()):
                percent = (count / data.get('task_count', 1) * 100) if data.get('task_count', 0) > 0 else 0
                print(f"  {priority}: {count} ({percent:.1f}%)")
        
        return 0


class CompletionTimelineCommand:
    """
    Command for visualizing task completion over time.
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize the completion timeline command.
        
        Args:
            core_manager: Core manager instance
        """
        self.core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        Args:
            parser: Argument parser to configure
        """
        parser.add_argument(
            "file_path",
            help="Path to the clickup JSON template file"
        )
        parser.add_argument(
            "--format",
            choices=["text", "json"],
            default="text",
            help="Output format (default: text)"
        )
        parser.add_argument(
            "--period",
            choices=["day", "week", "month"],
            default="day",
            help="Time period granularity (default: day)"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=30,
            help="Number of periods to show (default: 30)"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the completion timeline command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code
        """
        # Initialize the dashboard manager
        dashboard_manager = DashboardManager(self.core_manager)
        
        # Get data provider
        data_provider = TaskDataProvider(self.core_manager)
        
        # Build context
        context = {
            'level': 'root',
            'entity_id': None,
            'metrics': ['recent_activity', 'completion_timeline']
        }
        
        # Get data
        data = data_provider.get_data(context)
        
        # Generate timeline data based on the time period
        timeline_data = data.get('completion_timeline', [])
        
        # Limit the number of periods
        timeline_data = timeline_data[-args.limit:] if timeline_data else []
        
        # Output the timeline
        if args.format == "json":
            print(json.dumps(timeline_data, indent=2))
        else:
            print("Task Completion Timeline")
            print("=======================")
            
            if not timeline_data:
                print("No completion data available.")
                return 0
            
            # Find the maximum value for scaling
            max_value = max(item.get('value', 0) for item in timeline_data)
            max_bar_width = 40
            
            for item in timeline_data:
                date = item.get('date', 'Unknown')
                value = item.get('value', 0)
                label = item.get('label', '')
                
                # Calculate bar width
                bar_width = int((value / max_value) * max_bar_width) if max_value > 0 else 0
                bar = '█' * bar_width
                
                print(f"{date} | {bar} {value} {label}")
        
        return 0


class TaskHierarchyCommand:
    """
    Command for displaying task hierarchy visualization.
    """
    
    def __init__(self, core_manager: CoreManager):
        """
        Initialize the task hierarchy command.
        
        Args:
            core_manager: Core manager instance
        """
        self.core_manager = core_manager
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """
        Configure the argument parser for this command.
        
        Args:
            parser: Argument parser to configure
        """
        parser.add_argument(
            "file_path",
            help="Path to the clickup JSON template file"
        )
        parser.add_argument(
            "task_name",
            nargs="?",
            help="Optional task name to use as root (default: all tasks)"
        )
        parser.add_argument(
            "--format",
            choices=["text", "json"],
            default="text",
            help="Output format (default: text)"
        )
        parser.add_argument(
            "--max-depth",
            type=int,
            help="Maximum depth to display"
        )
        parser.add_argument(
            "--details",
            action="store_true",
            help="Show detailed information for each task"
        )
    
    def execute(self, args: Namespace) -> int:
        """
        Execute the task hierarchy command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code
        """
        # Initialize the dashboard manager
        dashboard_manager = DashboardManager(self.core_manager)
        
        # Set the navigation level
        if args.task_name:
            # Find the task by name
            task = self.core_manager.get_task_by_name(args.task_name)
            if not task:
                print(f"Task not found: {args.task_name}")
                return 1
            
            dashboard_manager.navigate("task", task.get("id"))
        else:
            dashboard_manager.navigate("root")
        
        # Update preferences
        if args.max_depth is not None:
            dashboard_manager.update_preference("hierarchy_max_depth", args.max_depth)
            
        if args.details:
            dashboard_manager.update_preference("hierarchy_show_details", True)
        
        # Get data provider
        data_provider = TaskDataProvider(self.core_manager)
        
        # Build context
        context = {
            'level': dashboard_manager.state.navigation_context.level,
            'entity_id': dashboard_manager.state.navigation_context.entity_id,
            'metrics': ['task_hierarchy']
        }
        
        # Get data
        data = data_provider.get_data(context)
        
        # Output the hierarchy
        if args.format == "json":
            hierarchy_data = data.get('task_hierarchy', {})
            print(json.dumps(hierarchy_data, indent=2))
        else:
            # Use the task hierarchy component for rendering
            from ...dashboard.components import TaskHierarchyComponent
            
            hierarchy_component = TaskHierarchyComponent(
                component_id="task_hierarchy",
                title="Task Hierarchy",
                data_key="task_hierarchy",
                max_depth=args.max_depth,
                show_details=args.details
            )
            
            output = hierarchy_component.render(data, "text")
            print(output)
        
        return 0 