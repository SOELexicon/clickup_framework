"""
Task: tsk_3f55d115 - Update Plugins Module Comments
Document: refactor/plugins/core_plugin/hook_system.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)

Used By:
    - PluginManager: Registers plugin hooks using this system
    - CoreManager: Executes hooks at defined extension points
    - TaskService: Uses hooks for task lifecycle events
    - SearchService: Uses hooks for search customization

Purpose:
    Provides the core functionality for registering and executing hooks,
    allowing plugins to extend and modify the behavior of the core system
    without direct modification of the codebase.

Requirements:
    - Hook specifications must define clear contracts with documentation
    - Hook implementations must be executed in a predictable order
    - Hook system must be thread-safe for concurrent access
    - CRITICAL: Hook failures must be isolated and not crash the system
    - CRITICAL: Hook registration/unregistration must be handled correctly during plugin lifecycle

Hook system implementation module.

This module provides the core functionality for registering and executing hooks,
allowing plugins to extend and modify the behavior of the core system.
"""

import inspect
from typing import Dict, List, Any, Optional, Set, Union, Callable, TypeVar, Generic

# Type variables for generic hook handling
T = TypeVar('T')
R = TypeVar('R')


class HookSpecification:
    """
    Class representing a hook specification.
    
    A hook specification defines the contract that hook implementations must follow,
    including the expected arguments and return value.
    """
    
    def __init__(self, name: str, doc: str = None):
        """
        Initialize a hook specification.
        
        Args:
            name: Unique name of the hook
            doc: Documentation string for the hook
        """
        self.name = name
        self.doc = doc or ""
        self.implementations: List[Callable] = []
    
    def add_implementation(self, impl: Callable) -> None:
        """
        Add an implementation to this hook specification.
        
        Args:
            impl: Implementation function or method
        """
        self.implementations.append(impl)
    
    def remove_implementation(self, impl: Callable) -> bool:
        """
        Remove an implementation from this hook specification.
        
        Args:
            impl: Implementation to remove
            
        Returns:
            True if the implementation was removed, False otherwise
        """
        if impl in self.implementations:
            self.implementations.remove(impl)
            return True
        return False


class HookRegistry:
    """
    Registry for managing hook specifications and implementations.
    
    This class provides methods to register hooks, add implementations,
    and execute hooks.
    """
    
    def __init__(self):
        """Initialize the hook registry."""
        self._specs: Dict[str, HookSpecification] = {}
    
    def register_hook(self, name: str, doc: str = None) -> HookSpecification:
        """
        Register a new hook specification.
        
        Args:
            name: Unique name for the hook
            doc: Documentation string for the hook
            
        Returns:
            The created hook specification
            
        Raises:
            ValueError: If a hook with this name already exists
        """
        if name in self._specs:
            raise ValueError(f"Hook '{name}' already registered")
            
        spec = HookSpecification(name, doc)
        self._specs[name] = spec
        return spec
    
    def unregister_hook(self, name: str) -> bool:
        """
        Unregister a hook specification.
        
        Args:
            name: Name of the hook to unregister
            
        Returns:
            True if the hook was unregistered, False if it didn't exist
        """
        if name in self._specs:
            del self._specs[name]
            return True
        return False
    
    def get_hook(self, name: str) -> Optional[HookSpecification]:
        """
        Get a hook specification by name.
        
        Args:
            name: Name of the hook
            
        Returns:
            The hook specification, or None if it doesn't exist
        """
        return self._specs.get(name)
    
    def hook_exists(self, name: str) -> bool:
        """
        Check if a hook with the given name exists.
        
        Args:
            name: Name of the hook
            
        Returns:
            True if the hook exists, False otherwise
        """
        return name in self._specs
    
    def add_implementation(self, hook_name: str, impl: Callable) -> bool:
        """
        Add an implementation to a hook.
        
        Args:
            hook_name: Name of the hook
            impl: Implementation function or method
            
        Returns:
            True if the implementation was added, False if the hook doesn't exist
        """
        spec = self.get_hook(hook_name)
        if spec:
            spec.add_implementation(impl)
            return True
        return False
    
    def remove_implementation(self, hook_name: str, impl: Callable) -> bool:
        """
        Remove an implementation from a hook.
        
        Args:
            hook_name: Name of the hook
            impl: Implementation to remove
            
        Returns:
            True if the implementation was removed, False otherwise
        """
        spec = self.get_hook(hook_name)
        if spec:
            return spec.remove_implementation(impl)
        return False
    
    def get_implementations(self, hook_name: str) -> List[Callable]:
        """
        Get all implementations for a hook.
        
        Args:
            hook_name: Name of the hook
            
        Returns:
            List of implementations, empty if the hook doesn't exist
        """
        spec = self.get_hook(hook_name)
        if spec:
            return spec.implementations.copy()
        return []
    
    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Execute all implementations of a hook and collect their results.
        
        Args:
            hook_name: Name of the hook
            *args: Positional arguments to pass to the implementations
            **kwargs: Keyword arguments to pass to the implementations
            
        Returns:
            List of results from all implementations
        """
        implementations = self.get_implementations(hook_name)
        results = []
        
        for impl in implementations:
            results.append(impl(*args, **kwargs))
        
        return results
    
    def execute_hook_first_result(self, hook_name: str, *args, **kwargs) -> Optional[Any]:
        """
        Execute implementations of a hook until one returns a non-None result.
        
        Args:
            hook_name: Name of the hook
            *args: Positional arguments to pass to the implementations
            **kwargs: Keyword arguments to pass to the implementations
            
        Returns:
            First non-None result, or None if all implementations return None
        """
        implementations = self.get_implementations(hook_name)
        
        for impl in implementations:
            result = impl(*args, **kwargs)
            if result is not None:
                return result
        
        return None
    
    def execute_hook_until(self, hook_name: str, predicate: Callable[[Any], bool], 
                          *args, **kwargs) -> Optional[Any]:
        """
        Execute implementations until one produces a result that satisfies the predicate.
        
        Args:
            hook_name: Name of the hook
            predicate: Function that evaluates results
            *args: Positional arguments to pass to the implementations
            **kwargs: Keyword arguments to pass to the implementations
            
        Returns:
            First result that satisfies the predicate, or None if none do
        """
        implementations = self.get_implementations(hook_name)
        
        for impl in implementations:
            result = impl(*args, **kwargs)
            if predicate(result):
                return result
        
        return None
    
    def get_all_hooks(self) -> Dict[str, HookSpecification]:
        """
        Get all registered hooks.
        
        Returns:
            Dictionary mapping hook names to specifications
        """
        return self._specs.copy()


# Global hook registry instance
global_hook_registry = HookRegistry()


def register_hook(name: str, doc: str = None) -> HookSpecification:
    """
    Register a new hook in the global registry.
    
    Args:
        name: Unique name for the hook
        doc: Documentation string for the hook
        
    Returns:
        The created hook specification
    """
    return global_hook_registry.register_hook(name, doc)


def hook_impl(hook_name: str) -> Callable[[Callable], Callable]:
    """
    Decorator for registering a function as a hook implementation.
    
    Args:
        hook_name: Name of the hook to implement
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        global_hook_registry.add_implementation(hook_name, func)
        return func
    return decorator


