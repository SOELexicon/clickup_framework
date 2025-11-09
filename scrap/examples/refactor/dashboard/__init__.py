"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/dashboard/__init__.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CLI: Imports dashboard components and managers for interactive displays
    - CoreManager: Initializes dashboard visualization capabilities
    - RESTfulAPI: Exposes dashboard data through API endpoints
    - TaskService: Provides data for dashboard visualization

Purpose:
    Dashboard Module provides a comprehensive visualization and reporting system
    for task data, metrics, and project insights. It implements various visualization
    components and data providers to generate interactive dashboards with drill-down
    capabilities.

Requirements:
    - Must maintain separation between data providers and visualization components
    - CRITICAL: Must not modify task data directly through dashboard interactions
    - CRITICAL: Data providers must implement caching for performance optimization
    - CRITICAL: All components must gracefully handle missing or invalid data
    - Must support both terminal-based and web-based display contexts

Dashboard Module

This module provides the dashboard visualization and reporting functionality.
"""

from .dashboard_component import (
    Component,
    DataProvider,
    NavigationContext,
    DashboardState
)

from .components import (
    MetricComponent,
    BarChartComponent,
    PieChartComponent,
    TableComponent,
    TimelineComponent,
    TaskHierarchyComponent,
    DashboardLayout
)

from .data_provider import TaskDataProvider
from .dashboard_manager import DashboardManager

__all__ = [
    # Base classes
    'Component',
    'DataProvider',
    'NavigationContext',
    'DashboardState',
    
    # Component implementations
    'MetricComponent',
    'BarChartComponent',
    'PieChartComponent',
    'TableComponent',
    'TimelineComponent',
    'TaskHierarchyComponent',
    'DashboardLayout',
    
    # Data providers
    'TaskDataProvider',
    
    # Managers
    'DashboardManager'
]
