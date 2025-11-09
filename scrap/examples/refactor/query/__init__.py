"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/query/__init__.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - SearchSystem: Uses TQL for advanced task filtering
    - CLI Search Command: Enables complex query capabilities
    - TaskService: Filters task collections using TQL
    - RESTfulAPI: Exposes query functionality through API endpoints
    - DashboardManager: Filters data for visualizations
    - RelationshipResolver: Queries task relationships

Purpose:
    Implements a Task Query Language (TQL) for filtering and querying tasks
    using SQL-like syntax. Provides a flexible and powerful way to filter task
    collections based on field values, logical conditions, and relationships.
    Supports complex expressions, nested queries, and multiple operators.

Requirements:
    - CRITICAL: Must be secure against injection attacks
    - CRITICAL: Must handle syntax errors gracefully with useful error messages
    - CRITICAL: Query parsing and evaluation must be optimized for performance
    - Must support all standard comparison and logical operators
    - Must provide consistent behavior across different task field types
    - Must validate field references against the task schema

Task Query Language (TQL) package

This package provides a query language for tasks in the ClickUp JSON Manager.
It allows filtering and querying tasks using a SQL-like syntax.

Example usage:
    from refactor.query import TQL
    
    # Create a TQL instance
    tql = TQL()
    
    # Filter tasks with a query
    filtered_tasks = tql.filter_tasks(tasks, "status == 'to do' AND priority > 2")
"""

from .tql import TQL
from .operators import Operator, FieldOperator, ComparisonOperator, LogicalOperator, OperatorType
from .parser import TQLParser
from .evaluator import TQLEvaluator

__all__ = [
    'TQL',
    'Operator',
    'FieldOperator',
    'ComparisonOperator',
    'LogicalOperator',
    'OperatorType',
    'TQLParser',
    'TQLEvaluator'
] 