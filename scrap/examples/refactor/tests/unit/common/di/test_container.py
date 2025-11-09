"""
Unit tests for the dependency injection container.

This module tests the functionality of the DI container components:
- Service registration with different lifetimes
- Service resolution
- Factory-based service creation
- Instance registration
- Circular dependency detection
"""
import unittest
from typing import List, Optional

from refactor.common.di import (
    ServiceContainer,
    ServiceLifetime,
    ServiceDescriptor
)
from refactor.common.exceptions import ConfigurationError


# Test interfaces and implementations
class IService:
    """Test service interface."""
    def get_value(self) -> str:
        """Get a value."""
        pass


class SimpleService(IService):
    """Simple implementation of IService."""
    def __init__(self):
        """Initialize the service with no parameters."""
        pass
    
    def get_value(self) -> str:
        """Get a simple value."""
        return "Simple"


class ComplexService(IService):
    """Complex implementation of IService that depends on another service."""
    def __init__(self, dependency: IService):
        """Initialize with a dependency."""
        self.dependency = dependency
    
    def get_value(self) -> str:
        """Get a value that includes the dependency's value."""
        return f"Complex({self.dependency.get_value()})"


class ParameterizedService(IService):
    """A service with constructor parameters."""
    def __init__(self, name: str, count: int = 0):
        """Initialize with parameters."""
        self.name = name
        self.count = count
    
    def get_value(self) -> str:
        """Get a value based on the parameters."""
        return f"{self.name}({self.count})"


class CircularService1:
    """Service that creates a circular dependency."""
    def __init__(self, service: 'CircularService2'):
        """Initialize with a dependency that creates a circular reference."""
        self.service = service


class CircularService2:
    """Service that creates a circular dependency."""
    def __init__(self, service: 'CircularService1'):
        """Initialize with a dependency that creates a circular reference."""
        self.service = service


class ListLogger:
    """A simple logger that records events in a list."""
    def __init__(self):
        """Initialize the logger."""
        self.logs: List[str] = []
    
    def log(self, message: str) -> None:
        """Log a message."""
        self.logs.append(message)


class ServiceWithLogger:
    """A service that uses a logger."""
    def __init__(self, logger: ListLogger):
        """Initialize with a logger."""
        self.logger = logger
        self.logger.log("ServiceWithLogger created")
    
    def do_something(self) -> None:
        """Do something and log it."""
        self.logger.log("ServiceWithLogger.do_something called")


