"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/query/tql.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CLI Search Command: Main entry point for task filtering in CLI
    - SearchSystem: Core query executor for search functionality
    - RESTfulAPI: Exposes TQL filtering for API consumers
    - SavedSearchManager: Uses for query parsing and validation
    - QueryBuilder: Programmatically constructs TQL queries
    - AutocompleteSystem: Provides query syntax assistance

Purpose:
    Provides the main entry point and interface for the Task Query Language (TQL)
    system. This facade class integrates the parser, operator model, and evaluator
    components into a cohesive API for filtering tasks using SQL-like query syntax.
    Includes utilities for parsing, evaluating, filtering, and explaining queries.

Requirements:
    - CRITICAL: Must catch and translate all syntax errors into clear messages
    - CRITICAL: Must efficiently filter large task collections
    - CRITICAL: String queries must be validated before execution
    - Query parsing must be isolated from evaluation for security
    - Must support both string queries and pre-compiled operator trees
    - Must provide descriptive error messages for debugging
    - Must maintain consistent API behavior across version changes

Task Query Language (TQL)

This module provides the main interface for working with the Task Query
Language, including parsing, evaluating, and filtering tasks.

Example usage:
    # Create a TQL instance
    tql = TQL()
    
    # Parse a query
    query = tql.parse("status == 'to do' AND priority > 2")
    
    # Evaluate a single task
    matches = tql.evaluate(query, task)
    
    # Filter a list of tasks
    filtered_tasks = tql.filter_tasks(tasks, "status == 'to do' AND priority > 2")
"""

from typing import Any, Dict, List, Optional, Union

from .parser import TQLParser
from .evaluator import TQLEvaluator
from .operators import Operator

class TQL:
    """
    Main interface for Task Query Language operations.
    Provides methods for parsing, evaluating, and filtering tasks with TQL queries.
    """
    
    def __init__(self):
        """Initialize the TQL interface with parser and evaluator"""
        self.parser = TQLParser()
        self.evaluator = TQLEvaluator()
    
    def parse(self, query_str: str) -> Operator:
        """
        Parse a TQL query string into an operator tree.
        
        Args:
            query_str: The TQL query string to parse
            
        Returns:
            Root operator of the parsed expression tree
            
        Raises:
            ValueError: If there's a syntax error in the query
        """
        try:
            return self.parser.parse(query_str)
        except Exception as e:
            raise ValueError(f"Error parsing TQL query: {e}")
    
    def evaluate(self, query: Union[str, Operator], task: Dict[str, Any]) -> bool:
        """
        Evaluate a query against a task to determine if it matches.
        
        Args:
            query: Either a TQL query string or a parsed operator tree
            task: The task dictionary to evaluate against
            
        Returns:
            True if the task matches the query criteria, False otherwise
            
        Raises:
            ValueError: If there's an error parsing or evaluating the query
        """
        # If query is a string, parse it first
        if isinstance(query, str):
            query = self.parse(query)
            
        try:
            return self.evaluator.evaluate(query, task)
        except Exception as e:
            raise ValueError(f"Error evaluating TQL query: {e}")
    
    def filter_tasks(self, tasks: List[Dict[str, Any]], query: Union[str, Operator]) -> List[Dict[str, Any]]:
        """
        Filter a list of tasks based on a TQL query.
        
        Args:
            tasks: List of task dictionaries to filter
            query: Either a TQL query string or a parsed operator tree
            
        Returns:
            List of tasks that match the query criteria
            
        Raises:
            ValueError: If there's an error parsing or evaluating the query
        """
        # If query is a string, parse it first
        if isinstance(query, str):
            query = self.parse(query)
            
        # Filter tasks based on query
        return [task for task in tasks if self.evaluate(query, task)]
        
    def explain(self, query_str: str) -> str:
        """
        Generate a human-readable explanation of a TQL query.
        
        Args:
            query_str: The TQL query string to explain
            
        Returns:
            Human-readable explanation of the query
            
        Raises:
            ValueError: If there's a syntax error in the query
        """
        # Parse the query
        query = self.parse(query_str)
        
        # Generate explanation based on operator tree
        return self._explain_operator(query, 0)
    
    def _explain_operator(self, operator: Operator, indent_level: int) -> str:
        """
        Generate a human-readable explanation of an operator.
        
        Args:
            operator: The operator to explain
            indent_level: Current indentation level for formatting
            
        Returns:
            Human-readable explanation of the operator
        """
        from .operators import ComparisonOperator, FieldOperator, LogicalOperator
        
        indent = "  " * indent_level
        
        if isinstance(operator, FieldOperator):
            return f"{indent}Access field '{operator.field_name}'"
            
        elif isinstance(operator, ComparisonOperator):
            left = self._explain_operand(operator._left, indent_level + 1)
            right = self._explain_operand(operator._right, indent_level + 1)
            return f"{indent}Compare using '{operator.operator_symbol}':\n{left}\n{right}"
            
        elif isinstance(operator, LogicalOperator):
            result = f"{indent}Logical {operator.operator_name}:"
            for operand in operator._operands:
                result += f"\n{self._explain_operator(operand, indent_level + 1)}"
            return result
            
        else:
            return f"{indent}Unknown operator: {operator}"
    
    def _explain_operand(self, operand: Any, indent_level: int) -> str:
        """
        Generate a human-readable explanation of an operand.
        
        Args:
            operand: The operand to explain (operator or literal)
            indent_level: Current indentation level for formatting
            
        Returns:
            Human-readable explanation of the operand
        """
        from .operators import Operator
        
        indent = "  " * indent_level
        
        if isinstance(operand, Operator):
            return self._explain_operator(operand, indent_level)
        else:
            # Format literal value
            if isinstance(operand, str):
                return f"{indent}Value: '{operand}'"
            elif operand is None:
                return f"{indent}Value: null"
            elif isinstance(operand, list):
                values = ", ".join(str(v) for v in operand)
                return f"{indent}List: [{values}]"
            else:
                return f"{indent}Value: {operand}" 