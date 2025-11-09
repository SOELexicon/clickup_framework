"""
Task Visualization Plugin that extends the dashboard with custom charts and graphs.
"""
import os
import json
import tempfile
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta

# Import plugin interface and base classes
from refactor.plugins.plugin_interface import VisualizationPlugin as VisualizationPluginInterface
from refactor.plugins.hooks.hook_system import register_hook

# For simple ASCII charts (always available)
class ASCIIChartRenderer:
    """Simple ASCII chart renderer for terminal output."""
    
    @staticmethod
    def bar_chart(labels: List[str], values: List[int], title: str, width: int = 40) -> str:
        """Create a simple ASCII bar chart."""
        max_value = max(values) if values else 1
        max_label_len = max(len(label) for label in labels) if labels else 10
        
        output = [f"\n{title}\n"]
        for i, (label, value) in enumerate(zip(labels, values)):
            bar_len = int((value / max_value) * width)
            bar = "█" * bar_len
            output.append(f"{label.ljust(max_label_len)} │ {bar} {value}")
        
        return "\n".join(output)
    
    @staticmethod
    def progress_bar(value: float, total: float, width: int = 40) -> str:
        """Create a simple ASCII progress bar."""
        percent = value / total if total else 0
        filled_len = int(width * percent)
        bar = "█" * filled_len + "░" * (width - filled_len)
        return f"[{bar}] {percent:.1%}"


