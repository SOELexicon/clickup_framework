"""
Task: tsk_3f55d115 - Update Plugins Module Comments
Document: refactor/plugins/hooks/hook_system.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)

Used By:
    - PluginManager: Uses hook system to integrate plugins into core functionality
    - TaskService: Defines hooks for task lifecycle events
    - CommandSystem: Creates extension points using hooks
    - NotificationSystem: Registers notification delivery hooks

Purpose:
    Defines the hook system that allows plugins to extend functionality
    at specific points in the application without modifying the core code.
    Provides a priority-based execution model with error isolation.

Requirements:
    - Hooks must be registered with unique names
    - Hook callbacks must be executed in priority order
    - Hook execution must isolate errors to prevent system crashes
    - CRITICAL: Hook system must not leak plugin failures
    - CRITICAL: Hook priority must be maintained during execution
    - CRITICAL: Plugin unregistration must properly clean up all hooks

Hook System Implementation

This module defines the hook system that allows plugins to extend functionality
at specific points in the application without modifying the core code.
"""

import functools
import inspect
import logging
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Generic, Union, Tuple

logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')  # Return type of hook functions
HookFunction = Callable[..., T]
HookCallback = Callable[..., Any]


class HookPriority(Enum):
    """Priority levels for hook execution order."""
    LOWEST = auto()
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    HIGHEST = auto()
    
    @classmethod
    def value_of(cls, priority: Union[int, str, 'HookPriority']) -> 'HookPriority':
        """Convert various priority formats to HookPriority enum."""
        if isinstance(priority, cls):
            return priority
        
        if isinstance(priority, int):
            priorities = list(cls)
            if 0 <= priority < len(priorities):
                return priorities[priority]
            return cls.NORMAL
            
        if isinstance(priority, str):
            try:
                return cls[priority.upper()]
            except KeyError:
                return cls.NORMAL
                
        return cls.NORMAL


class HookInfo:
    """Information about a registered hook."""
    
    def __init__(
        self,
        callback: HookCallback,
        plugin_id: str,
        priority: HookPriority = HookPriority.NORMAL,
        tags: Optional[Set[str]] = None
    ):
        """
        Initialize hook information.
        
        Args:
            callback: The function to call when the hook is triggered
            plugin_id: ID of the plugin that registered this hook
            priority: Execution priority of this hook
            tags: Optional set of tags for filtering hooks
        """
        self.callback = callback
        self.plugin_id = plugin_id
        self.priority = priority
        self.tags = tags or set()
        
    def __lt__(self, other: 'HookInfo') -> bool:
        """Compare hook priority for sorting."""
        if not isinstance(other, HookInfo):
            return NotImplemented
        
        # Sort by priority (higher priority runs first)
        return self.priority.value > other.priority.value


