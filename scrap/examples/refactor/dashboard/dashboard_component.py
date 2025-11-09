"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/dashboard/dashboard_component.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - DashboardManager: Utilizes component abstractions to build dashboard layouts
    - Components: Concrete implementations extend these base classes
    - InteractiveDashboard: Uses NavigationContext for drill-down navigation
    - CLI Commands: Leverages DashboardState for interactive dashboards
    - RESTfulAPI: Uses Component interfaces for web-based dashboards

Purpose:
    Provides the core component architecture for the dashboard system. Defines
    the abstractions, interfaces, and state management classes that form the
    foundation of the dashboard visualization system. Implements a hierarchical
    component model with separation between data providers and visualization components.

Requirements:
    - CRITICAL: Components must be renderable in multiple formats (text, HTML, JSON)
    - CRITICAL: State management must preserve navigation history for hierarchical browsing
    - CRITICAL: Data providers must abstract data access from visualization components
    - Components must declare their dependencies explicitly
    - State transitions must be atomic and reversible via navigation history
    - All components must handle missing or incomplete data gracefully

Dashboard Component Module

This module defines the component-based architecture for the Dashboard module.
It provides:
- Component interface for visualization elements
- Data provider interface for data access
- State management for dashboard navigation
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic, Set


# Type variable for component data
T = TypeVar('T')


class DataProvider(ABC):
    """
    Abstract interface for dashboard data providers.
    
    This interface is responsible for supplying data to dashboard components.
    """
    
    @abstractmethod
    def get_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get data for the dashboard based on the given context.
        
        Args:
            context: Context information for the data request
            
        Returns:
            Data for the dashboard
        """
        pass
    
    @abstractmethod
    def get_filtered_data(self, context: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get filtered data for the dashboard.
        
        Args:
            context: Context information for the data request
            filters: Filter criteria to apply
            
        Returns:
            Filtered data for the dashboard
        """
        pass


class Component:
    """
    Base class for dashboard components.
    
    Components are responsible for rendering specific parts of the dashboard.
    """
    
    def __init__(self, component_id: str, component_type: str):
        """
        Initialize the component with an ID and type.
        
        Args:
            component_id: Unique identifier for this component
            component_type: Type of this component
        """
        self._component_id = component_id
        self._component_type = component_type
    
    @property
    def component_id(self) -> str:
        """
        Get the unique identifier for this component.
        
        Returns:
            Component ID
        """
        return self._component_id
    
    @property
    def component_type(self) -> str:
        """
        Get the type of this component.
        
        Returns:
            Component type
        """
        return self._component_type
    
    def render(self, data: Dict[str, Any], format_type: str = 'text') -> str:
        """
        Render the component with the provided data.
        
        Args:
            data: Data to render
            format_type: Output format type (text, html, json)
            
        Returns:
            Rendered component as a string
        """
        return f"Component {self.component_id} of type {self.component_type}"
    
    def get_dependencies(self) -> Set[str]:
        """
        Get IDs of components this component depends on.
        
        Returns:
            Set of component IDs
        """
        return set()


