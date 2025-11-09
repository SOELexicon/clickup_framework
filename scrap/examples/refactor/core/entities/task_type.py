"""
Task: tsk_bf28d342 - Update CLI Module Comments
Document: refactor/core/entities/task_type.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (current)
    - tsk_7c9d4e8a - Task Command Implementation (related)

Used By:
    - TaskEntity: For defining task types
    - CLI Commands: For validating and displaying task types
    - Task Service: For handling task type operations
    - UI Components: For rendering task types with appropriate colors

Purpose:
    Provides a centralized definition of task types with color support and 
    extensibility. Enables consistent handling of task types across the
    application with proper color coding for improved visual distinction.

Requirements:
    - Must maintain backward compatibility with existing task types
    - Must provide color definitions for all task types
    - Must support easy extension with new task types
    - Must handle conversion between string and enum values
    - CRITICAL: Must not break existing code that uses TaskType
    - CRITICAL: Must provide consistent color mapping for UI elements

Parameters:
    N/A - This is a module file

Returns:
    N/A - This is a module file

Changes:
    - v1: Initial implementation with basic task types and color support
"""
from enum import Enum
from typing import Dict, List, Optional, Union, Tuple, Any

from refactor.utils.colors import TextColor, colorize


class TaskType(Enum):
    """
    Enumeration of possible task types with color support.
    
    Each task type has a corresponding string value and color for display purposes.
    """
    
    TASK = "task"
    BUG = "bug"
    FEATURE = "feature"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    ENHANCEMENT = "enhancement"  # New: minor improvements that aren't full features
    CHORE = "chore"              # New: routine maintenance tasks
    RESEARCH = "research"        # New: investigative tasks
    TESTING = "testing"          # New: test-related tasks
    SECURITY = "security"        # New: security-focused tasks
    PROJECT = "project"          # New: project-level tasks that serve as containers
    MILESTONE = "milestone"      # New: milestone tasks that represent key achievements
    
    @classmethod
    def from_string(cls, type_str: str) -> 'TaskType':
        """
        Convert a string to a TaskType enum value.
        
        Args:
            type_str: The task type string to convert
            
        Returns:
            The corresponding TaskType enum value
            
        Notes:
            Returns TASK as default for unrecognized values for backward compatibility
        """
        if not type_str:
            return cls.TASK
            
        type_map = {
            "task": cls.TASK,
            "bug": cls.BUG,
            "feature": cls.FEATURE,
            "refactor": cls.REFACTOR,
            "documentation": cls.DOCUMENTATION,
            "enhancement": cls.ENHANCEMENT,
            "chore": cls.CHORE,
            "research": cls.RESEARCH,
            "testing": cls.TESTING,
            "security": cls.SECURITY,
            "project": cls.PROJECT,
            "milestone": cls.MILESTONE
        }
        
        lower_type = type_str.lower()
        if lower_type not in type_map:
            return cls.TASK  # Default to TASK for unrecognized values
        
        return type_map[lower_type]
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """
        Get a list of all valid task type strings.
        
        Returns:
            List of string values for all task types
        """
        return [task_type.value for task_type in cls]
    
    @property
    def color(self) -> TextColor:
        """
        Get the color associated with this task type.
        
        Returns:
            TextColor: The color for this task type
        """
        color_map = {
            TaskType.TASK: TextColor.CYAN,
            TaskType.BUG: TextColor.BRIGHT_RED,
            TaskType.FEATURE: TextColor.BRIGHT_GREEN,
            TaskType.REFACTOR: TextColor.BLUE,
            TaskType.DOCUMENTATION: TextColor.BRIGHT_MAGENTA,
            TaskType.ENHANCEMENT: TextColor.GREEN,
            TaskType.CHORE: TextColor.BRIGHT_BLACK,
            TaskType.RESEARCH: TextColor.YELLOW,
            TaskType.TESTING: TextColor.BRIGHT_CYAN,
            TaskType.SECURITY: TextColor.RED,
            TaskType.PROJECT: TextColor.MAGENTA,
            TaskType.MILESTONE: TextColor.BRIGHT_YELLOW
        }
        
        return color_map.get(self, TextColor.WHITE)
    
    def colored_name(self) -> str:
        """
        Get the task type name with appropriate color applied.
        
        Returns:
            Colored string representation of the task type name
        """
        return colorize(self.value, self.color)
    
    def __str__(self) -> str:
        """String representation of the task type."""
        return self.value


def task_type_color(task_type_str: str) -> TextColor:
    """
    Get the color associated with a task type string.
    
    Args:
        task_type_str: String representation of the task type
    
    Returns:
        TextColor for the specified task type
    """
    task_type = TaskType.from_string(task_type_str)
    return task_type.color


def get_colored_task_type(task_type_str: str) -> str:
    """
    Get a colored string representation of a task type.
    
    Args:
        task_type_str: String representation of the task type
    
    Returns:
        Colored string representation of the task type
    """
    task_type = TaskType.from_string(task_type_str)
    return task_type.colored_name() 