"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/di/service_provider.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CoreManager: Uses for application service bootstrapping
    - Application: Main entry point uses for service configuration
    - PluginSystem: Uses to access core services
    - CommandSystem: Uses to resolve command dependencies
    - TestFramework: Uses for test service configuration

Purpose:
    Provides a higher-level API around the dependency injection container
    that simplifies service registration, bootstrapping, and resolution
    for application-level service management. Includes factory methods
    for common service configuration patterns.

Requirements:
    - Must provide a fluent interface for service registration
    - Must support registration of common service types
    - Must offer simplified access to the container's capabilities
    - Must include factory methods for standard application services
    - CRITICAL: Must follow consistent registration patterns
    - CRITICAL: Must maintain order-independent registration
    - CRITICAL: Must provide clear error messages for failed resolutions

Service Provider Module

This module provides a higher-level API for the dependency injection container
with a focus on application-level registration and bootstrapping.
"""
from typing import Optional, Any, Type, TypeVar, Callable, Dict
from .container import ServiceContainer, ServiceLifetime, ServiceResolver
from ..config import ConfigManager, create_default_config
from ..logging import get_logger, Logger

T = TypeVar('T')


class ServiceCollection:
    """
    A builder for the ServiceProvider that allows for fluent registration.
    
    This class provides a more user-friendly API for registering services.
    """
    
    def __init__(self):
        """Initialize the service collection."""
        self._container = ServiceContainer()
    
    def add_singleton(self, service_type: Type[T], implementation_type: Optional[Type] = None) -> 'ServiceCollection':
        """
        Register a singleton service.
        
        Args:
            service_type: The type of service to register
            implementation_type: The implementation type (defaults to service_type if None)
            
        Returns:
            The service collection for chaining
        """
        self._container.register_type(
            service_type=service_type,
            implementation_type=implementation_type or service_type,
            lifetime=ServiceLifetime.SINGLETON
        )
        return self
    
    def add_transient(self, service_type: Type[T], implementation_type: Optional[Type] = None) -> 'ServiceCollection':
        """
        Register a transient service.
        
        Args:
            service_type: The type of service to register
            implementation_type: The implementation type (defaults to service_type if None)
            
        Returns:
            The service collection for chaining
        """
        self._container.register_type(
            service_type=service_type,
            implementation_type=implementation_type or service_type,
            lifetime=ServiceLifetime.TRANSIENT
        )
        return self
    
    def add_singleton_factory(self, service_type: Type[T], 
                           factory: Callable[[ServiceResolver], T]) -> 'ServiceCollection':
        """
        Register a singleton service with a factory.
        
        Args:
            service_type: The type of service to register
            factory: Factory function to create the service
            
        Returns:
            The service collection for chaining
        """
        self._container.register_factory(
            service_type=service_type,
            factory=factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        return self
    
    def add_transient_factory(self, service_type: Type[T], 
                           factory: Callable[[ServiceResolver], T]) -> 'ServiceCollection':
        """
        Register a transient service with a factory.
        
        Args:
            service_type: The type of service to register
            factory: Factory function to create the service
            
        Returns:
            The service collection for chaining
        """
        self._container.register_factory(
            service_type=service_type,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT
        )
        return self
    
    def add_instance(self, service_type: Type[T], instance: T) -> 'ServiceCollection':
        """
        Register an existing instance.
        
        Args:
            service_type: The type of service to register
            instance: The instance to register
            
        Returns:
            The service collection for chaining
        """
        self._container.register_instance(service_type, instance)
        return self
    
    def build_service_provider(self) -> 'ServiceProvider':
        """
        Build a ServiceProvider with all registered services.
        
        Returns:
            A new ServiceProvider
        """
        return ServiceProvider(self._container)


class ServiceProvider:
    """
    A higher-level API for the dependency injection container.
    
    This class wraps the ServiceContainer to provide a more user-friendly API.
    """
    
    def __init__(self, container: ServiceContainer):
        """
        Initialize the service provider.
        
        Args:
            container: The underlying container
        """
        self._container = container
    
    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service of the specified type.
        
        Args:
            service_type: The type of service to get
            
        Returns:
            An instance of the service
            
        Raises:
            ConfigurationError: If the service is not registered
        """
        return self._container.resolve(service_type)
    
    def get_service_optional(self, service_type: Type[T]) -> Optional[T]:
        """
        Get a service of the specified type, or None if not registered.
        
        Args:
            service_type: The type of service to get
            
        Returns:
            An instance of the service or None
        """
        return self._container.try_resolve(service_type)
    
    def get_services(self, service_type: Type[T]) -> list[T]:
        """
        Get all services of the specified type.
        
        Args:
            service_type: The type of service to get
            
        Returns:
            A list of service instances
        """
        return self._container.resolve_all(service_type)


def create_default_service_provider(config_manager: Optional[ConfigManager] = None) -> ServiceProvider:
    """
    Create a default service provider with common services.
    
    Args:
        config_manager: Optional configuration manager to use
        
    Returns:
        A new ServiceProvider with common services registered
    """
    services = ServiceCollection()
    
    # Register configuration
    if config_manager is None:
        config_manager = create_default_config()
    
    services.add_instance(ConfigManager, config_manager)
    
    # Register logging
    logger = get_logger('clickup_json_manager')
    services.add_instance(Logger, logger)
    
    # Build the service provider
    return services.build_service_provider() 