class NavigationContext:
    """
    Context for dashboard navigation state.
    
    This class maintains the current view state and navigation history.
    """
    
    def __init__(self, level: str, entity_id: Optional[str] = None, parent_context: Optional['NavigationContext'] = None):
        """
        Initialize the navigation context.
        
        Args:
            level: Current navigation level (e.g., 'root', 'space', 'folder', 'list', 'task')
            entity_id: ID of the current entity being viewed
            parent_context: Optional parent context for hierarchical navigation
        """
        self.level = level
        self.entity_id = entity_id
        self.parent_context = parent_context
        self.history = [(level, entity_id)] if parent_context is None else []
        
    def navigate_to(self, level: str, entity_id: Optional[str] = None) -> 'NavigationContext':
        """
        Create a new context representing navigation to a specific entity.
        
        Args:
            level: Level to navigate to
            entity_id: ID of the entity to navigate to
            
        Returns:
            New navigation context
        """
        new_context = NavigationContext(level, entity_id, parent_context=self)
        if self.history is not None:
            new_context.history = self.history + [(level, entity_id)]
        return new_context
    
    def navigate_back(self) -> Optional['NavigationContext']:
        """
        Navigate back to the parent context.
        
        Returns:
            Parent navigation context, or None if at root
        """
        return self.parent_context
    
    def get_breadcrumb_trail(self) -> List[Dict[str, Any]]:
        """
        Get the hierarchical breadcrumb trail for navigation.
        
        Returns:
            List of breadcrumb entries with level and entity_id
        """
        trail = []
        context = self
        
        while context is not None:
            trail.append({
                'level': context.level,
                'entity_id': context.entity_id
            })
            context = context.parent_context
            
        return list(reversed(trail))
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the navigation history.
        
        Returns:
            List of navigation history entries with level and entity_id
        """
        return [{'level': level, 'entity_id': entity_id} for level, entity_id in self.history]


class DashboardState:
    """
    State container for the dashboard.
    
    This class maintains the overall dashboard state, including:
    - Current navigation context
    - Active filters
    - Selected metrics
    - View preferences
    """
    
    def __init__(self, initial_context: Optional[NavigationContext] = None):
        """
        Initialize the dashboard state.
        
        Args:
            initial_context: Optional initial navigation context
        """
        self.navigation_context = initial_context or NavigationContext('root')
        self.active_filters = {}
        self.selected_metrics = []
        self.view_preferences = {
            'view_type': 'standard',
            'sort_by': 'priority',
            'sort_direction': 'asc',
            'page_size': 20,
            'table_sort_column': None,
            'table_sort_direction': 'asc'
        }
        self.selected_entity = None
        
    def navigate_to(self, level: str, entity_id: Optional[str] = None) -> None:
        """
        Navigate to a specific entity.
        
        Args:
            level: Level to navigate to
            entity_id: ID of the entity to navigate to
        """
        self.navigation_context = self.navigation_context.navigate_to(level, entity_id)
        
    def navigate_back(self) -> bool:
        """
        Navigate back to the parent context.
        
        Returns:
            True if navigation was successful, False if at root
        """
        parent_context = self.navigation_context.navigate_back()
        if parent_context is not None:
            self.navigation_context = parent_context
            return True
        return False
    
    def set_filter(self, key: str, value: Any) -> None:
        """
        Set a filter value.
        
        Args:
            key: Filter key
            value: Filter value
        """
        self.active_filters[key] = value
        
    def clear_filter(self, key: str) -> None:
        """
        Clear a specific filter.
        
        Args:
            key: Filter key to clear
        """
        if key in self.active_filters:
            del self.active_filters[key]
            
    def clear_all_filters(self) -> None:
        """
        Clear all active filters.
        """
        self.active_filters = {}
        
    def update_preference(self, key: str, value: Any) -> None:
        """
        Update a view preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        self.view_preferences[key] = value


