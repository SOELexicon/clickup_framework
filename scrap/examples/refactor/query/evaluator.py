"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/query/evaluator.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - TQL: Uses evaluator to match tasks against parsed queries
    - SearchSystem: Core component for filter evaluation
    - QueryExecutor: Handles batch evaluation for performance
    - DashboardDataProvider: Filters visualization data
    - RESTfulAPI: Powers query parameter evaluation
    - SavedSearchExecutor: Runs saved searches against tasks

Purpose:
    Implements the evaluation engine for the Task Query Language (TQL).
    Takes parsed operator trees and evaluates them against task data to
    determine if tasks match the query criteria. Implements short-circuit
    evaluation for logical operators and handles the recursive evaluation
    of the expression tree.

Requirements:
    - CRITICAL: Must implement optimized short-circuit evaluation
    - CRITICAL: Must handle all supported operator types correctly
    - CRITICAL: Must ensure consistent and predictable evaluation behavior
    - Must properly propagate exceptions with meaningful context
    - Must minimize memory allocation during evaluation
    - Must handle large operator trees efficiently
    - Must guarantee thread safety during evaluation

Task Query Language Evaluator

This module provides functionality to evaluate parsed TQL expressions
against tasks to determine if they match query criteria.
"""

from typing import Any, Dict, List, Optional, Union

from .operators import ComparisonOperator, FieldOperator, LogicalOperator, Operator, OperatorType

class TQLEvaluator:
    """Evaluator for Task Query Language expressions"""
    
    def __init__(self):
        """Initialize the TQL evaluator"""
        pass
    
    def evaluate(self, operator: Operator, task: Dict[str, Any]) -> bool:
        """
        Evaluate a parsed query expression against a task.
        
        Args:
            operator: The root operator of the parsed expression
            task: The task dictionary to evaluate against
            
        Returns:
            True if the task matches the query criteria, False otherwise
        """
        return self._evaluate_operator(operator, task)
    
    def _evaluate_operator(self, operator: Operator, task: Dict[str, Any]) -> Any:
        """
        Recursively evaluate an operator against a task.
        
        Args:
            operator: The operator to evaluate
            task: The task dictionary to evaluate against
            
        Returns:
            Result of evaluating the operator against the task
        """
        if isinstance(operator, FieldOperator):
            return operator.evaluate(task)
            
        elif isinstance(operator, ComparisonOperator):
            return self._evaluate_comparison(operator, task)
            
        elif isinstance(operator, LogicalOperator):
            return self._evaluate_logical(operator, task)
            
        else:
            raise ValueError(f"Unsupported operator type: {type(operator)}")
    
    def _evaluate_comparison(self, operator: ComparisonOperator, task: Dict[str, Any]) -> bool:
        """
        Evaluate a comparison operator against a task.
        
        Args:
            operator: The comparison operator to evaluate
            task: The task dictionary to evaluate against
            
        Returns:
            Result of the comparison (True or False)
        """
        # Evaluate left operand (typically a field access)
        left = self._evaluate_operand(operator._left, task)
        
        # Evaluate right operand (could be literal or another field)
        right = self._evaluate_operand(operator._right, task)
        
        # Evaluate the comparison
        return operator.evaluate(left, right)
    
    def _evaluate_logical(self, operator: LogicalOperator, task: Dict[str, Any]) -> bool:
        """
        Evaluate a logical operator against a task.
        
        Args:
            operator: The logical operator to evaluate
            task: The task dictionary to evaluate against
            
        Returns:
            Result of the logical operation (True or False)
        """
        if operator.operator_name == 'AND':
            # Short-circuit AND
            for operand in operator._operands:
                if not self._evaluate_operator(operand, task):
                    return False
            return True
            
        elif operator.operator_name == 'OR':
            # Short-circuit OR
            for operand in operator._operands:
                if self._evaluate_operator(operand, task):
                    return True
            return False
            
        elif operator.operator_name == 'NOT':
            # NOT takes only one operand
            return not self._evaluate_operator(operator._operands[0], task)
            
        else:
            raise ValueError(f"Unsupported logical operator: {operator.operator_name}")
    
    def _evaluate_operand(self, operand: Any, task: Dict[str, Any]) -> Any:
        """
        Evaluate an operand, which may be an operator or a literal value.
        
        Args:
            operand: The operand to evaluate (operator or literal)
            task: The task dictionary for operator evaluation
            
        Returns:
            Result of evaluating the operand
        """
        if isinstance(operand, Operator):
            return self._evaluate_operator(operand, task)
        else:
            # Literal value, return as is
            return operand 