class HookCaller:
    """
    Utility class for calling hooks with a fluent interface.
    
    This class provides a more convenient way to execute hooks and
    process their results.
    """
    
    def __init__(self, registry: HookRegistry, hook_name: str):
        """
        Initialize a hook caller.
        
        Args:
            registry: Hook registry to use
            hook_name: Name of the hook to call
        """
        self.registry = registry
        self.hook_name = hook_name
    
    def call(self, *args, **kwargs) -> List[Any]:
        """
        Call all implementations and return all results.
        
        Args:
            *args: Positional arguments for the implementations
            **kwargs: Keyword arguments for the implementations
            
        Returns:
            List of results from all implementations
        """
        return self.registry.execute_hook(self.hook_name, *args, **kwargs)
    
    def call_first(self, *args, **kwargs) -> Optional[Any]:
        """
        Call implementations until one returns a non-None result.
        
        Args:
            *args: Positional arguments for the implementations
            **kwargs: Keyword arguments for the implementations
            
        Returns:
            First non-None result, or None if all implementations return None
        """
        return self.registry.execute_hook_first_result(self.hook_name, *args, **kwargs)
    
    def call_until(self, predicate: Callable[[Any], bool], *args, **kwargs) -> Optional[Any]:
        """
        Call implementations until one produces a result that satisfies the predicate.
        
        Args:
            predicate: Function that evaluates results
            *args: Positional arguments for the implementations
            **kwargs: Keyword arguments for the implementations
            
        Returns:
            First result that satisfies the predicate, or None if none do
        """
        return self.registry.execute_hook_until(self.hook_name, predicate, *args, **kwargs)
    
    def call_with_reduction(self, reducer: Callable[[Any, Any], Any], 
                           initial: Any, *args, **kwargs) -> Any:
        """
        Call all implementations and reduce their results using a reducer function.
        
        Args:
            reducer: Function to reduce results
            initial: Initial value for reduction
            *args: Positional arguments for the implementations
            **kwargs: Keyword arguments for the implementations
            
        Returns:
            Reduced result
        """
        results = self.call(*args, **kwargs)
        return reduce_results(results, reducer, initial)


def reduce_results(results: List[Any], reducer: Callable[[Any, Any], Any], initial: Any) -> Any:
    """
    Reduce a list of results using a reducer function.
    
    Args:
        results: List of results to reduce
        reducer: Function to reduce results
        initial: Initial value for reduction
        
    Returns:
        Reduced result
    """
    value = initial
    for result in results:
        value = reducer(value, result)
    return value


def hook_caller(hook_name: str) -> HookCaller:
    """
    Get a hook caller for the specified hook using the global registry.
    
    Args:
        hook_name: Name of the hook
        
    Returns:
        HookCaller instance
    """
    return HookCaller(global_hook_registry, hook_name)


# Define core hooks
register_hook("core.initialize", 
             "Called during core system initialization before any modules are loaded")

register_hook("core.shutdown", 
             "Called during system shutdown")

register_hook("task.validate", 
             "Called to validate a task before creation or update")

register_hook("task.pre_create", 
             "Called before a task is created")

register_hook("task.post_create", 
             "Called after a task is created")

register_hook("task.pre_update", 
             "Called before a task is updated")

register_hook("task.post_update", 
             "Called after a task is updated")

register_hook("task.status_change", 
             "Called when a task's status is changed")

register_hook("search.pre_query", 
             "Called before a search query is executed")

register_hook("search.post_query", 
             "Called after a search query is executed to filter or modify results")

register_hook("ui.dashboard.render", 
             "Called when dashboard components are being rendered")

register_hook("ui.task_view.render", 
             "Called when a task view is being rendered") 