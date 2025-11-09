"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/logging/__init__.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CoreManager: Uses for application-wide logging
    - CommandSystem: Logs command execution and errors
    - PluginSystem: Provides logging services to plugins
    - ErrorHandler: Records detailed error information
    - StorageManager: Logs file operations and data changes

Purpose:
    Provides a structured logging framework with multiple output destinations,
    configurable formatting, and hierarchical logging levels to enable comprehensive
    application activity tracking and error diagnostics.

Requirements:
    - Must support multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Must support multiple output destinations (console, file, etc.)
    - Must handle large log volumes efficiently
    - Must provide consistent log formatting
    - CRITICAL: Must avoid logging sensitive information
    - CRITICAL: Must be thread-safe for concurrent logging
    - CRITICAL: File logging must handle rotation to prevent excessive disk usage

Logging Package

This package provides a structured logging framework for the ClickUp JSON Manager.
"""

from .logger import (
    # Log level
    LogLevel,
    
    # Formatters
    LogFormatter,
    TextFormatter,
    JsonFormatter,
    
    # Handlers
    LogHandler,
    ConsoleHandler,
    FileHandler,
    BufferedHandler,
    
    # Logger
    Logger,
    default_logger,
    get_logger,
    
    # Configuration
    configure_logging
)

__all__ = [
    'LogLevel',
    'LogFormatter',
    'TextFormatter', 
    'JsonFormatter',
    'LogHandler',
    'ConsoleHandler',
    'FileHandler',
    'BufferedHandler',
    'Logger',
    'default_logger',
    'get_logger',
    'configure_logging'
]
