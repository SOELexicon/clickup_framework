"""
Task: tsk_0fa698f3 - Update Core Module Comments
Document: refactor/core/services/base_service.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_6be08e82 - Refactor Tool for Modularity (related)

Used By:
    - All Service Classes: Inherit from BaseService to leverage common functionality
    - Service Factory: For creating service instances
    - Core Manager: For coordinating operations across services
    - Plugin System: For hook integration at the service layer

Purpose:
    Defines the foundational BaseService class that all service classes extend,
    providing common functionality for error handling, logging, concurrency control,
    and hook system integration across the entire service layer.

Requirements:
    - Must provide consistent error handling mechanisms
    - Must integrate with the application's logging system
    - Must implement thread-safety mechanisms for service operations
    - Must connect to the hook system for extensibility
    - CRITICAL: Must handle errors in hook execution gracefully
    - CRITICAL: Must be lightweight to avoid impacting service performance

Changes:
    - v1: Initial implementation with basic service functionality
    - v2: Added hook system integration
    - v3: Enhanced logging and error handling
    - v4: Added thread safety with locks

Lessons Learned:
    - Thread safety is essential for services that may be accessed concurrently
    - Hook integration enables powerful extensibility with minimal coupling
    - Consistent error handling patterns simplify debugging and troubleshooting
    - Base classes should focus on providing infrastructure, not business logic
"""

import logging
import threading
from typing import Optional, Any, Dict

from ...plugins.hooks.hook_system import global_hook_registry


class BaseServiceError(Exception):
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/services/base_service.py
    dohcount: 1
    
    Used By:
        - Service Classes: For raising service-specific errors
        - Error Handlers: For catching and handling service errors
        - Core Manager: For propagating service errors to clients
    
    Purpose:
        Base exception class for all service-related errors, providing a common
        type that can be caught to handle any service error while enabling
        more specific exception types for detailed error handling.
    
    Requirements:
        - Must be the parent class for all service-specific exceptions
        - Should include informative error messages
        - Should be used sparingly in favor of more specific subclasses
    """
    pass


class BaseService:
    """
    Task: tsk_0fa698f3 - Update Core Module Comments
    Document: refactor/core/services/base_service.py
    dohcount: 1
    
    Used By:
        - All Service Classes: Inherit from this class for common functionality
        - Core Manager: Accesses services through this base interface
        - Test Framework: For mocking service behavior
    
    Purpose:
        Provides a foundation for all service classes with common infrastructure
        for logging, error handling, thread safety, and hook system integration,
        ensuring consistent behavior across the entire service layer.
    
    Requirements:
        - Must provide thread-safe operation capabilities
        - Must integrate with the application logging system
        - Must connect to the hook system for extensibility
        - Must implement consistent error handling
        - CRITICAL: Must handle errors in hook execution gracefully
        - CRITICAL: Must isolate service-specific errors from system errors
    
    Changes:
        - v1: Initial implementation with basic logging
        - v2: Added hook system integration
        - v3: Added thread safety with locks
        - v4: Enhanced error handling
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the base service.
        
        Sets up the logger, threading lock, and hook registry for the service.
        
        Args:
            logger: Optional logger for service operations; if None, 
                   a logger is created using the class name
        
        Side Effects:
            - Creates a logger if not provided
            - Initializes a reentrant lock for thread safety
            - References the global hook registry
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._lock = threading.RLock()
        self.hook_registry = global_hook_registry
    
    def _execute_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a hook with the given name and arguments.
        
        Calls the registered hook callbacks with the provided arguments,
        handling any exceptions that occur during hook execution.
        
        Args:
            hook_name: Name of the hook to execute
            *args: Positional arguments to pass to the hook
            **kwargs: Keyword arguments to pass to the hook
            
        Returns:
            Result of the hook execution, or None if an error occurs
            
        Side Effects:
            - Logs any exceptions that occur during hook execution
            
        Requirements:
            - Must handle exceptions during hook execution gracefully
            - Must not allow hook failures to crash the service
        """
        try:
            return self.hook_registry.execute_hook(hook_name, *args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error executing hook '{hook_name}': {str(e)}", exc_info=True)
            return None
    
    def _execute_hook_filter(self, hook_name: str, value: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a hook as a filter, passing the value through all registered callbacks.
        
        Similar to _execute_hook, but specifically for filter hooks that modify
        a value as it passes through multiple callbacks in sequence.
        
        Args:
            hook_name: Name of the hook to execute
            value: Initial value to filter
            *args: Additional positional arguments to pass to the hook
            **kwargs: Additional keyword arguments to pass to the hook
            
        Returns:
            Filtered value after passing through all callbacks,
            or the original value if an error occurs
            
        Side Effects:
            - Logs any exceptions that occur during hook execution
            
        Requirements:
            - Must handle exceptions during hook execution gracefully
            - Must not allow hook failures to crash the service
            - Must return the original value if filter execution fails
        """
        try:
            return self.hook_registry.filter(hook_name, value, *args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error executing filter hook '{hook_name}': {str(e)}", exc_info=True)
            return value 