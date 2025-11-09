"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/utils/__init__.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CLI: Imports color and formatting utilities for terminal output
    - CoreManager: Uses JSON utilities for data manipulation
    - ErrorHandler: Leverages error formatters for user-friendly messages
    - RESTfulAPI: Uses config utilities
    - DashboardManager: Uses formatting utilities for dashboard display
    - All modules: General utilities are used throughout the codebase

Purpose:
    Provides a collection of general-purpose utility functions and classes
    that are used throughout the application. Centralizes common functionality
    for formatting, styling, error handling, and configuration. Specifically
    focuses on terminal-based formatting, color support, and cross-platform
    compatibility.

Requirements:
    - CRITICAL: Color handling must degrade gracefully in terminals without color support
    - CRITICAL: JSON utilities must handle cross-platform newline differences
    - CRITICAL: Configuration utilities must validate inputs
    - All utilities must be platform-independent
    - Formatting helpers must use consistent styling conventions
    - Error formatting must provide user-friendly messages

Utilities package for ClickUp JSON Manager.

This package contains utility modules for various functionality:
- JSON utilities
- Error handling and formatting
- Text formatting
- Color support
"""

from refactor.utils.colors import (
    TextColor, BackgroundColor, TextStyle, DefaultTheme,
    colorize, status_color, priority_color, score_color, relationship_color
)

__all__ = [
    'TextColor',
    'BackgroundColor',
    'TextStyle',
    'DefaultTheme',
    'colorize',
    'status_color',
    'priority_color',
    'score_color',
    'relationship_color',
]

# Version info
__version__ = "0.1.0" 