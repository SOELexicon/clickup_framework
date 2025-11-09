"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/dashboard/components.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - DashboardManager: Creates and manages dashboard component instances
    - InteractiveDashboard: Renders components for user interaction
    - RESTfulAPI: Serializes component outputs for API responses
    - CLI Dashboard Command: Renders components to terminal
    - WebServer: Renders components to HTML format
    - Dashboard Plugins: Extend with custom component implementations

Purpose:
    Implements concrete visualizations for the dashboard system, providing a
    comprehensive set of components for displaying task data in various formats.
    Each component is specialized to render a specific type of visualization (metrics,
    charts, tables, etc.) while maintaining a consistent interface for the dashboard
    manager.

Requirements:
    - CRITICAL: All components must support multiple output formats (text, HTML, JSON)
    - CRITICAL: Components must handle missing or invalid data gracefully
    - CRITICAL: Time-intensive rendering operations must implement optimizations
    - Components must use consistent styling and formatting conventions
    - Components must implement proper dependency declarations
    - Complex visualizations must degrade gracefully in terminal environments
    - Visual components must honor accessibility guidelines

Dashboard Components Module

This module provides concrete implementations of dashboard components.
"""
from typing import Dict, List, Any, Optional, Set, Tuple
import datetime
import html

from .dashboard_component import Component


class MetricComponent(Component):
    """
    A component that displays a single metric value.
    """
    
    def __init__(
        self, 
        component_id: str, 
        title: str, 
        metric_key: str, 
        format_str: str = "{}", 
        description: Optional[str] = None
    ):
        """
        Initialize a new metric component.
        
        Args:
            component_id: Unique identifier for the component
            title: Title to display for the component
            metric_key: Key to extract the metric value from the data
            format_str: Format string to apply to the value
            description: Optional description of the metric
        """
        super().__init__(component_id, "metric")
        self.title = title
        self.metric_key = metric_key
        self.format_str = format_str
        self.description = description
    
    def render(self, data: Dict[str, Any], format_type: str = 'text') -> str:
        """
        Render the metric component.
        
        Args:
            data: Data dictionary containing the metric value
            format_type: Output format (text, html, json)
            
        Returns:
            Rendered component as a string
        """
        # Extract value with fallback
        value = data.get(self.metric_key, 0)
        
        # Format the value using the format string
        formatted_value = self.format_str.format(value)
        
        if format_type == 'text':
            output = f"{self.title}: {formatted_value}\n"
            if self.description:
                output += f"  {self.description}\n"
            return output
        
        elif format_type == 'html':
            description_html = f'<div class="metric-description">{html.escape(self.description)}</div>' if self.description else ''
            return f"""
            <div class="metric-component" id="{html.escape(self.component_id)}">
                <h3 class="metric-title">{html.escape(self.title)}</h3>
                <div class="metric-value">{html.escape(formatted_value)}</div>
                {description_html}
            </div>
            """
        
        elif format_type == 'json':
            return {
                'component_id': self.component_id,
                'component_type': self.component_type,
                'title': self.title,
                'value': value,
                'formatted_value': formatted_value,
                'description': self.description
            }
        
        return ""


class BarChartComponent(Component):
    """
    A component that displays data as a horizontal bar chart.
    """
    
    def __init__(
        self, 
        component_id: str, 
        title: str, 
        data_key: str, 
        max_width: int = 50, 
        show_values: bool = True,
        label_width: int = 15,
        sort_by: Optional[str] = None,
        limit: Optional[int] = None
    ):
        """
        Initialize a new bar chart component.
        
        Args:
            component_id: Unique identifier for the component
            title: Title to display for the component
            data_key: Key to extract the data from the data dictionary
            max_width: Maximum width of bars in characters (for text output)
            show_values: Whether to show numerical values
            label_width: Width of labels in characters (for text output)
            sort_by: Optional sorting key ('key', 'value', 'value_desc')
            limit: Optional limit on number of items to display
        """
        super().__init__(component_id, "bar_chart")
        self.title = title
        self.data_key = data_key
        self.max_width = max_width
        self.show_values = show_values
        self.label_width = label_width
        self.sort_by = sort_by
        self.limit = limit
    
    def render(self, data: Dict[str, Any], format_type: str = 'text') -> str:
        """
        Render the bar chart component.
        
        Args:
            data: Data dictionary containing the chart data
            format_type: Output format (text, html, json)
            
        Returns:
            Rendered component as a string
        """
        # Extract data with fallback
        chart_data = data.get(self.data_key, {})
        
        if not chart_data:
            return f"{self.title}: No data available\n"
        
        # Sort data if requested
        items = list(chart_data.items())
        if self.sort_by == 'key':
            items.sort(key=lambda x: x[0])
        elif self.sort_by == 'value':
            items.sort(key=lambda x: x[1])
        elif self.sort_by == 'value_desc':
            items.sort(key=lambda x: x[1], reverse=True)
        
        # Limit items if requested
        if self.limit and len(items) > self.limit:
            items = items[:self.limit]
        
        # Get maximum value for scaling
        max_value = max(x[1] for x in items) if items else 0
        
        if format_type == 'text':
            output = f"{self.title}:\n"
            
            # Calculate scale factor
            scale = self.max_width / max_value if max_value > 0 else 0
            
            for label, value in items:
                # Format the label with fixed width
                label_str = str(label)
                if len(label_str) > self.label_width:
                    label_str = label_str[:self.label_width - 3] + "..."
                else:
                    label_str = label_str.ljust(self.label_width)
                
                # Calculate bar width
                bar_width = int(value * scale) if value > 0 else 0
                bar = '█' * bar_width
                
                # Add value if requested
                value_str = f" {value}" if self.show_values else ""
                
                output += f"  {label_str} │ {bar}{value_str}\n"
            
            return output
        
        elif format_type == 'html':
            rows_html = ""
            
            for label, value in items:
                # Calculate percentage for CSS width
                percentage = (value / max_value * 100) if max_value > 0 else 0
                value_html = f'<div class="bar-value">{value}</div>' if self.show_values else ''
                
                rows_html += f"""
                <div class="bar-row">
                    <div class="bar-label">{html.escape(str(label))}</div>
                    <div class="bar-container">
                        <div class="bar" style="width: {percentage}%;"></div>
                    </div>
                    {value_html}
                </div>
                """
            
            return f"""
            <div class="chart-component" id="{html.escape(self.component_id)}">
                <h3 class="chart-title">{html.escape(self.title)}</h3>
                <div class="bar-chart-container">
                    {rows_html}
                </div>
            </div>
            """
        
        elif format_type == 'json':
            return {
                'component_id': self.component_id,
                'component_type': self.component_type,
                'title': self.title,
                'data': [{'label': k, 'value': v} for k, v in items]
            }
        
        return ""


class PieChartComponent(Component):
    """
    A component that displays data as a pie chart.
    """
    
    def __init__(
        self, 
        component_id: str, 
        title: str, 
        data_key: str, 
        show_percentages: bool = True,
        show_legend: bool = True,
        limit: Optional[int] = None
    ):
        """
        Initialize a new pie chart component.
        
        Args:
            component_id: Unique identifier for the component
            title: Title to display for the component
            data_key: Key to extract the data from the data dictionary
            show_percentages: Whether to show percentage values
            show_legend: Whether to show a legend
            limit: Optional limit on number of items to display
        """
        super().__init__(component_id, "pie_chart")
        self.title = title
        self.data_key = data_key
        self.show_percentages = show_percentages
        self.show_legend = show_legend
        self.limit = limit
    
    def render(self, data: Dict[str, Any], format_type: str = 'text') -> str:
        """
        Render the pie chart component.
        
        Args:
            data: Data dictionary containing the chart data
            format_type: Output format (text, html, json)
            
        Returns:
            Rendered component as a string
        """
        # Extract data with fallback
        chart_data = data.get(self.data_key, {})
        
        if not chart_data:
            return f"{self.title}: No data available\n"
        
        # Sort data by value in descending order
        items = sorted(chart_data.items(), key=lambda x: x[1], reverse=True)
        
        # Limit items if requested
        if self.limit and len(items) > self.limit:
            # Combine remaining items into "Other"
            other_sum = sum(x[1] for x in items[self.limit:])
            items = items[:self.limit]
            if other_sum > 0:
                items.append(("Other", other_sum))
        
        # Calculate total and percentages
        total = sum(x[1] for x in items)
        
        if format_type == 'text':
            output = f"{self.title}:\n"
            
            # Display as a simple percentage breakdown for text format
            for label, value in items:
                percentage = (value / total * 100) if total > 0 else 0
                percentage_str = f" ({percentage:.1f}%)" if self.show_percentages else ""
                output += f"  {label}: {value}{percentage_str}\n"
            
            return output
        
        elif format_type == 'html':
            # Generate CSS for pie chart slices
            slices_css = ""
            slices_html = ""
            legend_html = ""
            cumulative = 0
            
            colors = [
                "#4285f4", "#ea4335", "#fbbc05", "#34a853", "#673ab7",
                "#3f51b5", "#2196f3", "#009688", "#ff5722", "#795548"
            ]
            
            for i, (label, value) in enumerate(items):
                percentage = (value / total * 100) if total > 0 else 0
                
                # Calculate slice angles
                start_angle = cumulative / total * 360
                end_angle = (cumulative + value) / total * 360
                cumulative += value
                
                # Get color from predefined list
                color = colors[i % len(colors)]
                color_var = f"var(--color-{i % 10})"
                
                # Create CSS for this slice
                if i == 0:
                    # First slice starts at 0 degrees
                    slices_css += f"""
                    .pie .slice-{i} {{
                        clip-path: polygon(50% 50%, 50% 0%, 100% 0%, 100% 100%, 0% 100%, 0% 0%, 50% 0%);
                        clip-path: polygon(50% 50%, 50% 0%, 
                                         {50 + 50 * round(end_angle) / 360}% {50 - 50 * round(end_angle) / 360}%);
                        background-color: {color_var};
                        width: 100%;
                        height: 100%;
                        position: absolute;
                    }}
                    """
                else:
                    # Rotate other slices appropriately
                    slices_css += f"""
                    .pie .slice-{i} {{
                        clip-path: polygon(50% 50%, 50% 0%, 100% 0%, 100% 100%, 0% 100%, 0% 0%, 50% 0%);
                        clip-path: polygon(50% 50%, 50% 0%, 
                                         {50 + 50 * round(end_angle) / 360}% {50 - 50 * round(end_angle) / 360}%);
                        background-color: {color_var};
                        width: 100%;
                        height: 100%;
                        position: absolute;
                        transform: rotate({start_angle}deg);
                        transform-origin: center;
                    }}
                    """
                
                # Add slice to HTML
                slices_html += f'<div class="slice-{i}"></div>'
                
                # Add to legend if requested
                if self.show_legend:
                    percentage_html = f'<span class="legend-percent">({percentage:.1f}%)</span>' if self.show_percentages else ''
                    legend_html += f"""
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: {color_var};"></div>
                        <span class="legend-label">{html.escape(str(label))}</span>
                        <span class="legend-value">{value}</span>
                        {percentage_html}
                    </div>
                    """
            
            legend_container = f"""
            <div class="pie-legend">
                {legend_html}
            </div>
            """ if self.show_legend else ""
            
            return f"""
            <style>
            {slices_css}
            </style>
            <div class="chart-component" id="{html.escape(self.component_id)}">
                <h3 class="chart-title">{html.escape(self.title)}</h3>
                <div class="pie-container">
                    <div class="pie">
                        {slices_html}
                    </div>
                    {legend_container}
                </div>
            </div>
            """
        
        elif format_type == 'json':
            return {
                'component_id': self.component_id,
                'component_type': self.component_type,
                'title': self.title,
                'data': [{'label': k, 'value': v, 'percentage': (v / total * 100) if total > 0 else 0} for k, v in items]
            }
        
        return ""


class TableComponent(Component):
    """
    A component that displays data as a table.
    """
    
    def __init__(
        self,
        component_id: str,
        title: str,
        columns: List[str],
        column_labels: Optional[Dict[str, str]] = None,
        max_rows: Optional[int] = None,
        sortable: bool = True,
        data_key: str = "tasks"
    ):
        """
        Initialize a new table component.
        
        Args:
            component_id: Unique identifier for the component
            title: Title to display for the component
            columns: List of column keys to display
            column_labels: Optional mapping of column keys to display labels
            max_rows: Optional maximum number of rows to display
            sortable: Whether the table is sortable
            data_key: Key to extract the data from the data dictionary
        """
        super().__init__(component_id, "table")
        self.title = title
        self.columns = columns
        self.column_labels = column_labels or {col: col.replace('_', ' ').title() for col in columns}
        self.max_rows = max_rows
        self.sortable = sortable
        self.data_key = data_key
    
    def render(self, data: Dict[str, Any], format_type: str = 'text') -> str:
        """
        Render the table component.
        
        Args:
            data: Data dictionary containing the table data
            format_type: Output format (text, html, json)
            
        Returns:
            Rendered component as a string
        """
        # Extract data with fallback
        table_data = data.get(self.data_key, [])
        
        if not table_data:
            return f"{self.title}: No data available\n"
        
        # Limit rows if requested
        if self.max_rows and len(table_data) > self.max_rows:
            table_data = table_data[:self.max_rows]
        
        # Get preferences from view_preferences if available
        preferences = data.get('view_preferences', {})
        sort_column = preferences.get('table_sort_column', self.columns[0] if self.columns else None)
        sort_direction = preferences.get('table_sort_direction', 'asc')
        
        # Sort data if requested and possible
        if self.sortable and sort_column:
            reverse = sort_direction.lower() == 'desc'
            table_data.sort(key=lambda x: x.get(sort_column, ''), reverse=reverse)
        
        if format_type == 'text':
            # Calculate column widths
            widths = {}
            for col in self.columns:
                label = self.column_labels.get(col, col)
                # Start with label width
                widths[col] = max(len(label), 5)
                
                # Check all data values
                for row in table_data:
                    value = row.get(col, '')
                    if isinstance(value, list):
                        value = ', '.join(str(v) for v in value)
                    else:
                        value = str(value)
                    widths[col] = max(widths[col], min(len(value), 30))  # Cap at 30 chars
            
            # Generate header
            header = "  ".join(self.column_labels.get(col, col).ljust(widths[col]) for col in self.columns)
            separator = "  ".join("-" * widths[col] for col in self.columns)
            
            rows = [header, separator]
            
            # Generate rows
            for row in table_data:
                row_values = []
                for col in self.columns:
                    value = row.get(col, '')
                    if isinstance(value, list):
                        value = ', '.join(str(v) for v in value)
                    else:
                        value = str(value)
                    
                    # Truncate if too long
                    if len(value) > widths[col]:
                        value = value[:widths[col] - 3] + "..."
                    
                    row_values.append(value.ljust(widths[col]))
                
                rows.append("  ".join(row_values))
            
            output = f"{self.title}:\n"
            output += "\n".join(rows) + "\n"
            
            # Add pagination info if limited
            if self.max_rows and len(table_data) == self.max_rows:
                output += f"\nShowing {len(table_data)} of {len(table_data)}+ rows\n"
            
            return output
        
        elif format_type == 'html':
            headers_html = ""
            for col in self.columns:
                label = self.column_labels.get(col, col)
                sort_class = ""
                if self.sortable and col == sort_column:
                    sort_class = f"sorted {sort_direction}"
                
                headers_html += f'<th class="{sort_class}" data-col="{html.escape(col)}">{html.escape(label)}</th>'
            
            rows_html = ""
            for row in table_data:
                cells_html = ""
                for col in self.columns:
                    value = row.get(col, '')
                    
                    # Handle special formatting
                    if col == 'status':
                        status_class = str(value).lower().replace(' ', '_')
                        cells_html += f'<td><span class="task-status {status_class}">{html.escape(str(value))}</span></td>'
                    elif col == 'tags' and isinstance(value, list):
                        tags_html = ' '.join([f'<span class="tag">{html.escape(tag)}</span>' for tag in value])
                        cells_html += f'<td>{tags_html}</td>'
                    elif isinstance(value, list):
                        cells_html += f'<td>{html.escape(", ".join(str(v) for v in value))}</td>'
                    else:
                        cells_html += f'<td>{html.escape(str(value))}</td>'
                
                rows_html += f'<tr>{cells_html}</tr>'
            
            pagination_html = ""
            if self.max_rows and len(table_data) == self.max_rows:
                pagination_html = f'<div class="table-pagination">Showing {len(table_data)} of {len(table_data)}+ rows</div>'
            
            return f"""
            <div class="table-component" id="{html.escape(self.component_id)}">
                <h3 class="table-title">{html.escape(self.title)}</h3>
                <table class="data-table">
                    <thead>
                        <tr>{headers_html}</tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
                {pagination_html}
            </div>
            """
        
        elif format_type == 'json':
            return {
                'component_id': self.component_id,
                'component_type': self.component_type,
                'title': self.title,
                'columns': self.columns,
                'column_labels': self.column_labels,
                'data': table_data
            }
        
        return ""


class TimelineComponent(Component):
    """
    A component that displays timeline data.
    """
    
    def __init__(
        self,
        component_id: str,
        title: str,
        data_key: str,
        time_format: str = "%Y-%m-%d",
        interval_type: str = "day",
        limit: Optional[int] = None
    ):
        """
        Initialize a new timeline component.
        
        Args:
            component_id: Unique identifier for the component
            title: Title to display for the component
            data_key: Key to extract the data from the data dictionary
            time_format: Format string for time display
            interval_type: Interval type (day, week, month)
            limit: Optional maximum number of points to display
        """
        super().__init__(component_id, "timeline")
        self.title = title
        self.data_key = data_key
        self.time_format = time_format
        self.interval_type = interval_type
        self.limit = limit
    
    def render(self, data: Dict[str, Any], format_type: str = 'text') -> str:
        """
        Render the timeline component.
        
        Args:
            data: Data dictionary containing the timeline data
            format_type: Output format (text, html, json)
            
        Returns:
            Rendered component as a string
        """
        # Extract data with fallback
        timeline_data = data.get(self.data_key, [])
        
        if not timeline_data:
            return f"{self.title}: No data available\n"
        
        # Sort data by timestamp
        sorted_data = sorted(timeline_data, key=lambda x: x.get('timestamp', 0))
        
        # Limit points if requested
        if self.limit and len(sorted_data) > self.limit:
            sorted_data = sorted_data[-self.limit:]  # Keep most recent
        
        if format_type == 'text':
            output = f"{self.title}:\n"
            
            max_value = max(x.get('value', 0) for x in sorted_data)
            max_bar_width = 40
            scale = max_bar_width / max_value if max_value > 0 else 0
            
            for point in sorted_data:
                timestamp = point.get('timestamp', 0)
                value = point.get('value', 0)
                label = point.get('label', '')
                
                if isinstance(timestamp, (int, float)):
                    # Convert timestamp to datetime
                    dt = datetime.datetime.fromtimestamp(timestamp)
                    date_str = dt.strftime(self.time_format)
                else:
                    date_str = str(timestamp)
                
                bar_width = int(value * scale) if value > 0 else 0
                bar = '█' * bar_width
                
                output += f"  {date_str} | {bar} {value} {label}\n"
            
            return output
        
        elif format_type == 'html':
            points_html = ""
            max_value = max(x.get('value', 0) for x in sorted_data)
            
            for point in sorted_data:
                timestamp = point.get('timestamp', 0)
                value = point.get('value', 0)
                label = point.get('label', '')
                
                if isinstance(timestamp, (int, float)):
                    dt = datetime.datetime.fromtimestamp(timestamp)
                    date_str = dt.strftime(self.time_format)
                else:
                    date_str = str(timestamp)
                
                # Calculate bar height as percentage of max
                height_percent = (value / max_value * 100) if max_value > 0 else 0
                
                points_html += f"""
                <div class="timeline-point" title="{html.escape(label) if label else date_str}: {value}">
                    <div class="timeline-bar" style="height: {height_percent}%;"></div>
                    <div class="timeline-date">{html.escape(date_str)}</div>
                    <div class="timeline-value">{value}</div>
                </div>
                """
            
            return f"""
            <div class="chart-component" id="{html.escape(self.component_id)}">
                <h3 class="chart-title">{html.escape(self.title)}</h3>
                <div class="timeline-container">
                    {points_html}
                </div>
            </div>
            """
        
        elif format_type == 'json':
            return {
                'component_id': self.component_id,
                'component_type': self.component_type,
                'title': self.title,
                'data': sorted_data
            }
        
        return ""


class TaskHierarchyComponent(Component):
    """
    A component that displays a hierarchical task structure.
    """
    
    def __init__(
        self,
        component_id: str,
        title: str,
        data_key: str = "task_hierarchy",
        max_depth: Optional[int] = None,
        show_details: bool = True
    ):
        """
        Initialize a new task hierarchy component.
        
        Args:
            component_id: Unique identifier for the component
            title: Title to display for the component
            data_key: Key to extract the hierarchy data from the data dictionary
            max_depth: Maximum depth to display
            show_details: Whether to show task details
        """
        super().__init__(component_id, "task_hierarchy")
        self.title = title
        self.data_key = data_key
        self.max_depth = max_depth
        self.show_details = show_details
    
    def render(self, data: Dict[str, Any], format_type: str = 'text') -> str:
        """
        Render the task hierarchy component.
        
        Args:
            data: Data dictionary containing the hierarchy data
            format_type: Output format (text, html, json)
            
        Returns:
            Rendered component as a string
        """
        # Extract hierarchy data with fallback
        hierarchy = data.get(self.data_key, {})
        
        if not hierarchy:
            return f"{self.title}: No hierarchy data available\n"
        
        if format_type == 'text':
            output = f"{self.title}:\n"
            
            def render_node(node, prefix="", depth=0):
                """Recursively render a hierarchy node in text format."""
                if self.max_depth is not None and depth > self.max_depth:
                    return ""
                
                node_output = ""
                name = node.get('name', 'Unknown')
                task_id = node.get('id', '')
                status = node.get('status', '')
                
                # Format task details
                if self.show_details:
                    details = f"[{status}]" if status else ""
                    if task_id:
                        details += f" ({task_id})" if details else f"({task_id})"
                else:
                    details = ""
                
                # Add this node
                node_output += f"{prefix}└─ {name} {details}\n"
                
                # Add children with indentation
                children = node.get('children', [])
                child_prefix = prefix + "   "
                
                for i, child in enumerate(children):
                    if i == len(children) - 1:
                        node_output += render_node(child, child_prefix, depth + 1)
                    else:
                        node_output += render_node(child, child_prefix, depth + 1)
                
                return node_output
            
            # Start rendering from the root node
            output += render_node(hierarchy)
            
            return output
        
        elif format_type == 'html':
            def render_node_html(node, depth=0):
                """Recursively render a hierarchy node in HTML format."""
                if self.max_depth is not None and depth > self.max_depth:
                    return ""
                
                name = node.get('name', 'Unknown')
                task_id = node.get('id', '')
                status = node.get('status', '')
                
                # Format task details
                details_html = ""
                if self.show_details:
                    if status:
                        status_class = str(status).lower().replace(' ', '_')
                        details_html += f'<span class="task-status {status_class}">{html.escape(status)}</span>'
                    
                    if task_id:
                        details_html += f'<span class="task-id">{html.escape(task_id)}</span>'
                    
                    if details_html:
                        details_html = f'<span class="task-details">{details_html}</span>'
                
                # Process children
                children = node.get('children', [])
                children_html = ""
                
                if children:
                    children_html += '<ul class="task-children">'
                    for child in children:
                        children_html += f'<li class="task-item">{render_node_html(child, depth + 1)}</li>'
                    children_html += '</ul>'
                
                return f"""
                <span class="task-name">{html.escape(name)}</span>{details_html}
                {children_html}
                """
            
            return f"""
            <div class="hierarchy-component" id="{html.escape(self.component_id)}">
                <h3 class="hierarchy-title">{html.escape(self.title)}</h3>
                <div class="task-hierarchy">
                    <ul class="task-root">
                        <li class="task-item">{render_node_html(hierarchy)}</li>
                    </ul>
                </div>
            </div>
            """
        
        elif format_type == 'json':
            return {
                'component_id': self.component_id,
                'component_type': self.component_type,
                'title': self.title,
                'data': hierarchy
            }
        
        return ""


class DashboardLayout(Component):
    """
    A component that arranges other components into a layout.
    """
    
    def __init__(
        self,
        component_id: str,
        title: str,
        components: List[Component]
    ):
        """
        Initialize a new dashboard layout component.
        
        Args:
            component_id: Unique identifier for the component
            title: Title to display for the component
            components: List of components to include in the layout
        """
        super().__init__(component_id, "layout")
        self.title = title
        self.components = components
    
    def render(self, data: Dict[str, Any], format_type: str = 'text') -> str:
        """
        Render the dashboard layout component.
        
        Args:
            data: Data dictionary containing the data for all components
            format_type: Output format (text, html, json)
            
        Returns:
            Rendered component as a string
        """
        if format_type == 'text':
            output = f"{self.title}\n"
            output += "=" * len(self.title) + "\n\n"
            
            for component in self.components:
                component_output = component.render(data, format_type)
                output += component_output + "\n"
            
            return output
        
        elif format_type == 'html':
            components_html = ""
            for component in self.components:
                components_html += component.render(data, format_type)
            
            return f"""
            <div class="dashboard-layout" id="{html.escape(self.component_id)}">
                <h2 class="dashboard-title">{html.escape(self.title)}</h2>
                <div class="dashboard-components">
                    {components_html}
                </div>
            </div>
            """
        
        elif format_type == 'json':
            return {
                'component_id': self.component_id,
                'component_type': self.component_type,
                'title': self.title,
                'components': [component.render(data, 'json') for component in self.components]
            }
        
        return ""
    
    def get_dependencies(self) -> Set[str]:
        """
        Get the component IDs that this component depends on.
        
        Returns:
            Set of component IDs
        """
        return {component.component_id for component in self.components} 