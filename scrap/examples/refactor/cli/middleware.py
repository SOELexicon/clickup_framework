"""
Command Middleware Pipeline

This module implements an enhanced middleware pipeline system for the CLI module,
providing validation, logging, error handling, and recovery mechanisms.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Type
import logging
from pathlib import Path
import time
import traceback
from .command import Command, CommandContext, Middleware
from .error_handling import CLIError, map_exception_to_error_code
from refactor.core.exceptions import (
    get_command_error_code,
    get_storage_error_code,
    get_validation_error_code,
    ErrorContextBuilder,
    error_code_registry
)
import sys


@dataclass
class PipelineConfig:
    """Configuration for the middleware pipeline."""
    enable_validation: bool = True
    enable_logging: bool = True
    enable_error_handling: bool = True
    enable_recovery: bool = True
    log_level: int = logging.INFO
    log_file: Optional[Path] = None
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds


@dataclass
class ValidationError:
    """Represents a validation error."""
    field: str
    message: str
    code: str
    context: Dict[str, Any] = field(default_factory=dict)


class ValidationMiddleware(Middleware):
    """
    Middleware for validating command arguments and state.
    
    This middleware runs before command execution to ensure all
    required conditions are met.
    """
    
    def __init__(self, config: PipelineConfig):
        """
        Initialize the validation middleware.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.validators: Dict[str, List[Callable]] = {}
    
    def add_validator(self, command_name: str, validator: Callable) -> None:
        """
        Add a validator for a specific command.
        
        Args:
            command_name: Name of the command
            validator: Validation function that returns list of ValidationError
        """
        if command_name not in self.validators:
            self.validators[command_name] = []
        self.validators[command_name].append(validator)
    
    def before_execution(self, context: CommandContext) -> None:
        """Run validation before command execution."""
        if not self.config.enable_validation:
            return
        
        errors = []
        validators = self.validators.get(context.command.name, [])
        
        for validator in validators:
            try:
                result = validator(context)
                if result:
                    errors.extend(result)
            except Exception as e:
                errors.append(ValidationError(
                    field="validator",
                    message=f"Validator failed: {str(e)}",
                    code="VALIDATOR_ERROR"
                ))
        
        if errors:
            context.metadata['validation_errors'] = errors
            error_code = get_validation_error_code("001")
            error_context = ErrorContextBuilder("Validation failed") \
                .with_code(str(error_code)) \
                .with_data("command", context.command.name) \
                .with_data("errors", [e.message for e in errors]) \
                .build()
            context.abort(CLIError("Validation failed", error_code))
    
    def after_execution(self, context: CommandContext) -> None:
        """No-op after execution."""
        pass


