"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/query/operators.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - TQLParser: Constructs operator trees during query parsing
    - TQLEvaluator: Evaluates operators against tasks
    - TQL: Uses operators to build and explain query trees
    - QueryBuilder: Programmatically constructs operator trees
    - SearchSystem: Leverages operator model for advanced search
    - ExplanationGenerator: Creates human-readable query descriptions

Purpose:
    Implements the operator model for Task Query Language (TQL), providing
    the core building blocks used to represent queries as expression trees.
    Defines the base Operator class and concrete implementations for field
    access, comparisons, and logical operations. Provides the evaluation
    functionality that powers the query engine.

Requirements:
    - CRITICAL: Operators must handle type coercion consistently
    - CRITICAL: String comparisons must be case-insensitive by default
    - CRITICAL: Evaluation must be optimized for performance
    - Operators must provide consistent behavior across all data types
    - Field mapping must be flexible for backward compatibility
    - Operator trees must be serializable for debugging and storage
    - CRITICAL: Must handle null/None values gracefully

Query Language Operators

This module defines the operators used in the Task Query Language.
It includes:
- Base Operator class for all operators
- Field operators for accessing task fields
- Comparison operators (equals, not equals, greater than, etc.)
- Logical operators (AND, OR, NOT)
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union, Callable
import operator as op

class OperatorType(Enum):
    """Types of operators supported in the query language"""
    FIELD = auto()        # Field access (e.g., status, priority)
    COMPARISON = auto()   # Comparison (e.g., ==, !=, >, <)
    LOGICAL = auto()      # Logical operations (e.g., AND, OR, NOT)
    FUNCTION = auto()     # Function calls (e.g., contains(), exists())

class Operator(ABC):
    """Base class for all operators in the query language"""
    
    def __init__(self, operator_type: OperatorType):
        """
        Initialize an operator.
        
        Args:
            operator_type: The type of operator
        """
        self.operator_type = operator_type
    
    @abstractmethod
    def evaluate(self, *args, **kwargs) -> Any:
        """
        Evaluate the operator with the given arguments.
        
        Returns:
            Result of the operator evaluation
        """
        pass

class FieldOperator(Operator):
    """Operator for accessing fields from a task"""
    
    # Field mappings from query fields to task fields
    FIELD_MAPPINGS = {
        'status': 'status',
        'type': 'task_type',
        'priority': 'priority',
        'tag': 'tags',
        'tags': 'tags',
        'name': 'name',
        'description': 'description',
        'author': 'author',  # Maps to comment authors
        'id': 'id',
        'parent': 'parent_id',
        'list': 'list_name',
        'folder': 'folder_name',
        'space': 'space_name',
        'assignee': 'assignee',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
        'due_date': 'due_date'
    }
    
    def __init__(self, field_name: str):
        """
        Initialize a field operator.
        
        Args:
            field_name: Name of the field to access
        """
        super().__init__(OperatorType.FIELD)
        self.field_name = field_name
    
    def evaluate(self, task: Dict[str, Any]) -> Any:
        """
        Evaluate the field operator by retrieving the field value from the task.
        
        Args:
            task: The task dictionary to access
            
        Returns:
            The value of the specified field from the task
        """
        # Map the field name to the actual task field
        mapped_field = self.FIELD_MAPPINGS.get(self.field_name.lower(), self.field_name)
        
        # Special handling for tags (treat as a list)
        if mapped_field == 'tags':
            return task.get(mapped_field, [])
            
        # Special handling for comments (return list of authors)
        elif mapped_field == 'author':
            return [c.get('Author', '').lower() for c in task.get('comments', [])]
            
        # Standard field access
        value = task.get(mapped_field)
        
        # Ensure consistent case for string comparisons
        if isinstance(value, str):
            return value.lower()
            
        return value
        
    def __str__(self) -> str:
        return f"Field({self.field_name})"