class Hook(Generic[T]):
    """
    A hook that plugins can register callbacks with.
    
    Hooks are extension points that allow plugins to modify behavior
    or data at specific points in the application.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize a hook.
        
        Args:
            name: Unique name for the hook
            description: Optional description of the hook's purpose
        """
        self.name = name
        self.description = description
        self.hooks: List[HookInfo] = []
        
    def register(
        self,
        callback: HookCallback,
        plugin_id: str,
        priority: Union[HookPriority, int, str] = HookPriority.NORMAL,
        tags: Optional[Set[str]] = None
    ) -> None:
        """
        Register a callback with this hook.
        
        Args:
            callback: The function to call when the hook is triggered
            plugin_id: ID of the plugin registering the callback
            priority: Execution priority (higher runs first)
            tags: Optional set of tags for filtering hooks
        """
        if not callable(callback):
            raise ValueError(f"Hook callback must be callable: {callback}")
            
        priority_enum = HookPriority.value_of(priority)
        
        hook_info = HookInfo(callback, plugin_id, priority_enum, tags)
        self.hooks.append(hook_info)
        
        # Sort hooks by priority (higher priority runs first)
        self.hooks.sort()
        
        logger.debug(f"Registered hook '{self.name}' from plugin '{plugin_id}' with priority {priority_enum.name}")
        
    def unregister(self, plugin_id: str) -> int:
        """
        Unregister all callbacks from a specific plugin.
        
        Args:
            plugin_id: ID of the plugin to unregister
            
        Returns:
            Number of callbacks unregistered
        """
        initial_count = len(self.hooks)
        self.hooks = [h for h in self.hooks if h.plugin_id != plugin_id]
        removed = initial_count - len(self.hooks)
        
        if removed > 0:
            logger.debug(f"Unregistered {removed} hook(s) for '{self.name}' from plugin '{plugin_id}'")
            
        return removed
        
    def execute(self, *args: Any, **kwargs: Any) -> List[T]:
        """
        Execute all registered callbacks in priority order.
        
        Args:
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks
            
        Returns:
            List of return values from all callbacks
        """
        results = []
        
        for hook_info in self.hooks:
            try:
                result = hook_info.callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Error executing hook '{self.name}' from plugin '{hook_info.plugin_id}': {str(e)}",
                    exc_info=True
                )
                
        return results
        
    def execute_until_true(self, *args: Any, **kwargs: Any) -> Tuple[bool, Optional[T]]:
        """
        Execute callbacks until one returns a truthy value.
        
        Args:
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks
            
        Returns:
            Tuple of (success, result) where success is True if any
            callback returned a truthy value, and result is the first
            truthy value or None if no callback returned a truthy value
        """
        for hook_info in self.hooks:
            try:
                result = hook_info.callback(*args, **kwargs)
                if result:
                    return True, result
            except Exception as e:
                logger.error(
                    f"Error executing hook '{self.name}' from plugin '{hook_info.plugin_id}': {str(e)}",
                    exc_info=True
                )
                
        return False, None
        
    def execute_until_false(self, *args: Any, **kwargs: Any) -> Tuple[bool, Optional[T]]:
        """
        Execute callbacks until one returns a falsy value.
        
        Args:
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks
            
        Returns:
            Tuple of (success, result) where success is True if all
            callbacks returned truthy values, and result is the first
            falsy value or None if all callbacks returned truthy values
        """
        for hook_info in self.hooks:
            try:
                result = hook_info.callback(*args, **kwargs)
                if not result:
                    return False, result
            except Exception as e:
                logger.error(
                    f"Error executing hook '{self.name}' from plugin '{hook_info.plugin_id}': {str(e)}",
                    exc_info=True
                )
                return False, None
                
        return True, None
    
    def filter(self, value: T, *args: Any, **kwargs: Any) -> T:
        """
        Pass a value through all callbacks as a filter chain.
        
        Each callback receives the output of the previous callback.
        
        Args:
            value: Initial value to filter
            *args: Additional positional arguments to pass to callbacks
            **kwargs: Additional keyword arguments to pass to callbacks
            
        Returns:
            The final filtered value after passing through all callbacks
        """
        result = value
        
        for hook_info in self.hooks:
            try:
                next_result = hook_info.callback(result, *args, **kwargs)
                # Only update if the callback returned a value
                if next_result is not None:
                    result = next_result
            except Exception as e:
                logger.error(
                    f"Error executing filter hook '{self.name}' from plugin '{hook_info.plugin_id}': {str(e)}",
                    exc_info=True
                )
                
        return result