class LoggingMiddleware(Middleware):
    """
    Middleware for logging command execution.
    
    This middleware handles logging before and after command execution,
    including performance metrics and error details.
    """
    
    def __init__(self, config: PipelineConfig):
        """
        Initialize the logging middleware.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with the configured options."""
        logger = logging.getLogger('cli.commands')
        logger.setLevel(self.config.log_level)
        
        # Add console handler
        console = logging.StreamHandler()
        console.setLevel(self.config.log_level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console.setFormatter(formatter)
        logger.addHandler(console)
        
        # Add file handler if configured
        if self.config.log_file:
            file_handler = logging.FileHandler(self.config.log_file)
            file_handler.setLevel(self.config.log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def before_execution(self, context: CommandContext) -> None:
        """Log command execution start."""
        if not self.config.enable_logging:
            return
        
        context.metadata['start_time'] = time.time()
        self.logger.info(
            f"Executing command '{context.command.name}' with args: {vars(context.args)}"
        )
    
    def after_execution(self, context: CommandContext) -> None:
        """Log command execution completion and metrics."""
        if not self.config.enable_logging:
            return
        
        duration = time.time() - context.metadata.get('start_time', time.time())
        
        if context.error:
            self.logger.error(
                f"Command '{context.command.name}' failed after {duration:.2f}s: {str(context.error)}",
                exc_info=context.error
            )
        else:
            self.logger.info(
                f"Command '{context.command.name}' completed in {duration:.2f}s with result: {context.result}"
            )


class ErrorHandlingMiddleware(Middleware):
    """
    Middleware for handling errors consistently across commands.
    
    This middleware intercepts exceptions during command execution and
    formats errors consistently, ensuring that error information is stored
    in the command context.
    """
    
    def __init__(self, config: PipelineConfig):
        """
        Initialize the error handling middleware.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
    
    def before_execution(self, context: CommandContext) -> None:
        """
        Execute before the command is executed.
        
        No action needed before execution.
        
        Args:
            context: Command execution context
        """
        pass
    
    def after_execution(self, context: CommandContext) -> None:
        """
        Execute after the command is executed.
        
        If an error occurred, format it consistently and store it in the context.
        
        Args:
            context: Command execution context
        """
        if not self.config.enable_error_handling:
            return
            
        if context.error is not None:
            # Format error information when an error is already present
            self._format_error(context, context.error)
            
        elif context.result is not None and isinstance(context.result, Exception):
            # Command returned an exception, format it and store it
            self._format_error(context, context.result)
            context.result = 1  # Return error exit code
    
    def _format_error(self, context: CommandContext, error: Exception) -> None:
        """
        Format an error consistently and store it in the context.
        
        Args:
            context: Command execution context
            error: Exception that occurred
        """
        # Get command name for context
        command_name = context.command.name if context.command else "unknown"
        
        # Determine error message and code
        error_message = str(error)
        
        # Default to general command error
        error_code = get_command_error_code("GENERAL", "000")
        
        # Create error context
        context_builder = ErrorContextBuilder(error_message) \
            .with_code(str(error_code)) \
            .with_data("command", command_name)
        
        # Add command arguments to context (excluding sensitive data)
        if context.args:
            for key, value in vars(context.args).items():
                if key not in ['password', 'token', 'api_key']:  # Skip sensitive data
                    context_builder.with_data(f"arg_{key}", str(value))
        
        # Add stack trace in development mode (can be controlled via config)
        if True:  # Replace with config check for development mode
            tb = traceback.format_exc()
            context_builder.with_data("stack_trace", tb)
        
        # Build and store error context
        context.error_context = context_builder.build()
        
        # Add error_info to context metadata for test assertions and other middleware
        error_info = {
            "command": command_name,
            "error_type": type(error).__name__,
            "message": error_message,
            "error_code": str(error_code)
        }
        
        # Add validation errors if present
        if 'validation_errors' in context.metadata:
            error_info['validation_errors'] = [
                {
                    "field": e.field,
                    "message": e.message,
                    "code": e.code
                }
                for e in context.metadata['validation_errors']
            ]
            
        context.metadata['error_info'] = error_info
        context.error = error
        
        # Print error information
        print(f"Error [{error_code}]: {error_message}", file=sys.stderr)
        if context.error_context:
            # In production, you might want to limit the context output
            print(f"Context: {context.error_context.to_json()}", file=sys.stderr)


class RecoveryMiddleware(Middleware):
    """
    Middleware for handling command recovery and retries.
    
    This middleware implements retry logic and recovery mechanisms
    for failed commands.
    """
    
    def __init__(self, config: PipelineConfig):
        """
        Initialize the recovery middleware.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
    
    def before_execution(self, context: CommandContext) -> None:
        """Initialize retry count."""
        if not self.config.enable_recovery:
            return
        
        context.metadata['retry_count'] = 0
    
    def after_execution(self, context: CommandContext) -> None:
        """Handle command recovery if needed."""
        if not self.config.enable_recovery or not context.error:
            return
        
        retry_count = context.metadata.get('retry_count', 0)
        
        while (
            context.error
            and retry_count < self.config.max_retries
            and self._should_retry(context)
        ):
            retry_count += 1
            context.metadata['retry_count'] = retry_count
            
            # Wait before retrying
            time.sleep(self.config.retry_delay)
            
            # Clear error state
            context.error = None
            context.aborted = False
            
            try:
                # Re-execute the command
                context.result = context.command.execute(context.args)
            except Exception as e:
                context.error = e
    
    def _should_retry(self, context: CommandContext) -> bool:
        """
        Determine if a failed command should be retried.
        
        This method can be extended with more sophisticated retry logic
        based on error types, command types, etc.
        """
        # Don't retry validation errors
        if 'validation_errors' in context.metadata:
            return False
        
        # Don't retry if the command explicitly opts out
        if hasattr(context.command, 'allow_retry'):
            return bool(context.command.allow_retry)
        
        return True


class EnhancedMiddlewarePipeline:
    """
    Enhanced pipeline for executing middleware components.
    
    This class extends the basic middleware pipeline with configuration
    options and standard middleware components.
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the enhanced middleware pipeline.
        
        Args:
            config: Optional pipeline configuration
        """
        self.config = config or PipelineConfig()
        self.middleware_list: List[Middleware] = []
        
        # Add standard middleware components
        if self.config.enable_validation:
            self.add_middleware(ValidationMiddleware(self.config))
        
        if self.config.enable_logging:
            self.add_middleware(LoggingMiddleware(self.config))
        
        if self.config.enable_error_handling:
            self.add_middleware(ErrorHandlingMiddleware(self.config))
        
        if self.config.enable_recovery:
            self.add_middleware(RecoveryMiddleware(self.config))
    
    def add_middleware(self, middleware: Middleware) -> None:
        """
        Add a middleware component to the pipeline.
        
        Args:
            middleware: Middleware component to add
        """
        self.middleware_list.append(middleware)
    
    def execute(self, context: CommandContext) -> int:
        """
        Execute the command with middleware.
        
        Args:
            context: Command execution context
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        # Execute before_execution for all middleware
        for middleware in self.middleware_list:
            try:
                middleware.before_execution(context)
                if context.aborted:
                    break
            except Exception as e:
                context.abort(e)
                break
        
        # Execute command if not aborted
        if not context.aborted:
            try:
                context.result = context.command.execute(context.args)
            except Exception as e:
                context.abort(e)
        
        # Execute after_execution for all middleware in reverse order
        for middleware in reversed(self.middleware_list):
            try:
                middleware.after_execution(context)
            except Exception as e:
                # If an exception occurs in after_execution, we still continue
                # but we keep track of the latest error
                context.error = e
        
        # Return the result or an error code
        if context.error:
            return 1  # Error
        return context.result if isinstance(context.result, int) else 0 