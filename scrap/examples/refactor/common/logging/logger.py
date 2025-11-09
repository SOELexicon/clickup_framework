"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/logging/logger.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - All Application Components: For logging activities and errors
    - CoreManager: For application-wide logging configuration
    - PluginSystem: Provides logging facilities to plugins
    - ErrorHandler: For detailed error recording and tracking
    - RESTfulAPI: For API request/response logging
    - CommandSystem: For CLI command execution logging

Purpose:
    Implements a comprehensive logging system with multiple log levels,
    output handlers, formatters, and performance optimizations to provide
    detailed activity records while maintaining application performance.

Requirements:
    - Must provide both synchronous and asynchronous logging options
    - Must support multiple output destinations concurrently 
    - Must implement log rotation for file-based logging
    - Must support structured logging with context data
    - Must provide lazily evaluated log messages for performance
    - CRITICAL: Must be thread-safe for all operations
    - CRITICAL: Must avoid logging sensitive information
    - CRITICAL: Must handle high-volume logging efficiently

Logging Module

This module provides a structured logging framework for the ClickUp JSON Manager with:
- Different log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Multiple output handlers (console, file)
- Custom formatters
- Context tracking
- Performance optimization
"""
from typing import Dict, Any, Optional, List, Union, Callable
import sys
import os
import logging
import datetime
from enum import Enum
import json
import traceback


class LogLevel(Enum):
    """Log level enumeration that maps to standard logging levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormatter:
    """Base class for log formatters."""
    
    def format(self, record: Dict[str, Any]) -> str:
        """
        Format a log record into a string.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted log message
        """
        raise NotImplementedError("Subclasses must implement format method")


class TextFormatter(LogFormatter):
    """Formats log records as human-readable text."""
    
    def __init__(self, include_timestamp: bool = True, include_level: bool = True):
        """
        Initialize the text formatter.
        
        Args:
            include_timestamp: Whether to include timestamp in the output
            include_level: Whether to include log level in the output
        """
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        
    def format(self, record: Dict[str, Any]) -> str:
        """Format a record as text."""
        parts = []
        
        # Add timestamp if requested
        if self.include_timestamp and "timestamp" in record:
            parts.append(f"[{record['timestamp']}]")
            
        # Add log level if requested
        if self.include_level and "level" in record:
            parts.append(f"[{record['level']}]")
            
        # Add the message
        if "message" in record:
            parts.append(str(record["message"]))
            
        # Add context if present
        context_str = ""
        context = {k: v for k, v in record.items() 
                  if k not in ("timestamp", "level", "message", "exception")}
        
        if context:
            context_parts = []
            for key, value in context.items():
                if isinstance(value, (dict, list)):
                    # Convert complex structures to simplified representation
                    context_parts.append(f"{key}={str(value)}")
                else:
                    context_parts.append(f"{key}={value}")
            context_str = " - " + ", ".join(context_parts)
            
        # Add exception information if present
        exception_str = ""
        if "exception" in record and record["exception"]:
            exception_str = f"\nException: {record['exception']}"
            
        return " ".join(parts) + context_str + exception_str


class JsonFormatter(LogFormatter):
    """Formats log records as JSON for machine processing."""
    
    def format(self, record: Dict[str, Any]) -> str:
        """Format a record as JSON."""
        return json.dumps(record)


class LogHandler:
    """Base class for log handlers."""
    
    def handle(self, formatted_record: str) -> None:
        """
        Handle a formatted log record.
        
        Args:
            formatted_record: The formatted log record
        """
        raise NotImplementedError("Subclasses must implement handle method")


class ConsoleHandler(LogHandler):
    """Outputs log records to the console."""
    
    def __init__(self, use_stderr_for_errors: bool = True):
        """
        Initialize the console handler.
        
        Args:
            use_stderr_for_errors: Whether to output ERROR and CRITICAL logs to stderr
        """
        self.use_stderr_for_errors = use_stderr_for_errors
        
    def handle(self, formatted_record: str, level: LogLevel = None) -> None:
        """Output the record to the console."""
        if self.use_stderr_for_errors and level and level in (LogLevel.ERROR, LogLevel.CRITICAL):
            print(formatted_record, file=sys.stderr)
        else:
            print(formatted_record)