class MetricsCalculator:
    """
    Calculator for dashboard metrics.
    
    This class is responsible for calculating various metrics based on the data.
    """
    
    def calculate_metrics(self, data: Dict[str, Any], metrics: List[str]) -> Dict[str, Any]:
        """
        Calculate specified metrics from the data.
        
        Args:
            data: Data to calculate metrics from
            metrics: List of metric names to calculate
            
        Returns:
            Dictionary of calculated metrics
        """
        result = {}
        
        for metric in metrics:
            if metric == 'task_count':
                result[metric] = self._calculate_task_count(data)
            elif metric == 'completion_percentage':
                result[metric] = self._calculate_completion_percentage(data)
            elif metric == 'status_distribution':
                result[metric] = self._calculate_status_distribution(data)
            elif metric == 'priority_distribution':
                result[metric] = self._calculate_priority_distribution(data)
            # Add more metric calculations as needed
                
        return result
    
    def _calculate_task_count(self, data: Dict[str, Any]) -> int:
        """
        Calculate the total number of tasks.
        
        Args:
            data: Data containing tasks
            
        Returns:
            Total task count
        """
        return len(data.get('tasks', []))
    
    def _calculate_completion_percentage(self, data: Dict[str, Any]) -> float:
        """
        Calculate the percentage of completed tasks.
        
        Args:
            data: Data containing tasks
            
        Returns:
            Completion percentage (0-100)
        """
        tasks = data.get('tasks', [])
        if not tasks:
            return 0.0
            
        total = len(tasks)
        completed = sum(1 for task in tasks if str(task.get('status', '')).lower() == 'complete')
        return (completed / total) * 100 if total > 0 else 0.0
    
    def _calculate_status_distribution(self, data: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate the distribution of tasks by status.
        
        Args:
            data: Data containing tasks
            
        Returns:
            Dictionary mapping status values to counts
        """
        tasks = data.get('tasks', [])
        result = {}
        
        for task in tasks:
            status = task.get('status', 'unknown')
            result[status] = result.get(status, 0) + 1
            
        return result
    
    def _calculate_priority_distribution(self, data: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate the distribution of tasks by priority.
        
        Args:
            data: Data containing tasks
            
        Returns:
            Dictionary mapping priority values to counts
        """
        tasks = data.get('tasks', [])
        result = {}
        
        for task in tasks:
            priority = str(task.get('priority', 'unknown'))
            result[priority] = result.get(priority, 0) + 1
            
        return result


class DashboardManager:
    """
    Manager for the dashboard components and state.
    
    This class orchestrates the dashboard rendering and navigation.
    """
    
    def __init__(self, data_provider: DataProvider):
        """
        Initialize the dashboard manager.
        
        Args:
            data_provider: Data provider for dashboard data
        """
        self.data_provider = data_provider
        self.state = DashboardState()
        self.components: Dict[str, Component] = {}
        self.metrics_calculator = MetricsCalculator()
        
    def register_component(self, component: Component) -> None:
        """
        Register a component with the dashboard.
        
        Args:
            component: Component to register
        """
        self.components[component.component_id] = component
        
    def get_component(self, component_id: str) -> Optional[Component]:
        """
        Get a component by ID.
        
        Args:
            component_id: ID of the component to get
            
        Returns:
            Component if found, None otherwise
        """
        return self.components.get(component_id)
    
    def render_dashboard(self, format_type: str = 'text') -> str:
        """
        Render the complete dashboard.
        
        Args:
            format_type: Output format type (text, html, json)
            
        Returns:
            Rendered dashboard as a string
        """
        # Get context for data request
        context = {
            'level': self.state.navigation_context.level,
            'entity_id': self.state.navigation_context.entity_id,
            'breadcrumbs': self.state.navigation_context.get_breadcrumb_trail()
        }
        
        # Get data from provider
        data = self.data_provider.get_filtered_data(context, self.state.active_filters)
        
        # Calculate metrics
        metrics = self.metrics_calculator.calculate_metrics(data, self.state.selected_metrics)
        
        # Combine data and metrics
        dashboard_data = {
            'raw_data': data,
            'metrics': metrics,
            'context': context,
            'state': {
                'filters': self.state.active_filters,
                'preferences': self.state.view_preferences,
                'selected_entity': self.state.selected_entity
            }
        }
        
        # Render components
        rendered_components = {}
        for component_id, component in self.components.items():
            rendered_components[component_id] = component.render(dashboard_data, format_type)
        
        # Combine rendered components based on format
        if format_type == 'json':
            import json
            return json.dumps(rendered_components)
        elif format_type == 'html':
            # Simple HTML combination
            html = "<div class='dashboard'>\n"
            for component_id, content in rendered_components.items():
                html += f"<div class='component' id='{component_id}'>\n{content}\n</div>\n"
            html += "</div>"
            return html
        else:
            # Text format (default)
            result = "DASHBOARD\n=========\n\n"
            for component_id, content in rendered_components.items():
                result += f"--- {component_id} ---\n{content}\n\n"
            return result
        
    def navigate(self, level: str, entity_id: Optional[str] = None) -> None:
        """
        Navigate to a specific entity.
        
        Args:
            level: Level to navigate to
            entity_id: ID of the entity to navigate to
        """
        self.state.navigate_to(level, entity_id)
        
    def navigate_back(self) -> bool:
        """
        Navigate back to the parent context.
        
        Returns:
            True if navigation was successful, False if at root
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
        """Clear all filters."""
        self.state.clear_all_filters()
        
    def select_metrics(self, metrics: List[str]) -> None:
        """
        Select metrics to display.
        
        Args:
            metrics: List of metric names to display
        """
        self.state.selected_metrics = metrics 