# Dashboard Module

The Dashboard Module provides visualization and reporting functionality for the ClickUp JSON Manager. It follows a component-based architecture that makes it easy to extend and customize.

## Architecture

The dashboard module consists of several key components:

1. **Component Base Classes**:
   - `Component`: Base class for all dashboard components
   - `DataProvider`: Interface for data providers
   - `DashboardState`: State management for the dashboard

2. **Visualization Components**:
   - `MetricComponent`: Displays a single metric value
   - `BarChartComponent`: Displays data as a horizontal bar chart
   - `PieChartComponent`: Displays data as a pie chart
   - `TableComponent`: Displays tabular data
   - `TimelineComponent`: Displays timeline data
   - `TaskHierarchyComponent`: Displays a hierarchical task structure
   - `DashboardLayout`: Arranges components into a layout

3. **Data Providers**:
   - `TaskDataProvider`: Provides task data from the core manager

4. **Dashboard Manager**:
   - `DashboardManager`: Central manager that coordinates components and rendering

## Usage

### Basic Usage

```python
from refactor.core import CoreManager
from refactor.dashboard import DashboardManager

# Initialize the core manager
core_manager = CoreManager("path/to/file.json")

# Create a dashboard manager
dashboard_manager = DashboardManager(core_manager)

# Render the dashboard
output = dashboard_manager.render_dashboard("main_dashboard", "text")
print(output)
```

### Navigation

```python
# Navigate to a specific entity
dashboard_manager.navigate("task", "tsk_123456")

# Navigate back
dashboard_manager.navigate_back()

# Apply filters
dashboard_manager.apply_filter("status", "in progress")
dashboard_manager.apply_filter("priority", 1)

# Clear filters
dashboard_manager.clear_filter("status")
dashboard_manager.clear_all_filters()
```

### Customizing the Dashboard

```python
from refactor.dashboard import (
    DashboardManager,
    MetricComponent,
    BarChartComponent,
    DashboardLayout
)

# Create custom components
task_count = MetricComponent(
    component_id="task_count",
    title="Total Tasks",
    metric_key="task_count"
)

status_chart = BarChartComponent(
    component_id="status_chart",
    title="Tasks by Status",
    data_key="status_distribution"
)

# Create a layout
custom_layout = DashboardLayout(
    component_id="custom_dashboard",
    title="My Custom Dashboard",
    components=[task_count, status_chart]
)

# Register with the dashboard manager
dashboard_manager.register_component(custom_layout)

# Render the custom dashboard
output = dashboard_manager.render_dashboard("custom_dashboard", "html")
```

## Output Formats

The dashboard supports multiple output formats:

- **Text**: Plain text output suitable for terminal display
- **HTML**: Rich HTML output for web browsers
- **JSON**: Structured data for programmatic use

## CLI Commands

The dashboard module provides several CLI commands:

- `dashboard`: Display a dashboard
- `interactive-dashboard`: Launch an interactive dashboard with navigation
- `task-metrics`: Display task metrics and statistics
- `completion-timeline`: Visualize task completion over time
- `task-hierarchy`: Display task hierarchy visualization

## Extending the Dashboard

### Creating a Custom Component

```python
from refactor.dashboard import Component

class MyCustomComponent(Component):
    def __init__(self, component_id: str, title: str):
        super().__init__(component_id, "custom")
        self.title = title
    
    def render(self, data, format_type="text"):
        if format_type == "text":
            return f"{self.title}\n{'-' * len(self.title)}\nCustom content here!"
        elif format_type == "html":
            return f"<div class='custom-component'><h3>{self.title}</h3><p>Custom content here!</p></div>"
        elif format_type == "json":
            return {
                "component_id": self.component_id,
                "component_type": self.component_type,
                "title": self.title,
                "content": "Custom content here!"
            }
```

### Creating a Custom Data Provider

```python
from refactor.dashboard import DataProvider

class MyCustomDataProvider(DataProvider):
    def get_data(self, context):
        # Implement your data fetching logic
        return {
            "my_metric": 42,
            "my_distribution": {
                "category1": 10,
                "category2": 20,
                "category3": 30
            }
        }
    
    def get_filtered_data(self, context, filters):
        # Implement filtered data fetching
        data = self.get_data(context)
        # Apply filters
        return data
```

## Plugin Integration

The dashboard module supports plugins through the following integration points:

- **Custom Components**: Register custom visualization components
- **Custom Data Providers**: Provide data from external sources
- **Dashboard Extensions**: Add new dashboard types and layouts
- **Export Formatters**: Add support for additional output formats 