class FileHandler(LogHandler):
    """Outputs log records to a file."""
    
    def __init__(self, filename: str, mode: str = 'a', 
                 max_size_bytes: Optional[int] = None,
                 backup_count: int = 3):
        """
        Initialize the file handler.
        
        Args:
            filename: Path to the log file
            mode: File open mode ('a' for append, 'w' for write)
            max_size_bytes: Maximum file size before rotation (None for no limit)
            backup_count: Number of backup files to keep when rotating
        """
        self.filename = filename
        self.mode = mode
        self.max_size_bytes = max_size_bytes
        self.backup_count = backup_count
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
    
    def handle(self, formatted_record: str, level: LogLevel = None) -> None:
        """Output the record to a file."""
        try:
            # Check if rotation is needed
            if self.max_size_bytes and os.path.exists(self.filename):
                if os.path.getsize(self.filename) >= self.max_size_bytes:
                    self._rotate_files()
            
            # Write to file
            with open(self.filename, self.mode, encoding='utf-8') as f:
                f.write(formatted_record + '\n')
                
        except Exception as e:
            # Fall back to console if file writing fails
            print(f"Error writing to log file: {str(e)}")
            print(formatted_record)
    
    def _rotate_files(self) -> None:
        """Rotate log files."""
        if self.backup_count <= 0:
            return
            
        if os.path.exists(self.filename):
            # Remove the oldest backup if it exists
            oldest_backup = f"{self.filename}.{self.backup_count}"
            if os.path.exists(oldest_backup):
                os.remove(oldest_backup)
                
            # Shift the backup files
            for i in range(self.backup_count - 1, 0, -1):
                src = f"{self.filename}.{i}"
                dst = f"{self.filename}.{i + 1}"
                if os.path.exists(src):
                    os.rename(src, dst)
                    
            # Rename the current file to .1
            os.rename(self.filename, f"{self.filename}.1")


class BufferedHandler(LogHandler):
    """Buffers log records for batch processing."""
    
    def __init__(self, target_handler: LogHandler, buffer_size: int = 10, 
                 flush_level: LogLevel = LogLevel.ERROR):
        """
        Initialize the buffered handler.
        
        Args:
            target_handler: The handler to write records to when buffer is flushed
            buffer_size: The number of records to buffer before flushing
            flush_level: The minimum log level that triggers an immediate flush
        """
        self.target_handler = target_handler
        self.buffer_size = buffer_size
        self.flush_level = flush_level
        self.buffer = []
        
    def handle(self, formatted_record: str, level: LogLevel = None) -> None:
        """Buffer the record and flush if needed."""
        self.buffer.append(formatted_record)
        
        # Flush if buffer is full or level requires immediate flush
        if (len(self.buffer) >= self.buffer_size or 
                (level and level.value >= self.flush_level.value)):
            self.flush()
    
    def flush(self) -> None:
        """Flush the buffer to the target handler."""
        for record in self.buffer:
            self.target_handler.handle(record)
        self.buffer.clear()