class VisualizationPlugin(VisualizationPluginInterface):
    """Plugin that provides various visualization options for task data."""
    
    def __init__(self, plugin_id: str, config: Dict[str, Any]):
        """Initialize the visualization plugin."""
        self.plugin_id = plugin_id
        self.config = config
        self.renderers = {}
        self.chart_registry = {}
        self.logger = None
        self.last_refresh = datetime.now()
        
        # Initialize renderers
        self._init_renderers()
        
        # Register chart types
        self._register_charts()
    
    def _init_renderers(self) -> None:
        """Initialize rendering backends based on configuration."""
        # ASCII renderer is always available
        self.renderers['ascii'] = ASCIIChartRenderer()
        
        # Optionally load matplotlib if available and configured
        if self.config.get('render_backend') in ('matplotlib', 'default'):
            try:
                import matplotlib.pyplot as plt
                from matplotlib.figure import Figure
                from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
                
                self.renderers['matplotlib'] = {
                    'plt': plt,
                    'Figure': Figure,
                    'FigureCanvas': FigureCanvas
                }
                
            except ImportError:
                if self.logger:
                    self.logger.warning(f"[{self.plugin_id}] Matplotlib not available, falling back to ASCII rendering")
        
        # Optionally load plotly if available and configured
        if self.config.get('render_backend') == 'plotly':
            try:
                import plotly.graph_objects as go
                import plotly.express as px
                
                self.renderers['plotly'] = {
                    'go': go,
                    'px': px
                }
                
            except ImportError:
                if self.logger:
                    self.logger.warning(f"[{self.plugin_id}] Plotly not available, falling back to ASCII rendering")
    
    def _register_charts(self) -> None:
        """Register available chart types."""
        self.chart_registry = {
            'status_distribution': self.create_status_distribution,
            'priority_distribution': self.create_priority_distribution,
            'completion_trend': self.create_completion_trend,
            'tag_distribution': self.create_tag_distribution,
            'task_completion_rate': self.create_task_completion_rate,
            'task_hierarchy_tree': self.create_task_hierarchy_tree
        }
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """Validate plugin configuration."""
        errors = []
        
        required_config = [
            'render_backend',
            'default_charts',
            'chart_theme',
            'export_formats',
            'interactive'
        ]
        
        for config_key in required_config:
            if config_key not in self.config:
                errors.append(f"Missing required config: {config_key}")
        
        if 'render_backend' in self.config:
            if self.config['render_backend'] not in ['matplotlib', 'plotly', 'ascii']:
                errors.append(f"Invalid render_backend: {self.config['render_backend']}. " 
                              f"Must be one of: matplotlib, plotly, ascii")
        
        if 'default_charts' in self.config and isinstance(self.config['default_charts'], list):
            for chart in self.config['default_charts']:
                if chart not in self.chart_registry:
                    errors.append(f"Unknown chart type in default_charts: {chart}")
        
        return len(errors) == 0, errors
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize plugin with application context."""
        self.logger = context.get('logger')
        if self.logger:
            self.logger.info(f"[{self.plugin_id}] Visualization plugin initialized")
    
    def get_available_chart_types(self) -> List[Dict[str, str]]:
        """Return list of available chart types."""
        return [
            {
                'id': 'status_distribution',
                'name': 'Task Status Distribution',
                'description': 'Pie chart showing distribution of tasks by status'
            },
            {
                'id': 'priority_distribution',
                'name': 'Task Priority Distribution',
                'description': 'Bar chart showing distribution of tasks by priority'
            },
            {
                'id': 'completion_trend',
                'name': 'Task Completion Trend',
                'description': 'Line chart showing task completion over time'
            },
            {
                'id': 'tag_distribution',
                'name': 'Tag Distribution',
                'description': 'Bar chart showing frequency of tags across tasks'
            },
            {
                'id': 'task_completion_rate',
                'name': 'Task Completion Rate',
                'description': 'Gauge chart showing task completion rate'
            },
            {
                'id': 'task_hierarchy_tree',
                'name': 'Task Hierarchy Tree',
                'description': 'Tree visualization of task hierarchies'
            }
        ]
    
    def create_chart(self, chart_type: str, task_data: List[Dict[str, Any]], 
                    options: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Create a chart of the specified type using the provided task data."""
        options = options or {}
        
        if chart_type not in self.chart_registry:
            if self.logger:
                self.logger.error(f"[{self.plugin_id}] Unknown chart type: {chart_type}")
            return None
        
        try:
            chart_func = self.chart_registry[chart_type]
            result = chart_func(task_data, options)
            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"[{self.plugin_id}] Error creating chart {chart_type}: {str(e)}")
            return None
    
    def create_status_distribution(self, task_data: List[Dict[str, Any]], 
                                  options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a status distribution chart."""
        # Count tasks by status
        status_counts = {}
        for task in task_data:
            status = task.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        labels = list(status_counts.keys())
        values = list(status_counts.values())
        title = options.get('title', 'Task Status Distribution')
        
        # Get custom colors if available
        colors = self.config.get('custom_colors', {})
        
        # Create the chart based on the selected backend
        result = {
            'chart_type': 'status_distribution',
            'title': title,
            'data': {
                'labels': labels,
                'values': values
            }
        }
        
        # Generate ASCII version for terminal
        result['ascii'] = ASCIIChartRenderer.bar_chart(labels, values, title)
        
        # Generate matplotlib version if available
        if 'matplotlib' in self.renderers:
            try:
                plt = self.renderers['matplotlib']['plt']
                
                # Create figure
                fig, ax = plt.subplots(figsize=(8, 6))
                
                # Use custom colors if available
                chart_colors = [colors.get(status, f"C{i}") for i, status in enumerate(labels)]
                
                # Create pie chart
                ax.pie(values, labels=labels, autopct='%1.1f%%', colors=chart_colors, startangle=90)
                ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                ax.set_title(title)
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
                    temp_filename = temp.name
                    plt.savefig(temp_filename, format='png')
                    plt.close(fig)
                
                result['image_path'] = temp_filename
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[{self.plugin_id}] Error creating matplotlib chart: {str(e)}")
        
        return result
    
    def create_priority_distribution(self, task_data: List[Dict[str, Any]], 
                                    options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a priority distribution bar chart."""
        # Count tasks by priority
        priority_counts = {}
        for task in task_data:
            priority = task.get('priority', 0)
            priority_label = self._get_priority_label(priority)
            priority_counts[priority_label] = priority_counts.get(priority_label, 0) + 1
        
        # Sort by priority (assuming 1 is highest, 5 is lowest)
        priority_order = ['P1 (Urgent)', 'P2 (High)', 'P3 (Medium)', 'P4 (Low)', 'P5 (Trivial)']
        labels = [label for label in priority_order if label in priority_counts]
        values = [priority_counts[label] for label in labels]
        
        title = options.get('title', 'Task Priority Distribution')
        
        # Create result dictionary
        result = {
            'chart_type': 'priority_distribution',
            'title': title,
            'data': {
                'labels': labels,
                'values': values
            }
        }
        
        # Generate ASCII version
        result['ascii'] = ASCIIChartRenderer.bar_chart(labels, values, title)
        
        # Generate matplotlib version if available
        if 'matplotlib' in self.renderers:
            try:
                plt = self.renderers['matplotlib']['plt']
                
                # Create figure
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Create bar chart
                colors = ['#e74c3c', '#f39c12', '#3498db', '#2ecc71', '#95a5a6']
                bars = ax.bar(labels, values, color=[colors[i] for i in range(len(labels))])
                
                # Add value labels on top of bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                            f'{height:.0f}', ha='center', va='bottom')
                
                ax.set_title(title)
                ax.set_ylabel('Number of Tasks')
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
                    temp_filename = temp.name
                    plt.savefig(temp_filename, format='png')
                    plt.close(fig)
                
                result['image_path'] = temp_filename
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[{self.plugin_id}] Error creating matplotlib chart: {str(e)}")
        
        return result
    
    def create_completion_trend(self, task_data: List[Dict[str, Any]], 
                               options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a line chart showing task completion trend over time."""
        # Extract completed task dates and sort
        completion_dates = []
        for task in task_data:
            if task.get('status') == 'complete' and 'date_completed' in task:
                try:
                    completion_dates.append(datetime.fromtimestamp(task['date_completed']))
                except (ValueError, TypeError):
                    # Skip invalid dates
                    pass
        
        # Sort dates
        completion_dates.sort()
        
        # If no completion dates, return empty chart
        if not completion_dates:
            return {
                'chart_type': 'completion_trend',
                'title': 'Task Completion Trend',
                'ascii': 'No completed tasks found',
                'data': {
                    'dates': [],
                    'completions': []
                }
            }
        
        # Group by day and count
        completion_counts = {}
        current_date = completion_dates[0].date()
        end_date = completion_dates[-1].date()
        
        # Initialize all dates in range
        delta = timedelta(days=1)
        while current_date <= end_date:
            completion_counts[current_date] = 0
            current_date += delta
        
        # Count completions by day
        for date in completion_dates:
            day = date.date()
            completion_counts[day] = completion_counts.get(day, 0) + 1
        
        # Prepare data for chart
        dates = list(completion_counts.keys())
        dates.sort()
        daily_counts = [completion_counts[date] for date in dates]
        
        # Calculate cumulative counts
        cumulative_counts = []
        total = 0
        for count in daily_counts:
            total += count
            cumulative_counts.append(total)
        
        # Format dates as strings
        date_strings = [date.strftime('%Y-%m-%d') for date in dates]
        
        title = options.get('title', 'Task Completion Trend')
        show_cumulative = options.get('show_cumulative', True)
        
        # Prepare result
        result = {
            'chart_type': 'completion_trend',
            'title': title,
            'data': {
                'dates': date_strings,
                'daily_completions': daily_counts,
                'cumulative_completions': cumulative_counts
            }
        }
        
        # Generate simple ASCII version (just showing the last 7 days or less)
        if len(dates) > 7:
            ascii_dates = date_strings[-7:]
            ascii_counts = daily_counts[-7:]
        else:
            ascii_dates = date_strings
            ascii_counts = daily_counts
        
        result['ascii'] = ASCIIChartRenderer.bar_chart(ascii_dates, ascii_counts, 
                                                     "Task Completion (Last 7 Days)")
        
        # Generate matplotlib version if available
        if 'matplotlib' in self.renderers:
            try:
                plt = self.renderers['matplotlib']['plt']
                
                # Create figure
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # Plot daily counts
                ax.bar(date_strings, daily_counts, alpha=0.6, color='#3498db', label='Daily')
                
                # Plot cumulative counts if requested
                if show_cumulative:
                    ax2 = ax.twinx()
                    ax2.plot(date_strings, cumulative_counts, 'r-', linewidth=2, 
                            label='Cumulative')
                    ax2.set_ylabel('Cumulative Completed Tasks')
                
                # Set up axes
                ax.set_title(title)
                ax.set_xlabel('Date')
                ax.set_ylabel('Tasks Completed')
                
                # Show legend
                lines1, labels1 = ax.get_legend_handles_labels()
                if show_cumulative:
                    lines2, labels2 = ax2.get_legend_handles_labels()
                    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
                else:
                    ax.legend(loc='upper left')
                
                # Rotate x-axis labels for readability
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
                    temp_filename = temp.name
                    plt.savefig(temp_filename, format='png')
                    plt.close(fig)
                
                result['image_path'] = temp_filename
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[{self.plugin_id}] Error creating matplotlib chart: {str(e)}")
        
        return result
    
    def create_tag_distribution(self, task_data: List[Dict[str, Any]], 
                               options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a bar chart showing tag distribution across tasks."""
        # Count tags
        tag_counts = {}
        for task in task_data:
            tags = task.get('tags', [])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Sort by count (descending)
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Limit to top N tags
        max_items = min(options.get('max_items', self.config.get('max_chart_items', 10)), 
                        len(sorted_tags))
        top_tags = sorted_tags[:max_items]
        
        labels = [tag for tag, _ in top_tags]
        values = [count for _, count in top_tags]
        
        title = options.get('title', 'Tag Distribution')
        
        # Create result
        result = {
            'chart_type': 'tag_distribution',
            'title': title,
            'data': {
                'labels': labels,
                'values': values
            }
        }
        
        # Generate ASCII version
        result['ascii'] = ASCIIChartRenderer.bar_chart(labels, values, title)
        
        # Generate matplotlib version if available
        if 'matplotlib' in self.renderers:
            try:
                plt = self.renderers['matplotlib']['plt']
                
                # Create figure
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # Create horizontal bar chart
                y_pos = range(len(labels))
                ax.barh(y_pos, values, align='center')
                ax.set_yticks(y_pos)
                ax.set_yticklabels(labels)
                ax.invert_yaxis()  # Labels read top-to-bottom
                ax.set_xlabel('Number of Tasks')
                ax.set_title(title)
                
                # Add count labels
                for i, v in enumerate(values):
                    ax.text(v + 0.1, i, str(v), va='center')
                
                plt.tight_layout()
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
                    temp_filename = temp.name
                    plt.savefig(temp_filename, format='png')
                    plt.close(fig)
                
                result['image_path'] = temp_filename
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[{self.plugin_id}] Error creating matplotlib chart: {str(e)}")
        
        return result
    
    def create_task_completion_rate(self, task_data: List[Dict[str, Any]], 
                                   options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a gauge chart showing task completion rate."""
        total_tasks = len(task_data)
        completed_tasks = sum(1 for task in task_data if task.get('status') == 'complete')
        
        if total_tasks == 0:
            completion_rate = 0
        else:
            completion_rate = (completed_tasks / total_tasks) * 100
        
        title = options.get('title', 'Task Completion Rate')
        
        # Create result
        result = {
            'chart_type': 'task_completion_rate',
            'title': title,
            'data': {
                'completed': completed_tasks,
                'total': total_tasks,
                'rate': completion_rate
            }
        }
        
        # Generate ASCII version
        result['ascii'] = (f"{title}\n\n"
                         f"Completed: {completed_tasks}/{total_tasks} tasks ({completion_rate:.1f}%)\n"
                         f"{ASCIIChartRenderer.progress_bar(completed_tasks, total_tasks, 40)}")
        
        # Generate matplotlib version if available
        if 'matplotlib' in self.renderers:
            try:
                plt = self.renderers['matplotlib']['plt']
                
                # Create figure
                fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
                
                # Gauge chart parameters
                start_angle = 3*np.pi/4  # Starting angle
                end_angle = -np.pi/4     # Ending angle
                
                # Calculate theta values for the gauge
                theta = np.linspace(start_angle, end_angle, 100)
                
                # Calculate radii for the gauge (fixed radius for gauge outline)
                r = np.ones(100)
                
                # Draw gauge outline
                ax.plot(theta, r, color='#cccccc', linewidth=3)
                
                # Calculate completion angle
                completion_angle = start_angle - (completion_rate/100) * (start_angle - end_angle)
                completion_theta = np.linspace(start_angle, completion_angle, 100)
                completion_r = np.ones(100)
                
                # Draw completion arc
                if completion_rate < 30:
                    color = '#e74c3c'  # Red for low completion
                elif completion_rate < 70:
                    color = '#f39c12'  # Orange for medium completion
                else:
                    color = '#2ecc71'  # Green for high completion
                
                ax.plot(completion_theta, completion_r, color=color, linewidth=3)
                
                # Set up the axes
                ax.set_rticks([])  # No radial ticks
                ax.set_xticks([])  # No angular ticks
                
                # Add percentage text in center
                ax.text(0, 0, f"{completion_rate:.1f}%", ha='center', va='center', 
                       fontsize=24, fontweight='bold')
                
                # Add label below
                ax.text(0, -0.4, f"{completed_tasks} of {total_tasks} tasks completed", 
                       ha='center', va='center', fontsize=12)
                
                # Set title
                ax.set_title(title, pad=20)
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
                    temp_filename = temp.name
                    plt.savefig(temp_filename, format='png')
                    plt.close(fig)
                
                result['image_path'] = temp_filename
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[{self.plugin_id}] Error creating matplotlib chart: {str(e)}")
        
        return result
    
    def create_task_hierarchy_tree(self, task_data: List[Dict[str, Any]], 
                                  options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a tree visualization of task hierarchies."""
        # Build task hierarchy
        task_map = {task.get('id'): task for task in task_data}
        root_tasks = [task for task in task_data if not task.get('parent_id')]
        
        # Build tree structure
        tree_data = self._build_hierarchy_tree(root_tasks, task_map)
        
        title = options.get('title', 'Task Hierarchy')
        
        # Create result
        result = {
            'chart_type': 'task_hierarchy_tree',
            'title': title,
            'data': {
                'tree': tree_data
            }
        }
        
        # Generate ASCII version
        ascii_tree = self._generate_ascii_tree(tree_data)
        result['ascii'] = f"{title}\n\n{ascii_tree}"
        
        # Generate matplotlib version if available
        if 'matplotlib' in self.renderers and False:  # Tree charts in matplotlib are complex
            # This would require more code that's beyond the scope here
            pass
        
        return result
    
    def _build_hierarchy_tree(self, tasks: List[Dict[str, Any]], 
                             task_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build a hierarchical tree structure from tasks."""
        result = []
        for task in tasks:
            # Find children
            children = [t for t in task_map.values() if t.get('parent_id') == task.get('id')]
            
            # Build node
            node = {
                'id': task.get('id'),
                'name': task.get('name'),
                'status': task.get('status', 'unknown'),
                'children': self._build_hierarchy_tree(children, task_map) if children else []
            }
            
            result.append(node)
        
        return result
    
    def _generate_ascii_tree(self, tree_data: List[Dict[str, Any]], prefix: str = '') -> str:
        """Generate an ASCII representation of the task hierarchy."""
        result = []
        
        for i, node in enumerate(tree_data):
            is_last = i == len(tree_data) - 1
            status_icon = self._get_status_icon(node.get('status', 'unknown'))
            
            # Current node
            if is_last:
                result.append(f"{prefix}└── {status_icon} {node.get('name')}")
                child_prefix = prefix + "    "
            else:
                result.append(f"{prefix}├── {status_icon} {node.get('name')}")
                child_prefix = prefix + "│   "
            
            # Children
            if node.get('children'):
                child_tree = self._generate_ascii_tree(node['children'], child_prefix)
                result.append(child_tree)
        
        return '\n'.join(result)
    
    @staticmethod
    def _get_status_icon(status: str) -> str:
        """Get an icon representing task status."""
        status_icons = {
            'to do': '○',
            'in progress': '◔',
            'in review': '◑',
            'complete': '●',
            'blocked': '✗',
            'unknown': '?'
        }
        return status_icons.get(status.lower(), '?')
    
    @staticmethod
    def _get_priority_label(priority: int) -> str:
        """Convert priority number to label."""
        priority_labels = {
            1: 'P1 (Urgent)',
            2: 'P2 (High)',
            3: 'P3 (Medium)',
            4: 'P4 (Low)',
            5: 'P5 (Trivial)'
        }
        return priority_labels.get(priority, f"P{priority}")
    
    def get_renderer_backends(self) -> List[str]:
        """Return list of available rendering backends."""
        return list(self.renderers.keys())
    
    def cleanup(self) -> None:
        """Clean up any temporary resources."""
        # Nothing to do here for the basic implementation
        pass


# Register hooks
@register_hook('dashboard.initialize')
def on_dashboard_initialize(dashboard_context):
    """Hook called when dashboard is initialized."""
    # Here we could register custom views or prepare data
    return dashboard_context


@register_hook('dashboard.render_view')
def on_dashboard_render(view_context):
    """Hook called when dashboard renders a view."""
    # Here we could inject custom visualizations into the dashboard
    return view_context


@register_hook('task.status_changed')
def on_task_status_changed(task_data, old_status, new_status):
    """Hook called when a task's status changes."""
    # Here we could update metrics or notify about significant status changes
    return task_data


@register_hook('command.dashboard')
def on_dashboard_command(args, dashboard_data):
    """Hook called when dashboard command is executed."""
    # Here we could customize dashboard output or add visualization options
    return dashboard_data 