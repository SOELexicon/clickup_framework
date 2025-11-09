"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/query/parser.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - TQL: Entry point for parsing query strings
    - SearchSystem: Parses user-provided search queries
    - SavedSearchManager: Validates and parses saved searches
    - AutocompleteSystem: Parses partial queries for completion
    - QueryBuilder: Provides programmatic query construction
    - RESTfulAPI: Parses query parameters from API requests

Purpose:
    Implements a parser for the Task Query Language (TQL) that converts string
    query expressions into executable operator trees. Uses a recursive descent
    parser with Pratt parsing techniques to handle operator precedence. Includes
    tokenization, syntax validation, and expression tree construction.

Requirements:
    - CRITICAL: Must validate syntax before execution for security
    - CRITICAL: Must provide clear, specific error messages for syntax errors
    - CRITICAL: Must handle all supported operators with correct precedence
    - CRITICAL: Must properly escape string literals
    - Parsing must be optimized for performance with large queries
    - Parser must support future extension with new operators
    - Must handle nested expressions with unlimited depth

Task Query Language Parser

This module provides functionality to parse Task Query Language (TQL) expressions
into operator trees that can be evaluated against tasks.
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from enum import Enum, auto

from .operators import ComparisonOperator, FieldOperator, LogicalOperator, Operator, OperatorType

class TokenType(Enum):
    """Types of tokens in the TQL parser"""
    FIELD = auto()          # Field identifier (e.g., status, priority)
    OPERATOR = auto()       # Operator (e.g., ==, !=, >, <)
    LITERAL = auto()        # Literal value (e.g., "complete", 3)
    LOGICAL = auto()        # Logical operator (AND, OR, NOT)
    LPAREN = auto()         # Left parenthesis
    RPAREN = auto()         # Right parenthesis
    FUNCTION = auto()       # Function name (e.g., contains, exists)
    COMMA = auto()          # Comma (for function arguments)

class Token:
    """Token for TQL parsing"""
    
    def __init__(self, token_type: TokenType, value: str):
        self.type = token_type
        self.value = value
        
    def __str__(self) -> str:
        return f"Token({self.type}, '{self.value}')"
        
    def __repr__(self) -> str:
        return self.__str__()

