"""
Template Finder Utility

This module provides functions to find and manage template files,
including finding default templates in .project directories.

Task: tsk_default_template - Default Template Support
"""

import os
from pathlib import Path
from typing import Optional, List


def find_default_template() -> Optional[str]:
    """
    Find the default template file in the .project directory.
    
    This function looks for template files in the following order:
    1. .project/clickup_tasks.json in the current directory
    2. .project/template.json in the current directory
    3. .project/default.json in the current directory
    
    Returns:
        Path to the default template file, or None if not found
    """
    current_dir = Path(os.getcwd())
    project_dir = current_dir / ".project"
    
    # Look for template files in the .project directory
    template_names = ["clickup_tasks.json", "template.json", "default.json"]
    
    for name in template_names:
        template_path = project_dir / name
        if template_path.exists():
            return str(template_path)
    
    return None


def get_template_path(template_arg: Optional[str]) -> Optional[str]:
    """
    Get the template path from an argument or use the default.
    
    Args:
        template_arg: Template path argument from command line
        
    Returns:
        Template path to use, or None if not found
    """
    if template_arg:
        # Use the provided template path
        return template_arg
    
    # Try to find the default template
    default_template = find_default_template()
    if default_template:
        return default_template
    
    # No template found
    return None


def get_required_template_path(template_arg: Optional[str]) -> str:
    """
    Get the template path from an argument or use the default.
    If no template is available, raise an error with a helpful message.
    
    Args:
        template_arg: Template path argument from command line
        
    Returns:
        Template path to use
        
    Raises:
        ValueError: If no template can be found
    """
    template_path = get_template_path(template_arg)
    if not template_path:
        raise ValueError(
            "No template file specified and no default template found.\n\n"
            "You can either:\n"
            "1. Specify a template file: ./cujm <command> path/to/template.json\n"
            "2. Create a default template in the .project directory:\n"
            "   ./cujm init --output .project/clickup_tasks.json\n"
            "\nOnce you have a default template in .project/clickup_tasks.json, "
            "you can run commands without specifying the template path."
        )
    return template_path


def create_project_directory() -> Path:
    """
    Create the .project directory if it doesn't exist.
    
    Returns:
        Path to the .project directory
    """
    current_dir = Path(os.getcwd())
    project_dir = current_dir / ".project"
    
    # Create the directory if it doesn't exist
    project_dir.mkdir(exist_ok=True)
    
    return project_dir 