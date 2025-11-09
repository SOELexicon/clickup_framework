"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/utils/error_formatter.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CLI Commands: Formats command errors for user display
    - ErrorHandler: Centralizes error message formatting
    - ValidationSystem: Formats validation errors consistently
    - TaskService: Reports task-specific errors
    - RelationshipService: Reports dependency errors
    - CoreManager: Formats general application errors

Purpose:
    Provides a comprehensive set of functions for formatting error messages
    across the application. Ensures consistent, user-friendly error presentation
    with appropriate color coding, context, and resolution suggestions. Handles
    different error categories (command errors, validation errors, task errors)
    with specialized formatting to maximize usability.

Requirements:
    - CRITICAL: Messages must be user-friendly and actionable
    - CRITICAL: Must format all errors consistently across the application
    - CRITICAL: Must include context information for debugging
    - Error formatting must support color for improved readability
    - Debug information must be conditionally displayed based on environment
    - Error codes must be prominently displayed when available
    - Must provide suggested actions where applicable

Error formatting utilities for the ClickUp JSON Manager.

This module provides utilities for formatting error messages in a 
consistent way across the application, with special handling for 
different error types and improved user-friendly messages.
"""

import os
import sys
import traceback
from typing import Optional, Dict, Any, List, Union

from refactor.utils.formatting import Color, colorize


def format_error_message(message: str, 
                        error_code: Optional[str] = None,
                        details: Optional[str] = None,
                        suggestions: Optional[List[str]] = None) -> str:
    """
    Format an error message in a consistent, user-friendly way.
    
    Args:
        message: The main error message
        error_code: Optional error code for reference
        details: Optional detailed description of the error
        suggestions: Optional list of suggestions to fix the error
        
    Returns:
        Formatted error message string
    """
    # Start with the main message
    error_text = colorize("ERROR: ", Color.RED) + message
    
    # Add error code if provided
    if error_code:
        error_text += f" [Code: {error_code}]"
    
    # Add details if provided
    if details:
        error_text += f"\n\n{details}"
    
    # Add suggestions if provided
    if suggestions and len(suggestions) > 0:
        error_text += "\n\nSuggestions:"
        for suggestion in suggestions:
            error_text += f"\n- {suggestion}"
    
    return error_text


def format_command_error(command_name: str, error: Exception) -> str:
    """
    Format an error that occurred during command execution.
    
    Args:
        command_name: Name of the command that failed
        error: The exception that was raised
        
    Returns:
        Formatted error message string
    """
    error_text = colorize(f"Command '{command_name}' failed: ", Color.RED)
    error_text += str(error)
    
    # Add traceback in debug mode
    if os.environ.get("DEBUG"):
        error_text += "\n\n" + "".join(traceback.format_exception(
            type(error), error, error.__traceback__))
    
    return error_text


def format_validation_error(validation_errors: Dict[str, str]) -> str:
    """
    Format validation errors for user input.
    
    Args:
        validation_errors: Dictionary of field names and error messages
        
    Returns:
        Formatted validation error message
    """
    if not validation_errors:
        return ""
    
    error_text = colorize("Validation errors:", Color.RED)
    
    for field, message in validation_errors.items():
        error_text += f"\n- {field}: {message}"
    
    return error_text


def format_task_error(task_id: str, 
                     error: str, 
                     task_name: Optional[str] = None) -> str:
    """
    Format an error related to a specific task.
    
    Args:
        task_id: ID of the task
        error: Error message
        task_name: Optional task name for more user-friendly output
        
    Returns:
        Formatted task error message
    """
    if task_name:
        error_text = colorize(f"Task '{task_name}' (ID: {task_id}) error: ", Color.RED)
    else:
        error_text = colorize(f"Task {task_id} error: ", Color.RED)
    
    error_text += error
    return error_text


def format_dependency_error(task_id: str, 
                          dependency_id: str,
                          error: str,
                          task_name: Optional[str] = None,
                          dependency_name: Optional[str] = None) -> str:
    """
    Format an error related to a task dependency.
    
    Args:
        task_id: ID of the task
        dependency_id: ID of the dependency
        error: Error message
        task_name: Optional task name
        dependency_name: Optional dependency name
        
    Returns:
        Formatted dependency error message
    """
    if task_name and dependency_name:
        error_text = colorize(
            f"Dependency error between task '{task_name}' and '{dependency_name}': ", 
            Color.RED
        )
    else:
        error_text = colorize(
            f"Dependency error between task {task_id} and {dependency_id}: ", 
            Color.RED
        )
    
    error_text += error
    return error_text 