class TestServiceDescriptor(unittest.TestCase):
    """Tests for the ServiceDescriptor class."""
    
    def test_init_with_implementation(self):
        """Test initializing a descriptor with an implementation type."""
        descriptor = ServiceDescriptor(
            service_type=IService,
            implementation_type=SimpleService,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        self.assertEqual(descriptor.service_type, IService)
        self.assertEqual(descriptor.implementation_type, SimpleService)
        self.assertIsNone(descriptor.factory)
        self.assertEqual(descriptor.lifetime, ServiceLifetime.SINGLETON)
    
    def test_init_with_factory(self):
        """Test initializing a descriptor with a factory function."""
        factory = lambda resolver: SimpleService()
        
        descriptor = ServiceDescriptor(
            service_type=IService,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT
        )
        
        self.assertEqual(descriptor.service_type, IService)
        self.assertIsNone(descriptor.implementation_type)
        self.assertEqual(descriptor.factory, factory)
        self.assertEqual(descriptor.lifetime, ServiceLifetime.TRANSIENT)
    
    def test_init_invalid_missing_both(self):
        """Test that providing neither implementation nor factory raises an error."""
        with self.assertRaises(ConfigurationError):
            ServiceDescriptor(
                service_type=IService
            )
    
    def test_init_invalid_both_provided(self):
        """Test that providing both implementation and factory raises an error."""
        with self.assertRaises(ConfigurationError):
            ServiceDescriptor(
                service_type=IService,
                implementation_type=SimpleService,
                factory=lambda resolver: SimpleService()
            )


class TestServiceContainer(unittest.TestCase):
    """Tests for the ServiceContainer class."""
    
    def setUp(self):
        """Set up a new container for each test."""
        self.container = ServiceContainer()
    
    def test_register_type_and_resolve(self):
        """Test registering a type and resolving it."""
        # Register a service
        self.container.register_type(IService, SimpleService)
        
        # Resolve the service
        service = self.container.resolve(IService)
        
        # Verify it's the correct type
        self.assertIsInstance(service, SimpleService)
        self.assertEqual(service.get_value(), "Simple")
    
    def test_register_and_resolve_concrete_type(self):
        """Test registering and resolving a concrete type."""
        # Register a concrete service as itself
        self.container.register_type(SimpleService, SimpleService)
        
        # Resolve the service
        service = self.container.resolve(SimpleService)
        
        # Verify it's the correct type
        self.assertIsInstance(service, SimpleService)
        self.assertEqual(service.get_value(), "Simple")
    
    def test_transient_lifetime(self):
        """Test transient lifetime creates new instances each time."""
        # Register a service as transient
        self.container.register_type(
            IService, SimpleService, ServiceLifetime.TRANSIENT)
        
        # Resolve the service twice
        service1 = self.container.resolve(IService)
        service2 = self.container.resolve(IService)
        
        # Verify they are different instances
        self.assertIsNot(service1, service2)
    
    def test_singleton_lifetime(self):
        """Test singleton lifetime reuses the same instance."""
        # Register a service as singleton
        self.container.register_type(
            IService, SimpleService, ServiceLifetime.SINGLETON)
        
        # Resolve the service twice
        service1 = self.container.resolve(IService)
        service2 = self.container.resolve(IService)
        
        # Verify they are the same instance
        self.assertIs(service1, service2)
    
    def test_register_factory(self):
        """Test registering a factory function."""
        # Create a factory that tracks how many times it's called
        call_count = 0
        
        def factory(resolver):
            nonlocal call_count
            call_count += 1
            return SimpleService()
        
        # Register the factory
        self.container.register_factory(IService, factory)
        
        # Resolve the service
        service = self.container.resolve(IService)
        
        # Verify it's the correct type and the factory was called
        self.assertIsInstance(service, SimpleService)
        self.assertEqual(call_count, 1)
    
    def test_factory_singleton(self):
        """Test a factory with singleton lifetime."""
        # Create a factory that tracks how many times it's called
        call_count = 0
        
        def factory(resolver):
            nonlocal call_count
            call_count += 1
            return SimpleService()
        
        # Register the factory as singleton
        self.container.register_factory(
            IService, factory, ServiceLifetime.SINGLETON)
        
        # Resolve the service twice
        service1 = self.container.resolve(IService)
        service2 = self.container.resolve(IService)
        
        # Verify they are the same instance and the factory was called once
        self.assertIs(service1, service2)
        self.assertEqual(call_count, 1)
    
    def test_factory_with_dependencies(self):
        """Test a factory that uses the resolver to get dependencies."""
        # Register a dependency - use factory to avoid type annotation issues
        self.container.register_factory(SimpleService, lambda resolver: SimpleService())
        
        # Create a factory that resolves a dependency
        def factory(resolver):
            simple_service = resolver.resolve(SimpleService)
            return ComplexService(simple_service)
        
        # Register the factory
        self.container.register_factory(IService, factory)
        
        # Resolve the service
        service = self.container.resolve(IService)
        
        # Verify it's the correct type and has the dependency
        self.assertIsInstance(service, ComplexService)
        self.assertIsInstance(service.dependency, SimpleService)
        self.assertEqual(service.get_value(), "Complex(Simple)")
    
    def test_register_instance(self):
        """Test registering an existing instance."""
        # Create an instance
        instance = SimpleService()
        
        # Register the instance
        self.container.register_instance(IService, instance)
        
        # Resolve the service
        service = self.container.resolve(IService)
        
        # Verify it's the same instance
        self.assertIs(service, instance)
    
    def test_dependency_resolution(self):
        """Test resolving a service with dependencies."""
        # Register dependencies using factories to avoid type annotation issues
        self.container.register_factory(SimpleService, lambda resolver: SimpleService())
        self.container.register_factory(ComplexService, lambda resolver: ComplexService(resolver.resolve(SimpleService)))
        
        # Resolve the complex service
        service = self.container.resolve(ComplexService)
        
        # Verify it's the correct type and has the dependency
        self.assertIsInstance(service, ComplexService)
        self.assertIsInstance(service.dependency, SimpleService)
        self.assertEqual(service.get_value(), "Complex(Simple)")
    
    def test_interface_dependency_resolution(self):
        """Test resolving a service with an interface dependency."""
        # Register IService -> SimpleService
        self.container.register_factory(IService, lambda resolver: SimpleService())
        
        # Create a factory that depends on IService
        def factory(resolver):
            service = resolver.resolve(IService)
            return ComplexService(service)
        
        # Register the factory
        self.container.register_factory(ComplexService, factory)
        
        # Resolve the complex service
        service = self.container.resolve(ComplexService)
        
        # Verify it's the correct type and has the dependency
        self.assertIsInstance(service, ComplexService)
        self.assertIsInstance(service.dependency, SimpleService)
        self.assertEqual(service.get_value(), "Complex(Simple)")
    
    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        # Register services that depend on each other using factories
        # to avoid type annotation issues with circular references
        self.container.register_factory(
            CircularService1, 
            lambda resolver: CircularService1(resolver.resolve(CircularService2))
        )
        self.container.register_factory(
            CircularService2, 
            lambda resolver: CircularService2(resolver.resolve(CircularService1))
        )
        
        # Resolve should detect the circular dependency
        with self.assertRaises(ConfigurationError) as context:
            self.container.resolve(CircularService1)
        
        # Verify the error message contains the dependency chain
        error_message = str(context.exception)
        self.assertIn("Circular dependency detected", error_message)
        self.assertIn("CircularService1", error_message)
        self.assertIn("CircularService2", error_message)
    
    def test_missing_service(self):
        """Test resolving a service that isn't registered."""
        # Try to resolve a service that isn't registered
        with self.assertRaises(ConfigurationError) as context:
            self.container.resolve(IService)
        
        # Verify the error message
        error_message = str(context.exception)
        self.assertIn("is not registered", error_message)
        self.assertIn("IService", error_message)
    
    def test_try_resolve(self):
        """Test the try_resolve method."""
        # Register a service
        self.container.register_factory(IService, lambda resolver: SimpleService())
        
        # Try to resolve the service
        service = self.container.try_resolve(IService)
        
        # Verify it's the correct type
        self.assertIsInstance(service, SimpleService)
        
        # Try to resolve a service that isn't registered
        service = self.container.try_resolve(ComplexService)
        
        # Verify it's None
        self.assertIsNone(service)
    
    def test_resolve_all(self):
        """Test the resolve_all method."""
        # Register multiple implementations of IService using factories
        self.container.register_factory(IService, lambda resolver: SimpleService())
        
        def factory(resolver):
            return ComplexService(SimpleService())
        
        self.container.register_factory(IService, factory)
        
        # Resolve all implementations
        services = self.container.resolve_all(IService)
        
        # Verify we got both implementations
        self.assertEqual(len(services), 2)
        self.assertIsInstance(services[0], SimpleService)
        self.assertIsInstance(services[1], ComplexService)
    
    def test_resolve_all_empty(self):
        """Test resolve_all with no registered services."""
        # Resolve all implementations of a service that isn't registered
        services = self.container.resolve_all(IService)
        
        # Verify we got an empty list
        self.assertEqual(len(services), 0)
    
    def test_shared_dependencies(self):
        """Test that singleton dependencies are shared."""
        # Register a logger as singleton
        logger = ListLogger()
        self.container.register_instance(ListLogger, logger)
        
        # Register a service that uses the logger
        self.container.register_factory(
            ServiceWithLogger, 
            lambda resolver: ServiceWithLogger(resolver.resolve(ListLogger))
        )
        
        # Resolve the service
        service1 = self.container.resolve(ServiceWithLogger)
        service2 = self.container.resolve(ServiceWithLogger)
        
        # Both services should use the same logger
        self.assertIs(service1.logger, logger)
        self.assertIs(service2.logger, logger)
        
        # Call a method on both services
        service1.do_something()
        service2.do_something()
        
        # Verify the logs
        self.assertEqual(logger.logs, [
            "ServiceWithLogger created",
            "ServiceWithLogger created",
            "ServiceWithLogger.do_something called",
            "ServiceWithLogger.do_something called"
        ])
    
    def test_override_registration(self):
        """Test that later registrations override earlier ones."""
        # Register a service
        self.container.register_factory(IService, lambda resolver: SimpleService())
        
        # Override with a different implementation
        def factory(resolver):
            return ComplexService(SimpleService())
        
        self.container.register_factory(IService, factory)
        
        # Resolve the service
        service = self.container.resolve(IService)
        
        # Verify it's the second registration
        self.assertIsInstance(service, ComplexService)
    
    def test_different_lifetime_doesnt_share(self):
        """Test that transient services don't share dependencies."""
        # Create a service that tracks its identity
        class IdentityService:
            counter = 0
            
            def __init__(self):
                type(self).counter += 1
                self.id = type(self).counter
        
        # Register it as transient using factory to avoid type annotation issues
        self.container.register_factory(
            IdentityService, 
            lambda resolver: IdentityService(),
            ServiceLifetime.TRANSIENT
        )
        
        # Create a service that depends on it
        class DependentService:
            def __init__(self, dependency: IdentityService):
                self.dependency = dependency
        
        # Register it as transient using factory to avoid type annotation issues
        self.container.register_factory(
            DependentService,
            lambda resolver: DependentService(resolver.resolve(IdentityService)),
            ServiceLifetime.TRANSIENT
        )
        
        # Resolve two instances
        service1 = self.container.resolve(DependentService)
        service2 = self.container.resolve(DependentService)
        
        # Verify they have different dependencies
        self.assertIsNot(service1.dependency, service2.dependency)
        self.assertNotEqual(service1.dependency.id, service2.dependency.id)


if __name__ == "__main__":
    unittest.main() 