class TQLParser:
    """Parser for Task Query Language expressions"""
    
    # Operator precedence for parsing (higher value = higher precedence)
    PRECEDENCE = {
        'NOT': 5,
        '==': 4, '!=': 4, '>': 4, '>=': 4, '<': 4, '<=': 4, 
        'in': 4, 'not in': 4, 'contains': 4, 'starts_with': 4, 'ends_with': 4, 
        'exists': 4, 'is': 4, 'is not': 4,
        'AND': 3,
        'OR': 2,
    }
    
    # Regex patterns for tokenizing
    PATTERNS = [
        (r'\s+', None),  # Skip whitespace
        (r'[()]', lambda m: Token(TokenType.LPAREN if m.group(0) == '(' else TokenType.RPAREN, m.group(0))),
        (r',', lambda m: Token(TokenType.COMMA, m.group(0))),
        (r'(==|!=|>=|<=|>|<)', lambda m: Token(TokenType.OPERATOR, m.group(0))),
        (r'(not\s+in|in|is\s+not|is|contains|starts_with|ends_with|exists)', 
         lambda m: Token(TokenType.OPERATOR, m.group(0).lower())),
        (r'(AND|OR|NOT|and|or|not)\b', lambda m: Token(TokenType.LOGICAL, m.group(0).upper())),
        (r'"([^"\\]|\\"|\\\\)*"', lambda m: Token(TokenType.LITERAL, m.group(0)[1:-1].replace('\\"', '"'))),
        (r"'([^'\\]|\\'|\\\\)*'", lambda m: Token(TokenType.LITERAL, m.group(0)[1:-1].replace("\\'", "'"))),
        (r'\b(true|false)\b', lambda m: Token(TokenType.LITERAL, m.group(0).lower() == 'true')),
        (r'\b(null|none)\b', lambda m: Token(TokenType.LITERAL, None)),
        (r'\b\d+\.\d+\b', lambda m: Token(TokenType.LITERAL, float(m.group(0)))),
        (r'\b\d+\b', lambda m: Token(TokenType.LITERAL, int(m.group(0)))),
        (r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', lambda m: Token(TokenType.FIELD, m.group(0))),
    ]
    
    def __init__(self):
        """Initialize the TQL parser"""
        self.tokens: List[Token] = []
        self.pos = 0
    
    def tokenize(self, query: str) -> List[Token]:
        """
        Convert a TQL query string into tokens.
        
        Args:
            query: The TQL query string to tokenize
            
        Returns:
            List of tokens
        """
        tokens = []
        pos = 0
        
        while pos < len(query):
            for pattern, token_func in self.PATTERNS:
                match = re.match(pattern, query[pos:], re.DOTALL)
                if match:
                    if token_func:  # Skip whitespace
                        tokens.append(token_func(match))
                    pos += match.end()
                    break
            else:
                # If no pattern matches, raise error
                raise ValueError(f"Syntax error in query at position {pos}: '{query[pos:pos+10]}...'")
        
        return tokens
    
    def parse(self, query: str) -> Operator:
        """
        Parse a TQL query string into an operator tree.
        
        Args:
            query: The TQL query string to parse
            
        Returns:
            Root operator of the parsed expression tree
        """
        self.tokens = self.tokenize(query)
        self.pos = 0
        
        if not self.tokens:
            raise ValueError("Empty query")
            
        return self._parse_expression()
    
    def _current_token(self) -> Optional[Token]:
        """Get the current token"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def _consume_token(self) -> Optional[Token]:
        """Consume and return the current token"""
        token = self._current_token()
        if token:
            self.pos += 1
        return token
    
    def _peek_token(self) -> Optional[Token]:
        """Look ahead at the next token without consuming it"""
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return None
    
    def _parse_expression(self, precedence: int = 0) -> Operator:
        """
        Parse an expression with a given precedence.
        
        Args:
            precedence: The minimum precedence to consider
            
        Returns:
            Root operator of the parsed expression
        """
        # Parse prefix expression
        left = self._parse_prefix()
        
        # Handle infix expressions (binary operators)
        while True:
            token = self._current_token()
            
            # End of expression
            if not token:
                break
                
            # End of subexpression (closing parenthesis, comma)
            if token.type == TokenType.RPAREN or token.type == TokenType.COMMA:
                break
                
            # Parse infix expression if operator has higher precedence
            if token.type in (TokenType.OPERATOR, TokenType.LOGICAL):
                current_precedence = self.PRECEDENCE.get(token.value, 0)
                if current_precedence <= precedence:
                    break
                
                left = self._parse_infix(left, current_precedence)
            else:
                break
                
        return left
    
    def _parse_prefix(self) -> Operator:
        """
        Parse a prefix expression (field, literal, NOT, parenthesized expression).
        
        Returns:
            Operator representing the prefix expression
        """
        token = self._consume_token()
        
        if not token:
            raise ValueError("Unexpected end of query")
            
        if token.type == TokenType.FIELD:
            # Field identifier
            field_name = token.value
            
            # Check if it's actually a function call
            peek = self._current_token()
            if peek and peek.type == TokenType.LPAREN:
                # TODO: Implement function calls
                raise NotImplementedError(f"Function calls not yet implemented: {field_name}")
                
            return FieldOperator(field_name)
            
        elif token.type == TokenType.LITERAL:
            # Literal values can't be standalone expressions
            raise ValueError(f"Unexpected literal value '{token.value}' without field and operator")
            
        elif token.type == TokenType.LOGICAL and token.value == 'NOT':
            # NOT operator
            expr = self._parse_expression(self.PRECEDENCE['NOT'])
            return LogicalOperator('NOT')._with_operands([expr])
            
        elif token.type == TokenType.LPAREN:
            # Parenthesized expression
            expr = self._parse_expression()
            
            # Expect closing parenthesis
            if not self._current_token() or self._current_token().type != TokenType.RPAREN:
                raise ValueError("Missing closing parenthesis in query")
                
            self._consume_token()  # Consume ')'
            return expr
            
        else:
            raise ValueError(f"Unexpected token in query: {token}")
    
    def _parse_infix(self, left: Operator, precedence: int) -> Operator:
        """
        Parse an infix expression (e.g., field == value).
        
        Args:
            left: The left operand (already parsed)
            precedence: The precedence of the current operator
            
        Returns:
            Operator representing the infix expression
        """
        token = self._consume_token()
        
        if not token:
            raise ValueError("Unexpected end of query")
            
        if token.type == TokenType.OPERATOR:
            # Comparison operator
            op = ComparisonOperator(token.value)
            
            # Parse right operand
            right_token = self._consume_token()
            
            # Extract literal values or field reference
            if right_token and right_token.type == TokenType.LITERAL:
                right_value = right_token.value
                return self._create_comparison(op, left, right_value)
                
            elif right_token and right_token.type == TokenType.FIELD:
                right_field = FieldOperator(right_token.value)
                return self._create_comparison(op, left, right_field)
                
            elif right_token and right_token.type == TokenType.LPAREN:
                # List of values in parentheses
                values = self._parse_parenthesized_values()
                return self._create_comparison(op, left, values)
                
            else:
                raise ValueError(f"Expected value after operator {token.value}")
                
        elif token.type == TokenType.LOGICAL:
            # Logical operator (AND, OR)
            op = LogicalOperator(token.value)
            
            # Parse right operand with the same precedence
            right = self._parse_expression(precedence)
            
            # Create logical operation
            return self._create_logical(op, left, right)
            
        else:
            raise ValueError(f"Unexpected token in query: {token}")
    
    def _parse_parenthesized_values(self) -> List[Any]:
        """
        Parse a comma-separated list of values in parentheses.
        
        Returns:
            List of values
        """
        values = []
        
        # Handle empty list
        if self._current_token() and self._current_token().type == TokenType.RPAREN:
            self._consume_token()
            return values
            
        while True:
            token = self._current_token()
            
            if not token:
                raise ValueError("Unexpected end of query in list")
                
            if token.type == TokenType.LITERAL:
                values.append(self._consume_token().value)
            elif token.type == TokenType.FIELD:
                values.append(FieldOperator(self._consume_token().value))
            else:
                raise ValueError(f"Expected value in list, got {token}")
                
            # Check for comma or closing parenthesis
            token = self._current_token()
            
            if not token:
                raise ValueError("Unexpected end of query in list")
                
            if token.type == TokenType.RPAREN:
                self._consume_token()
                break
                
            if token.type != TokenType.COMMA:
                raise ValueError(f"Expected comma or closing parenthesis in list, got {token}")
                
            self._consume_token()  # Consume ','
            
        return values
    
    def _create_comparison(self, op: ComparisonOperator, left: Any, right: Any) -> ComparisonOperator:
        """
        Create a comparison operation node with operands.
        
        Args:
            op: Comparison operator
            left: Left operand
            right: Right operand
            
        Returns:
            ComparisonOperator with operands
        """
        op._left = left
        op._right = right
        return op
    
    def _create_logical(self, op: LogicalOperator, left: Operator, right: Operator) -> LogicalOperator:
        """
        Create a logical operation node with operands.
        
        Args:
            op: Logical operator
            left: Left operand
            right: Right operand
            
        Returns:
            LogicalOperator with operands
        """
        op._operands = [left, right]
        return op

# Add monkey patching to extend operator classes with operand storage
def _monkey_patch_operators():
    """Add convenience methods to operator classes for operand storage"""
    
    # Add operands storage to ComparisonOperator
    ComparisonOperator._left = None
    ComparisonOperator._right = None
    
    def _with_operands(self, operands):
        """Set operands and return self for chaining"""
        self._left, self._right = operands
        return self
    
    ComparisonOperator._with_operands = _with_operands
    
    # Add operands storage to LogicalOperator
    LogicalOperator._operands = []
    
    def _with_operands(self, operands):
        """Set operands and return self for chaining"""
        self._operands = operands
        return self
    
    LogicalOperator._with_operands = _with_operands

# Run monkey patching when module is imported
_monkey_patch_operators() 