# Task Visualization Plugin

This plugin extends the ClickUp JSON Manager with visualization capabilities for task data, metrics, and progress tracking.

## Features

- Multiple chart types for visualizing task data
- Support for different rendering backends (matplotlib, plotly, ASCII)
- Customizable colors, themes, and chart settings
- Integration with dashboard hooks
- Exportable charts in various formats (PNG, SVG, PDF)
- Fallback to ASCII charts when graphical rendering is not available

## Chart Types

The plugin provides the following visualizations:

1. **Task Status Distribution**: Pie chart showing the distribution of tasks by status.
2. **Task Priority Distribution**: Bar chart showing the distribution of tasks by priority.
3. **Task Completion Trend**: Line chart showing task completion over time, with both daily and cumulative views.
4. **Tag Distribution**: Bar chart showing the frequency of tags across tasks.
5. **Task Completion Rate**: Gauge chart showing the overall task completion rate.
6. **Task Hierarchy Tree**: Tree visualization of task hierarchies with status indicators.

## Configuration

The plugin supports the following configuration options:

```json
{
  "render_backend": "matplotlib",  // Options: "matplotlib", "plotly", "ascii"
  "default_charts": ["status_distribution", "priority_distribution", "completion_trend"],
  "chart_theme": "default",  // Options: "default", "dark", "light", "colorblind_friendly"
  "export_formats": ["png", "svg", "pdf"],
  "interactive": true,
  "custom_colors": {
    "to do": "#3498db",
    "in progress": "#f39c12",
    "in review": "#9b59b6",
    "complete": "#2ecc71"
  },
  "max_chart_items": 10,
  "refresh_interval": 60
}
```

## Usage

### Basic Usage

```python
from refactor.plugins.sample.visualization.visualization_plugin import VisualizationPlugin

# Create plugin configuration
config = {
    'render_backend': 'matplotlib',
    'default_charts': ['status_distribution', 'priority_distribution'],
    'chart_theme': 'default',
    'export_formats': ['png'],
    'interactive': True
}

# Initialize the plugin
visualization_plugin = VisualizationPlugin('visualization_plugin', config)

# Initialize with context
visualization_plugin.initialize({'logger': logger})

# Get available chart types
chart_types = visualization_plugin.get_available_chart_types()

# Create a chart
chart_result = visualization_plugin.create_chart('status_distribution', tasks_data)

# Access chart output
ascii_representation = chart_result['ascii']
image_path = chart_result.get('image_path')
```

### CLI Integration

The plugin registers hooks for the dashboard command, allowing for visualization integration with the CLI:

```bash
# Example CLI usage
./cujm dashboard 000_clickup_tasks_template.json --visualize status_distribution
```

### Dashboard Integration

The plugin integrates with the dashboard through hooks:

- `dashboard.initialize`: Registers custom views and prepares data
- `dashboard.render_view`: Injects custom visualizations into dashboard views
- `task.status_changed`: Updates metrics when task status changes
- `command.dashboard`: Customizes dashboard output with visualizations

## Dependencies

The plugin has the following dependencies:

- **Required**: None for ASCII charts
- **Optional**: matplotlib for graphical charts (recommended)
- **Optional**: plotly for interactive web-based charts

## Examples

See the `example_usage.py` script for a complete example of how to use the visualization plugin.

## Contributing

When adding new chart types, follow these steps:

1. Add the new chart function to the `VisualizationPlugin` class
2. Register the function in the `_register_charts` method
3. Ensure the function works with all rendering backends, including ASCII fallback
4. Add documentation for the new chart type
5. Update any affected unit tests

## License

This plugin is released under the same license as the ClickUp JSON Manager project. 