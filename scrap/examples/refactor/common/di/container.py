"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/di/container.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - ServiceProvider: Builds on the container for higher-level services
    - CoreManager: Uses for service dependency management
    - PluginSystem: Uses for plugin service registration
    - CommandSystem: Uses for service access in commands
    - TestFramework: Uses for service mocking and test isolation

Purpose:
    Implements a lightweight dependency injection container that
    supports service registration, dependency resolution, and 
    lifecycle management (singleton/transient). Provides the core 
    infrastructure for application service management.

Requirements:
    - Must support registration by type with implementation type
    - Must support registration by factory function
    - Must support singleton and transient lifetimes
    - Must resolve dependencies for constructor injection
    - Must detect and prevent circular dependencies
    - CRITICAL: Must be thread-safe for singleton resolution
    - CRITICAL: Must maintain consistent resolution order
    - CRITICAL: Must support service scoping

Dependency Injection Container Module

This module provides a simple dependency injection container system for the ClickUp JSON Manager with:
- Service registration with different lifetimes (singleton, transient)
- Factory registration
- Dependency resolution
- Circular dependency detection
"""
from typing import Dict, Any, Optional, List, Type, TypeVar, Callable, Generic, cast
from enum import Enum
from ..exceptions import ConfigurationError

T = TypeVar('T')
TService = TypeVar('TService')
TImpl = TypeVar('TImpl')


class ServiceLifetime(Enum):
    """Defines the lifetime of a registered service."""
    
    # A new instance is created for each resolution
    TRANSIENT = 1
    
    # A single instance is created and reused for all resolutions
    SINGLETON = 2


class ServiceDescriptor(Generic[TService, TImpl]):
    """Describes a service registration."""
    
    def __init__(self, 
                 service_type: Type[TService],
                 implementation_type: Optional[Type[TImpl]] = None,
                 factory: Optional[Callable[['ServiceResolver'], TService]] = None,
                 lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT):
        """
        Initialize a service descriptor.
        
        Args:
            service_type: The service type (interface)
            implementation_type: The implementation type (concrete class)
            factory: Factory function to create the service
            lifetime: The service lifetime
        """
        self.service_type = service_type
        self.implementation_type = implementation_type
        self.factory = factory
        self.lifetime = lifetime
        
        # Only one of implementation_type or factory must be provided
        if implementation_type is None and factory is None:
            raise ConfigurationError(
                "Either implementation_type or factory must be provided")
        if implementation_type is not None and factory is not None:
            raise ConfigurationError(
                "Only one of implementation_type or factory can be provided")


class ServiceRegistration:
    """Service registration interface for the container."""
    
    def register(self, descriptor: ServiceDescriptor) -> None:
        """
        Register a service with the container.
        
        Args:
            descriptor: The service descriptor
        """
        pass
    
    def register_type(self, service_type: Type[TService], 
                      implementation_type: Type[TImpl], 
                      lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """
        Register a service type with an implementation type.
        
        Args:
            service_type: The service type (interface)
            implementation_type: The implementation type (concrete class)
            lifetime: The service lifetime
        """
        pass
    
    def register_factory(self, service_type: Type[TService], 
                         factory: Callable[['ServiceResolver'], TService], 
                         lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """
        Register a service type with a factory function.
        
        Args:
            service_type: The service type (interface)
            factory: Factory function to create the service
            lifetime: The service lifetime
        """
        pass
    
    def register_instance(self, service_type: Type[TService], instance: TService) -> None:
        """
        Register a service type with an existing instance.
        
        Args:
            service_type: The service type (interface)
            instance: The service instance
        """
        pass


class ServiceResolver:
    """Service resolution interface for the container."""
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service from the container.
        
        Args:
            service_type: The service type to resolve
            
        Returns:
            An instance of the service
        """
        pass
    
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to resolve a service from the container.
        
        Args:
            service_type: The service type to resolve
            
        Returns:
            An instance of the service or None if not registered
        """
        pass
    
    def resolve_all(self, service_type: Type[T]) -> List[T]:
        """
        Resolve all services of a given type from the container.
        
        Args:
            service_type: The service type to resolve
            
        Returns:
            A list of service instances
        """
        pass


class ServiceContainer(ServiceRegistration, ServiceResolver):
    """
    A simple dependency injection container.
    
    This container provides service registration and resolution capabilities.
    """
    
    def __init__(self):
        """Initialize the container."""
        # Dictionary of service descriptors by service type
        self._descriptors: Dict[Type, List[ServiceDescriptor]] = {}
        
        # Dictionary of singleton instances by service descriptor
        self._instances: Dict[ServiceDescriptor, Any] = {}
        
        # Stack of types being resolved (for circular dependency detection)
        self._resolution_stack: List[Type] = []
    
    def register(self, descriptor: ServiceDescriptor) -> None:
        """Register a service with the container."""
        service_type = descriptor.service_type
        
        if service_type not in self._descriptors:
            self._descriptors[service_type] = []
            
        self._descriptors[service_type].append(descriptor)
    
    def register_type(self, service_type: Type[TService], 
                      implementation_type: Type[TImpl], 
                      lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """Register a service type with an implementation type."""
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            lifetime=lifetime
        )
        self.register(descriptor)
    
    def register_factory(self, service_type: Type[TService], 
                         factory: Callable[['ServiceResolver'], TService], 
                         lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """Register a service type with a factory function."""
        descriptor = ServiceDescriptor(
            service_type=service_type,
            factory=factory,
            lifetime=lifetime
        )
        self.register(descriptor)
    
    def register_instance(self, service_type: Type[TService], instance: TService) -> None:
        """Register a service type with an existing instance."""
        # Create a factory that returns the instance
        factory = lambda _: instance
        
        descriptor = ServiceDescriptor(
            service_type=service_type,
            factory=factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        self.register(descriptor)
        
        # Add the instance to the cache
        self._instances[descriptor] = instance
    
    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service from the container."""
        # Check for circular dependencies
        if service_type in self._resolution_stack:
            chain = " -> ".join([t.__name__ for t in self._resolution_stack]) + f" -> {service_type.__name__}"
            raise ConfigurationError(f"Circular dependency detected: {chain}")
        
        # Check if the service type is registered
        if service_type not in self._descriptors or not self._descriptors[service_type]:
            raise ConfigurationError(f"Service '{service_type.__name__}' is not registered")
        
        # Use the last registered descriptor (allowing overrides)
        descriptor = self._descriptors[service_type][-1]
        
        # Add to resolution stack
        self._resolution_stack.append(service_type)
        
        try:
            # Check if there's an instance for singleton
            if descriptor.lifetime == ServiceLifetime.SINGLETON and descriptor in self._instances:
                return cast(T, self._instances[descriptor])
            
            # Create the instance
            instance = self._create_instance(descriptor)
            
            # Cache singleton instances
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                self._instances[descriptor] = instance
                
            return instance
        finally:
            # Remove from resolution stack
            self._resolution_stack.pop()
    
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """Try to resolve a service from the container."""
        try:
            return self.resolve(service_type)
        except ConfigurationError:
            return None
    
    def resolve_all(self, service_type: Type[T]) -> List[T]:
        """Resolve all services of a given type from the container."""
        if service_type not in self._descriptors:
            return []
            
        instances: List[T] = []
        
        # Add to resolution stack
        self._resolution_stack.append(service_type)
        
        try:
            for descriptor in self._descriptors[service_type]:
                # Check if there's an instance for singleton
                if descriptor.lifetime == ServiceLifetime.SINGLETON and descriptor in self._instances:
                    instances.append(cast(T, self._instances[descriptor]))
                    continue
                
                # Create the instance
                instance = self._create_instance(descriptor)
                
                # Cache singleton instances
                if descriptor.lifetime == ServiceLifetime.SINGLETON:
                    self._instances[descriptor] = instance
                    
                instances.append(instance)
                
            return instances
        finally:
            # Remove from resolution stack
            self._resolution_stack.pop()
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create an instance from a service descriptor."""
        # Use factory if provided
        if descriptor.factory is not None:
            return descriptor.factory(self)
        
        # Otherwise use implementation type
        impl_type = descriptor.implementation_type
        if impl_type is None:
            raise ConfigurationError("Implementation type is not provided")
        
        # Check if the implementation has a constructor
        if not hasattr(impl_type, "__init__"):
            return impl_type()
        
        # Get constructor parameter hints
        from inspect import signature
        sig = signature(impl_type.__init__)
        
        # Skip self parameter
        params = list(sig.parameters.items())[1:]
        
        # Build arguments by resolving dependencies
        args = {}
        for param_name, param in params:
            if param.annotation == param.empty:
                # No type annotation, can't resolve
                raise ConfigurationError(
                    f"Parameter '{param_name}' of '{impl_type.__name__}' has no type annotation")
            
            # Resolve the dependency
            args[param_name] = self.resolve(param.annotation)
        
        # Create the instance with dependencies
        return impl_type(**args) 