class HookRegistry:
    """
    Registry for managing hooks throughout the application.
    
    The registry is responsible for:
    - Creating and retrieving hooks
    - Managing hook registrations
    - Dispatching hook events
    """
    
    def __init__(self):
        """Initialize the hook registry."""
        self.hooks: Dict[str, Hook] = {}
        
    def create_hook(self, name: str, description: str = "") -> Hook:
        """
        Create a new hook.
        
        Args:
            name: Unique name for the hook
            description: Optional description of the hook's purpose
            
        Returns:
            The created hook
            
        Raises:
            ValueError: If a hook with the given name already exists
        """
        if name in self.hooks:
            raise ValueError(f"Hook '{name}' already exists")
            
        hook = Hook(name, description)
        self.hooks[name] = hook
        
        logger.debug(f"Created hook: {name}")
        return hook
        
    def get_hook(self, name: str) -> Hook:
        """
        Get an existing hook by name.
        
        Args:
            name: Name of the hook to retrieve
            
        Returns:
            The hook
            
        Raises:
            KeyError: If no hook with the given name exists
        """
        if name not in self.hooks:
            raise KeyError(f"Hook '{name}' does not exist")
            
        return self.hooks[name]
        
    def get_or_create_hook(self, name: str, description: str = "") -> Hook:
        """
        Get an existing hook or create a new one if it doesn't exist.
        
        Args:
            name: Name of the hook
            description: Optional description for new hooks
            
        Returns:
            The hook
        """
        if name in self.hooks:
            return self.hooks[name]
            
        return self.create_hook(name, description)
        
    def register_hook(
        self,
        hook_name: str,
        callback: HookCallback,
        plugin_id: str,
        priority: Union[HookPriority, int, str] = HookPriority.NORMAL,
        tags: Optional[Set[str]] = None,
        description: str = ""
    ) -> None:
        """
        Register a callback with a hook, creating the hook if needed.
        
        Args:
            hook_name: Name of the hook to register with
            callback: The function to call when the hook is triggered
            plugin_id: ID of the plugin registering the callback
            priority: Execution priority (higher runs first)
            tags: Optional set of tags for filtering hooks
            description: Optional description for new hooks
        """
        hook = self.get_or_create_hook(hook_name, description)
        hook.register(callback, plugin_id, priority, tags)
        
    def unregister_hooks(self, plugin_id: str) -> int:
        """
        Unregister all hooks from a specific plugin.
        
        Args:
            plugin_id: ID of the plugin to unregister
            
        Returns:
            Number of hooks unregistered
        """
        total_removed = 0
        
        for hook in self.hooks.values():
            removed = hook.unregister(plugin_id)
            total_removed += removed
            
        if total_removed > 0:
            logger.debug(f"Unregistered {total_removed} hook(s) from plugin '{plugin_id}'")
            
        return total_removed
        
    def execute_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> List[Any]:
        """
        Execute all callbacks registered with a hook.
        
        Args:
            hook_name: Name of the hook to execute
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks
            
        Returns:
            List of return values from all callbacks
            
        Raises:
            KeyError: If no hook with the given name exists
        """
        hook = self.get_hook(hook_name)
        return hook.execute(*args, **kwargs)
        
    def filter_with_hook(self, hook_name: str, value: T, *args: Any, **kwargs: Any) -> T:
        """
        Filter a value through all callbacks registered with a hook.
        
        Args:
            hook_name: Name of the hook to use for filtering
            value: Initial value to filter
            *args: Additional positional arguments to pass to callbacks
            **kwargs: Additional keyword arguments to pass to callbacks
            
        Returns:
            The final filtered value after passing through all callbacks
            
        Raises:
            KeyError: If no hook with the given name exists
        """
        hook = self.get_hook(hook_name)
        return hook.filter(value, *args, **kwargs)


# Global hook registry
registry = HookRegistry()

# Create a global instance of HookRegistry to be imported by other modules
global_hook_registry = registry


def register_hook(
    hook_name: str,
    priority: Union[HookPriority, int, str] = HookPriority.NORMAL,
    tags: Optional[Set[str]] = None,
    description: str = ""
) -> Callable[[HookCallback], HookCallback]:
    """
    Decorator for registering a function as a hook callback.
    
    Example:
        @register_hook('task.pre_status_change', priority=HookPriority.HIGH)
        def validate_status_change(task, old_status, new_status):
            # Validation logic
            return True
    
    Args:
        hook_name: Name of the hook to register with
        priority: Execution priority (higher runs first)
        tags: Optional set of tags for filtering hooks
        description: Optional description for new hooks
        
    Returns:
        Decorator function that registers the callback
    """
    def decorator(func: HookCallback) -> HookCallback:
        # Plugin ID will be set when the plugin is loaded
        # This is just a placeholder that will be replaced
        setattr(func, '_hook_info', {
            'hook_name': hook_name,
            'priority': priority,
            'tags': tags or set(),
            'description': description
        })
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
            
        return wrapper
        
    return decorator


def get_hooks_from_module(module: Any) -> List[Tuple[Callable, Dict[str, Any]]]:
    """
    Extract all hook callbacks from a module.
    
    Args:
        module: Module object to scan for hook callbacks
        
    Returns:
        List of (callback, hook_info) tuples for all hook callbacks in the module
    """
    hooks = []
    
    for name, obj in inspect.getmembers(module):
        if callable(obj) and hasattr(obj, '_hook_info'):
            hooks.append((obj, getattr(obj, '_hook_info')))
            
    return hooks 