class Logger:
    """
    Main logger class that handles log message routing.
    
    This logger supports:
    - Multiple handlers
    - Multiple formatters
    - Log levels
    - Context propagation
    - Lazy evaluation of expensive log messages
    """
    
    def __init__(self, name: str, level: Union[LogLevel, str] = LogLevel.INFO, 
                 handlers: Optional[List[LogHandler]] = None,
                 formatter: Optional[LogFormatter] = None):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            level: Minimum log level to process
            handlers: List of handlers to process records
            formatter: Formatter for log records
        """
        self.name = name
        
        # Set log level
        if isinstance(level, str):
            self.level = getattr(LogLevel, level.upper(), LogLevel.INFO)
        else:
            self.level = level
            
        # Set handlers and formatter
        self.handlers = handlers or [ConsoleHandler()]
        self.formatter = formatter or TextFormatter()
        
    def is_enabled_for(self, level: Union[LogLevel, str]) -> bool:
        """
        Check if a specific log level is enabled.
        
        Args:
            level: The log level to check
            
        Returns:
            True if the level is enabled, False otherwise
        """
        if isinstance(level, str):
            level = getattr(LogLevel, level.upper(), LogLevel.INFO)
            
        return level.value >= self.level.value
    
    def _log(self, level: LogLevel, message: Union[str, Callable[[], str]], 
             exception: Optional[Exception] = None, **kwargs) -> None:
        """
        Log a message at the specified level.
        
        Args:
            level: Log level
            message: Message or lazy function that returns a message
            exception: Optional exception to include
            **kwargs: Additional context values
        """
        # Check if this level is enabled
        if not self.is_enabled_for(level):
            return
            
        # Evaluate lazy messages
        if callable(message):
            message = message()
            
        # Create the log record
        record = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "level": level.name,
            "logger": self.name,
            "message": message,
        }
        
        # Add context
        record.update(kwargs)
        
        # Add exception information if provided
        if exception:
            record["exception"] = str(exception)
            record["traceback"] = "".join(traceback.format_exception(
                type(exception), exception, exception.__traceback__))
        
        # Format the record
        formatted_record = self.formatter.format(record)
        
        # Send to all handlers
        for handler in self.handlers:
            handler.handle(formatted_record, level)
    
    def debug(self, message: Union[str, Callable[[], str]], 
              exception: Optional[Exception] = None, **kwargs) -> None:
        """Log a message at DEBUG level."""
        self._log(LogLevel.DEBUG, message, exception, **kwargs)
    
    def info(self, message: Union[str, Callable[[], str]], 
             exception: Optional[Exception] = None, **kwargs) -> None:
        """Log a message at INFO level."""
        self._log(LogLevel.INFO, message, exception, **kwargs)
    
    def warning(self, message: Union[str, Callable[[], str]], 
                exception: Optional[Exception] = None, **kwargs) -> None:
        """Log a message at WARNING level."""
        self._log(LogLevel.WARNING, message, exception, **kwargs)
    
    def error(self, message: Union[str, Callable[[], str]], 
              exception: Optional[Exception] = None, **kwargs) -> None:
        """Log a message at ERROR level."""
        self._log(LogLevel.ERROR, message, exception, **kwargs)
    
    def critical(self, message: Union[str, Callable[[], str]], 
                 exception: Optional[Exception] = None, **kwargs) -> None:
        """Log a message at CRITICAL level."""
        self._log(LogLevel.CRITICAL, message, exception, **kwargs)
    
    def exception(self, message: Union[str, Callable[[], str]], 
                  exception: Optional[Exception] = None, **kwargs) -> None:
        """
        Log an exception with traceback.
        
        Args:
            message: Message or lazy function that returns a message
            exception: The exception to log (defaults to last exception in except block)
            **kwargs: Additional context values
        """
        if exception is None:
            # If no exception is provided, get the current exception
            exception = sys.exc_info()[1]
            
        # If there's still no exception, just log as error
        if exception is None:
            self.error(message, **kwargs)
        else:
            self._log(LogLevel.ERROR, message, exception, **kwargs)


# Create a default logger
default_logger = Logger(
    name="clickup_json_manager",
    level=LogLevel.INFO,
    handlers=[ConsoleHandler()],
    formatter=TextFormatter()
)

# Function to get or create a logger
def get_logger(name: Optional[str] = None, 
               level: Optional[Union[LogLevel, str]] = None,
               handlers: Optional[List[LogHandler]] = None,
               formatter: Optional[LogFormatter] = None) -> Logger:
    """
    Get or create a logger.
    
    Args:
        name: Logger name (uses default if None)
        level: Log level (uses default if None)
        handlers: List of handlers (uses default if None)
        formatter: Formatter (uses default if None)
        
    Returns:
        Logger instance
    """
    if name is None:
        return default_logger
        
    return Logger(
        name=name,
        level=level or default_logger.level,
        handlers=handlers or default_logger.handlers,
        formatter=formatter or default_logger.formatter
    )

def configure_logging(
    level: Union[LogLevel, str] = LogLevel.INFO,
    console: bool = True,
    console_level: Optional[Union[LogLevel, str]] = None,
    file_path: Optional[str] = None,
    file_level: Optional[Union[LogLevel, str]] = None,
    format_style: str = "text",
    include_timestamp: bool = True,
    include_level: bool = True,
    max_file_size_bytes: Optional[int] = None,
    backup_count: int = 3
) -> None:
    """
    Configure the default logger with the given settings.
    
    Args:
        level: Overall minimum log level
        console: Whether to log to console
        console_level: Console-specific log level (if different from overall)
        file_path: Path to log file (if file logging is desired)
        file_level: File-specific log level (if different from overall)
        format_style: "text" or "json"
        include_timestamp: Whether to include timestamp in text format
        include_level: Whether to include level in text format
        max_file_size_bytes: Max size for log file rotation
        backup_count: Number of backup files to keep
    """
    # Convert string levels to enum
    if isinstance(level, str):
        level = getattr(LogLevel, level.upper(), LogLevel.INFO)
    
    if isinstance(console_level, str):
        console_level = getattr(LogLevel, console_level.upper(), level)
    elif console_level is None:
        console_level = level
    
    if isinstance(file_level, str):
        file_level = getattr(LogLevel, file_level.upper(), level)
    elif file_level is None:
        file_level = level
    
    # Create formatter
    if format_style.lower() == "json":
        formatter = JsonFormatter()
    else:
        formatter = TextFormatter(
            include_timestamp=include_timestamp,
            include_level=include_level
        )
    
    # Create handlers
    handlers = []
    
    if console:
        handlers.append(ConsoleHandler())
    
    if file_path:
        handlers.append(
            FileHandler(
                filename=file_path,
                max_size_bytes=max_file_size_bytes,
                backup_count=backup_count
            )
        )
    
    # Update default logger
    default_logger.level = level
    default_logger.formatter = formatter
    default_logger.handlers = handlers 