class ComparisonOperator(Operator):
    """Operator for comparisons between values"""
    
    @staticmethod
    def _evaluate_in(a: Any, b: Any) -> bool:
        """
        Custom implementation of 'in' operator with enhanced behavior.
        
        Args:
            a: Left operand (value to check or container)
            b: Right operand (container to check in or value)
            
        Returns:
            True if a is in b or b is in a, with special handling for different types
        """
        # Try both directions and see if either works
        # This allows both "value in list" and "list in value" syntax
        
        try:
            # First try: a in b (standard direction)
            # String in string (case-insensitive)
            if isinstance(a, str) and isinstance(b, str):
                return a.lower() in b.lower()
                
            # Value in list (case-insensitive for strings)
            elif isinstance(b, (list, tuple)):
                if isinstance(a, str):
                    a_lower = a.lower()
                    for item in b:
                        if isinstance(item, str) and a_lower == item.lower():
                            return True
                        elif a == item:
                            return True
                    return False
                else:
                    return a in b
            
            # Standard 'in' check
            return a in b
            
        except (TypeError, ValueError):
            try:
                # Second try: b in a (reversed direction)
                # This handles the case when the field is a list (e.g., tags)
                # and we want to check if a value is in the list
                
                # String in string (case-insensitive)
                if isinstance(b, str) and isinstance(a, str):
                    return b.lower() in a.lower()
                    
                # Value in list (case-insensitive for strings)
                elif isinstance(a, (list, tuple)):
                    if isinstance(b, str):
                        b_lower = b.lower()
                        for item in a:
                            if isinstance(item, str) and b_lower == item.lower():
                                return True
                            elif b == item:
                                return True
                        return False
                    else:
                        return b in a
                
                # Standard 'in' check
                return b in a
                
            except (TypeError, ValueError) as e:
                # Both directions failed
                print(f"Warning: Comparison error ({a} in {b}): {e}")
                return False
    
    # Map of operator symbols to functions
    OPERATORS = {
        # Standard comparisons
        '==': op.eq,
        '!=': op.ne,
        '>': op.gt,
        '>=': op.ge,
        '<': op.lt,
        '<=': op.le,
        
        # Membership checks
        'in': lambda a, b: ComparisonOperator._evaluate_in(a, b),
        'not in': lambda a, b: not ComparisonOperator._evaluate_in(a, b),
        
        # Text-specific operations
        'contains': lambda a, b: b.lower() in a.lower() if isinstance(a, str) and isinstance(b, str) else False,
        'starts_with': lambda a, b: a.lower().startswith(b.lower()) if isinstance(a, str) and isinstance(b, str) else False,
        'ends_with': lambda a, b: a.lower().endswith(b.lower()) if isinstance(a, str) and isinstance(b, str) else False,
        
        # Existence check
        'exists': lambda a, _: bool(a),
        'is': lambda a, b: a is b,
        'is not': lambda a, b: a is not b
    }
    
    def __init__(self, operator_symbol: str):
        """
        Initialize a comparison operator.
        
        Args:
            operator_symbol: Symbol representing the comparison (e.g., '==', '!=')
        """
        super().__init__(OperatorType.COMPARISON)
        self.operator_symbol = operator_symbol
        
        if operator_symbol not in self.OPERATORS:
            raise ValueError(f"Unsupported comparison operator: {operator_symbol}")
            
        self.operator_func = self.OPERATORS[operator_symbol]
    
    def evaluate(self, left: Any, right: Any) -> bool:
        """
        Evaluate the comparison between left and right operands.
        
        Args:
            left: Left operand of the comparison
            right: Right operand of the comparison
            
        Returns:
            Result of the comparison (True or False)
        """
        try:
            # Special handling for 'in' with lists/strings
            if self.operator_symbol in ('in', 'not in'):
                return self.operator_func(left, right)
                
            # Special handling for 'exists' (only uses left operand)
            if self.operator_symbol == 'exists':
                return self.operator_func(left, None)
                
            # Ensure consistent case for string comparisons
            if isinstance(left, str) and isinstance(right, str):
                return self.operator_func(left.lower(), right.lower())
                
            # Try numeric comparison if both values can be converted
            try:
                if (isinstance(left, (int, float, str)) and 
                    isinstance(right, (int, float, str)) and
                    self.operator_symbol in ('==', '!=', '>', '>=', '<', '<=')):
                    left_num = float(left) if str(left).replace('.','',1).isdigit() else left
                    right_num = float(right) if str(right).replace('.','',1).isdigit() else right
                    if isinstance(left_num, (int, float)) and isinstance(right_num, (int, float)):
                        return self.operator_func(left_num, right_num)
            except (ValueError, TypeError):
                # Fallback to original types if numeric conversion fails
                pass
                
            # Standard comparison
            return self.operator_func(left, right)
            
        except (TypeError, ValueError) as e:
            # If comparison fails (e.g., incompatible types), assume False
            print(f"Warning: Comparison error ({left} {self.operator_symbol} {right}): {e}")
            return False
            
    def __str__(self) -> str:
        return f"Comparison({self.operator_symbol})"

class LogicalOperator(Operator):
    """Operator for logical operations (AND, OR, NOT)"""
    
    # Map of operator names to functions
    OPERATORS = {
        'AND': lambda a, b: a and b,
        'OR': lambda a, b: a or b,
        'NOT': lambda a: not a
    }
    
    def __init__(self, operator_name: str):
        """
        Initialize a logical operator.
        
        Args:
            operator_name: Name of the logical operator ('AND', 'OR', 'NOT')
        """
        super().__init__(OperatorType.LOGICAL)
        self.operator_name = operator_name.upper()
        
        if self.operator_name not in self.OPERATORS:
            raise ValueError(f"Unsupported logical operator: {operator_name}")
            
        self.operator_func = self.OPERATORS[self.operator_name]
    
    def evaluate(self, *operands: Any) -> bool:
        """
        Evaluate the logical operation on the operands.
        
        Args:
            *operands: Operands for the logical operation
            
        Returns:
            Result of the logical operation
        """
        if self.operator_name == 'NOT':
            if len(operands) != 1:
                raise ValueError(f"NOT operator requires exactly 1 operand, got {len(operands)}")
            return self.operator_func(operands[0])
        else:
            if len(operands) != 2:
                raise ValueError(f"{self.operator_name} operator requires exactly 2 operands, got {len(operands)}")
            return self.operator_func(operands[0], operands[1])
            
    def __str__(self) -> str:
        return f"Logical({self.operator_name})" 