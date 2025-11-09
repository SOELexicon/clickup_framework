"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/dashboard/dashboard_manager.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CLI Dashboard Commands: Entry point for terminal-based dashboard rendering
    - WebServer: Provides dashboard data for web interfaces
    - TaskService: Integrates dashboard capabilities with task operations
    - CoreManager: Initializes dashboards as part of system startup
    - InteractiveDashboard: Primary consumer for interactive CLI experience

Purpose:
    Provides the main orchestration layer for the dashboard system. Manages the
    component lifecycle, coordinates data providers with visualization components,
    handles state transitions, and renders comprehensive dashboards. Acts as the
    facade to the dashboard subsystem for other application components.

Requirements:
    - CRITICAL: Must handle all component dependencies correctly during rendering
    - CRITICAL: Must render components in the correct order based on dependencies
    - CRITICAL: Must support multiple output formats (text, HTML, JSON)
    - Must handle all error conditions gracefully with fallback rendering
    - Must support custom component registration for extensibility
    - Must implement navigation and filtering without modifying underlying data

Dashboard Manager Module

This module provides the Dashboard Manager for coordinating components and rendering.
"""
from typing import Dict, List, Any, Optional, Set, Tuple
import re

from .dashboard_component import Component, DataProvider, DashboardState
from .components import (
    MetricComponent, 
    BarChartComponent, 
    TableComponent, 
    PieChartComponent,
    TimelineComponent,
    TaskHierarchyComponent,
    DashboardLayout
)
from ..core.interfaces.core_manager import CoreManager


class DashboardManager:
    """
    Manager for dashboard components and rendering.
    
    This class coordinates the dashboard components, data providers, and state.
    """
    
    def __init__(self, core_manager: CoreManager, data_provider: Optional[DataProvider] = None):
        """
        Initialize the dashboard manager.
        
        Args:
            core_manager: The core manager instance to use for data access
            data_provider: Optional data provider instance to use
        """
        self.core_manager = core_manager
        
        # Set up data provider
        from .data_provider import TaskDataProvider
        self.data_provider = data_provider or TaskDataProvider(core_manager)
        
        # Set up dashboard state
        self.state = DashboardState()
        
        # Initialize component registry
        self.components: Dict[str, Component] = {}
        
        # Create and register default components
        self._register_default_components()
    
    def _register_default_components(self) -> None:
        """
        Create and register the default dashboard components.
        """
        # Task summary metrics
        self.register_component(MetricComponent(
            component_id="task_count_metric",
            title="Total Tasks",
            metric_key="task_count",
            format_str="{}"
        ))
        
        self.register_component(MetricComponent(
            component_id="completion_metric",
            title="Completion Rate",
            metric_key="completion_percentage",
            format_str="{:.1f}%",
            description="Percentage of tasks marked as complete"
        ))
        
        # Status and priority charts
        self.register_component(BarChartComponent(
            component_id="status_chart",
            title="Tasks by Status",
            data_key="status_distribution",
            max_width=40,
            show_values=True
        ))
        
        self.register_component(BarChartComponent(
            component_id="priority_chart",
            title="Tasks by Priority",
            data_key="priority_distribution",
            max_width=40,
            show_values=True
        ))
        
        # Pie charts
        self.register_component(PieChartComponent(
            component_id="status_pie",
            title="Status Distribution",
            data_key="status_distribution",
            show_percentages=True,
            show_legend=True
        ))
        
        # Timeline for recent activity
        self.register_component(TimelineComponent(
            component_id="activity_timeline",
            title="Recent Activity",
            data_key="recent_activity",
            time_format="%Y-%m-%d",
            interval_type="day"
        ))
        
        # Task hierarchy view
        self.register_component(TaskHierarchyComponent(
            component_id="task_hierarchy",
            title="Task Hierarchy",
            data_key="task_hierarchy",
            max_depth=None,
            show_details=True
        ))
        
        # Task table view
        self.register_component(TableComponent(
            component_id="task_table",
            title="Task List",
            columns=["name", "status", "type", "priority", "tags", "parent_name"],
            column_labels={
                "name": "Task Name",
                "status": "Status",
                "type": "Type",
                "priority": "Priority",
                "tags": "Tags",
                "parent_name": "Parent Task"
            },
            max_rows=20
        ))
        
        # Default dashboard layouts
        self.register_component(DashboardLayout(
            component_id="summary_dashboard",
            title="Task Summary Dashboard",
            components=[
                self.components["task_count_metric"],
                self.components["completion_metric"],
                self.components["status_chart"],
                self.components["priority_chart"],
                self.components["activity_timeline"]
            ]
        ))
        
        self.register_component(DashboardLayout(
            component_id="detail_dashboard",
            title="Task Detail Dashboard",
            components=[
                self.components["task_hierarchy"],
                self.components["task_table"]
            ]
        ))
        
        # Main dashboard layout
        self.register_component(DashboardLayout(
            component_id="main_dashboard",
            title="ClickUp Task Dashboard",
            components=[
                self.components["summary_dashboard"],
                self.components["detail_dashboard"]
            ]
        ))
    
    def register_component(self, component: Component) -> None:
        """
        Register a component with the dashboard manager.
        
        Args:
            component: Component instance to register
        """
        self.components[component.component_id] = component
    
    def get_component(self, component_id: str) -> Optional[Component]:
        """
        Get a component by its ID.
        
        Args:
            component_id: ID of the component to get
            
        Returns:
            Component instance or None if not found
        """
        return self.components.get(component_id)
    
    def render_dashboard(self, dashboard_id: Optional[str] = None, format_type: str = 'text') -> str:
        """
        Render the dashboard with the current state.
        
        Args:
            dashboard_id: Optional ID of the dashboard layout to render (defaults to main_dashboard)
            format_type: Output format type (text, html, json)
            
        Returns:
            Rendered dashboard as a string
        """
        # Get the dashboard layout component to render
        dashboard_id = dashboard_id or "main_dashboard"
        dashboard = self.get_component(dashboard_id)
        
        if not dashboard:
            if dashboard_id == "main_dashboard" and len(self.components) > 0:
                # If main_dashboard not found but we have components, find a layout component
                for component_id, component in self.components.items():
                    if component.component_type == "layout":
                        dashboard = component
                        break
            
            if not dashboard:
                return f"Dashboard '{dashboard_id}' not found."
        
        # Get data based on current navigation context
        context = {
            'level': self.state.navigation_context.level,
            'entity_id': self.state.navigation_context.entity_id,
            'metrics': self._get_required_metrics(dashboard),
            'filters': self.state.active_filters
        }
        
        # Apply filters if present
        if self.state.active_filters:
            data = self.data_provider.get_filtered_data(context, self.state.active_filters)
        else:
            data = self.data_provider.get_data(context)
        
        # Add navigation breadcrumbs to the data
        breadcrumbs = self.state.navigation_context.get_breadcrumb_trail()
        data['breadcrumbs'] = breadcrumbs
        
        # Add filter information to the data
        data['filters'] = self.state.active_filters
        
        # Add state information
        data['selected_entity'] = self.state.selected_entity
        data['view_preferences'] = self.state.view_preferences
        
        # Render the dashboard
        result = dashboard.render(data, format_type)
        
        # Add navigation header for text format
        if format_type == 'text':
            header = "ClickUp Task Dashboard\n"
            header += "=====================\n\n"
            
            # Add breadcrumb trail
            breadcrumb_text = " > ".join([f"{b['level'].capitalize()}: {self._get_entity_name(b['level'], b['entity_id'])}" 
                                         for b in breadcrumbs])
            header += f"Location: {breadcrumb_text}\n\n"
            
            # Add filter information if present
            if self.state.active_filters:
                header += "Active Filters:\n"
                for key, value in self.state.active_filters.items():
                    header += f"  {key}: {value}\n"
                header += "\n"
            
            result = header + result
        
        # Add navigation header for HTML format
        elif format_type == 'html':
            breadcrumb_html = ""
            for i, breadcrumb in enumerate(breadcrumbs):
                level = breadcrumb['level']
                entity_id = breadcrumb['entity_id']
                name = self._get_entity_name(level, entity_id)
                
                if i > 0:
                    breadcrumb_html += '<span class="breadcrumb-separator">&gt;</span>'
                
                breadcrumb_html += f'<span class="breadcrumb-item">{level.capitalize()}: {name}</span>'
            
            filter_html = ""
            if self.state.active_filters:
                filter_html = "<div class='active-filters'><h3>Active Filters</h3><ul>"
                for key, value in self.state.active_filters.items():
                    filter_html += f"<li><strong>{key}:</strong> {value}</li>"
                filter_html += "</ul></div>"
            
            header_html = f"""
            <div class="dashboard-header">
                <h1>ClickUp Task Dashboard</h1>
                <div class="breadcrumb-trail">{breadcrumb_html}</div>
                {filter_html}
            </div>
            """
            
            # Add CSS styles for dashboard components
            styles = self._get_dashboard_styles()
            
            # Wrap the result with HTML structure
            result = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>ClickUp Task Dashboard</title>
                <style>
                {styles}
                </style>
            </head>
            <body>
                {header_html}
                <div class="dashboard-container">
                    {result}
                </div>
            </body>
            </html>
            """
        
        return result
    
    def navigate(self, level: str, entity_id: Optional[str] = None) -> None:
        """
        Navigate to a specific entity.
        
        Args:
            level: Level to navigate to
            entity_id: ID of the entity to navigate to
        """
        self.state.navigate_to(level, entity_id)
        
        # Clear cache for the new navigation context
        if hasattr(self.data_provider, 'clear_cache'):
            self.data_provider.clear_cache()
    
    def navigate_back(self) -> bool:
        """
        Navigate back to the parent context.
        
        Returns:
            True if navigation was successful, False otherwise
        """
        return self.state.navigate_back()
    
    def apply_filter(self, key: str, value: Any) -> None:
        """
        Apply a filter to the dashboard.
        
        Args:
            key: Filter key
            value: Filter value
        """
        self.state.set_filter(key, value)
    
    def clear_filter(self, key: str) -> None:
        """
        Clear a specific filter.
        
        Args:
            key: Filter key to clear
        """
        self.state.clear_filter(key)
    
    def clear_all_filters(self) -> None:
        """
        Clear all active filters.
        """
        self.state.clear_all_filters()
    
    def update_preference(self, key: str, value: Any) -> None:
        """
        Update a view preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        self.state.update_preference(key, value)
    
    def _get_required_metrics(self, dashboard: Component) -> List[str]:
        """
        Get the list of metrics required by the dashboard and its components.
        
        Args:
            dashboard: Dashboard component to check
            
        Returns:
            List of required metric keys
        """
        required_metrics = set()
        
        def collect_metrics(component: Component) -> None:
            """Recursively collect metrics from a component and its dependencies."""
            # Check if component is a metric component
            if component.component_type == "metric":
                if hasattr(component, 'metric_key'):
                    required_metrics.add(component.metric_key)
            
            # Check if component is a chart component
            elif component.component_type in ["bar_chart", "pie_chart", "timeline"]:
                if hasattr(component, 'data_key'):
                    required_metrics.add(component.data_key)
            
            # Check if component is a hierarchy component
            elif component.component_type == "task_hierarchy":
                if hasattr(component, 'data_key'):
                    required_metrics.add(component.data_key)
            
            # Check if component is a layout
            elif component.component_type == "layout":
                if hasattr(component, 'components'):
                    for child in component.components:
                        collect_metrics(child)
            
            # Check component dependencies
            dependencies = component.get_dependencies()
            for dep_id in dependencies:
                dep_component = self.get_component(dep_id)
                if dep_component:
                    collect_metrics(dep_component)
        
        # Start collection from the dashboard
        collect_metrics(dashboard)
        
        return list(required_metrics)
    
    def _get_entity_name(self, level: str, entity_id: Optional[str]) -> str:
        """
        Get the name of an entity based on its level and ID.
        
        Args:
            level: Entity level
            entity_id: Entity ID
            
        Returns:
            Entity name or default name if not found
        """
        if not entity_id:
            if level == 'root':
                return 'All Tasks'
            return 'Unknown'
        
        if level == 'root':
            return 'All Tasks'
        
        elif level == 'space':
            space = self.core_manager.get_space(entity_id)
            return space.get('name', 'Unknown Space') if space else 'Unknown Space'
        
        elif level == 'folder':
            folder = self.core_manager.get_folder(entity_id)
            return folder.get('name', 'Unknown Folder') if folder else 'Unknown Folder'
        
        elif level == 'list':
            task_list = self.core_manager.get_list(entity_id)
            return task_list.get('name', 'Unknown List') if task_list else 'Unknown List'
        
        elif level == 'task':
            task = self.core_manager.get_task(entity_id)
            return task.get('name', 'Unknown Task') if task else 'Unknown Task'
        
        return 'Unknown'
    
    def _get_dashboard_styles(self) -> str:
        """
        Get CSS styles for the dashboard components.
        
        Returns:
            CSS styles as a string
        """
        return """
        :root {
            --color-0: #4285f4;
            --color-1: #ea4335;
            --color-2: #fbbc05;
            --color-3: #34a853;
            --color-4: #673ab7;
            --color-5: #3f51b5;
            --color-6: #2196f3;
            --color-7: #009688;
            --color-8: #ff5722;
            --color-9: #795548;
            --primary-color: #4285f4;
            --secondary-color: #34a853;
            --background-color: #ffffff;
            --text-color: #202124;
            --border-color: #dadce0;
            --hover-color: #f8f9fa;
        }
        
        body {
            font-family: 'Roboto', Arial, sans-serif;
            line-height: 1.5;
            color: var(--text-color);
            background-color: var(--background-color);
            margin: 0;
            padding: 20px;
        }
        
        .dashboard-header {
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
        }
        
        .dashboard-header h1 {
            margin-top: 0;
            color: var(--primary-color);
        }
        
        .breadcrumb-trail {
            margin-bottom: 10px;
            font-size: 14px;
        }
        
        .breadcrumb-item {
            color: var(--secondary-color);
        }
        
        .breadcrumb-separator {
            margin: 0 8px;
            color: var(--border-color);
        }
        
        .active-filters {
            background-color: var(--hover-color);
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        
        .active-filters h3 {
            margin-top: 0;
            font-size: 16px;
        }
        
        .active-filters ul {
            margin: 0;
            padding-left: 20px;
        }
        
        .dashboard-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .dashboard-layout {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        
        .dashboard-title {
            background-color: var(--primary-color);
            color: white;
            margin: 0;
            padding: 15px;
            font-size: 18px;
        }
        
        .dashboard-components {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px;
        }
        
        .metric-component {
            background-color: white;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }
        
        .metric-title {
            margin-top: 0;
            font-size: 16px;
            color: var(--text-color);
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: var(--primary-color);
            margin: 10px 0;
        }
        
        .metric-description {
            font-size: 12px;
            color: #5f6368;
        }
        
        .chart-component {
            background-color: white;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }
        
        .chart-title {
            margin-top: 0;
            font-size: 16px;
            color: var(--text-color);
        }
        
        .bar-chart-container {
            margin-top: 15px;
        }
        
        .bar-row {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .bar-label {
            width: 100px;
            text-align: right;
            padding-right: 10px;
            font-size: 14px;
        }
        
        .bar-container {
            flex-grow: 1;
            height: 20px;
            background-color: var(--hover-color);
            border-radius: 4px;
            overflow: hidden;
        }
        
        .bar {
            height: 100%;
            background-color: var(--primary-color);
            border-radius: 4px;
        }
        
        .bar-value {
            width: 40px;
            text-align: right;
            padding-left: 10px;
            font-size: 14px;
        }
        
        .pie-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-top: 15px;
        }
        
        .pie {
            position: relative;
            width: 200px;
            height: 200px;
            border-radius: 50%;
            overflow: hidden;
            margin-bottom: 20px;
        }
        
        .pie-legend {
            width: 100%;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 2px;
            margin-right: 8px;
        }
        
        .legend-label {
            flex-grow: 1;
            font-size: 14px;
        }
        
        .legend-value {
            margin-left: 8px;
            font-size: 14px;
            font-weight: bold;
        }
        
        .legend-percent {
            margin-left: 8px;
            font-size: 12px;
            color: #5f6368;
        }
        
        .timeline-container {
            display: flex;
            align-items: flex-end;
            height: 200px;
            margin-top: 15px;
            padding-bottom: 30px;
        }
        
        .timeline-point {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
        }
        
        .timeline-bar {
            width: 20px;
            background-color: var(--primary-color);
            border-radius: 4px 4px 0 0;
            margin-bottom: 8px;
        }
        
        .timeline-date {
            position: absolute;
            bottom: -25px;
            font-size: 10px;
            transform: rotate(-45deg);
            transform-origin: left;
            white-space: nowrap;
        }
        
        .timeline-value {
            font-size: 10px;
            position: absolute;
            bottom: -10px;
        }
        
        .table-component {
            grid-column: 1 / -1;
            background-color: white;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            overflow-x: auto;
        }
        
        .table-title {
            margin-top: 0;
            font-size: 16px;
            color: var(--text-color);
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .data-table th {
            background-color: var(--hover-color);
            text-align: left;
            padding: 8px 12px;
            font-weight: 500;
            border-bottom: 2px solid var(--border-color);
        }
        
        .data-table td {
            padding: 8px 12px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .data-table tr:hover {
            background-color: var(--hover-color);
        }
        
        .table-pagination {
            margin-top: 10px;
            text-align: right;
            font-size: 12px;
            color: #5f6368;
        }
        
        .hierarchy-component {
            grid-column: 1 / -1;
            background-color: white;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }
        
        .hierarchy-title {
            margin-top: 0;
            font-size: 16px;
            color: var(--text-color);
        }
        
        .task-hierarchy {
            margin-top: 15px;
        }
        
        .task-root {
            list-style-type: none;
            padding-left: 0;
        }
        
        .task-item {
            margin-bottom: 5px;
        }
        
        .task-children {
            list-style-type: none;
            padding-left: 20px;
        }
        
        .task-name {
            font-weight: 500;
        }
        
        .task-details {
            font-size: 12px;
            color: #5f6368;
            margin-left: 8px;
        }
        
        .task-status {
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 10px;
            text-transform: uppercase;
        }
        
        .task-status.complete {
            background-color: var(--secondary-color);
            color: white;
        }
        
        .task-status.in.progress, .task-status.in_progress {
            background-color: var(--primary-color);
            color: white;
        }
        
        .task-status.to.do, .task-status.to_do {
            background-color: var(--hover-color);
            color: var(--text-color);
        }
        
        .task-id {
            font-family: monospace;
            margin-left: 5px;
        }
        
        /* Media queries for responsive layout */
        @media (max-width: 768px) {
            .dashboard-components {
                grid-template-columns: 1fr;
            }
            
            .bar-label {
                width: 80px;
            }
            
            .pie {
                width: 150px;
                height: 150px;
            }
            
            .timeline-container {
                height: 150px;
            }
        }
        """ 