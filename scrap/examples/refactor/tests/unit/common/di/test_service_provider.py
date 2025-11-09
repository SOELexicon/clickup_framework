"""
Unit tests for the service provider.

This module tests the functionality of the service provider components:
- ServiceCollection fluent API
- ServiceProvider wrapper
- Default service provider creation
"""
import unittest
from unittest.mock import MagicMock, patch

from refactor.common.di import (
    ServiceCollection,
    ServiceProvider,
    ServiceLifetime,
    ServiceContainer,
    create_default_service_provider
)
from refactor.common.config import ConfigManager
from refactor.common.logging import Logger


# Test interfaces and implementations
class IService:
    """Test service interface."""
    def get_value(self) -> str:
        """Get a value."""
        pass


class SimpleService(IService):
    """Simple implementation of IService."""
    def __init__(self):
        """Initialize with no parameters."""
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


class TestServiceCollection(unittest.TestCase):
    """Tests for the ServiceCollection class."""
    
    def setUp(self):
        """Set up a new collection for each test."""
        self.services = ServiceCollection()
    
    def test_add_singleton(self):
        """Test adding a singleton service."""
        # Add a singleton service using a factory function
        result = self.services.add_singleton_factory(IService, lambda resolver: SimpleService())
        
        # Should return self for fluent API
        self.assertIs(result, self.services)
        
        # Build a service provider
        provider = self.services.build_service_provider()
        
        # Resolve the service twice
        service1 = provider.get_service(IService)
        service2 = provider.get_service(IService)
        
        # Verify they are the same instance
        self.assertIs(service1, service2)
        self.assertIsInstance(service1, SimpleService)
    
    def test_add_singleton_same_type(self):
        """Test adding a singleton where service type and implementation type are the same."""
        # Add a singleton service using a factory function
        result = self.services.add_singleton_factory(SimpleService, lambda resolver: SimpleService())
        
        # Should return self for fluent API
        self.assertIs(result, self.services)
        
        # Build a service provider
        provider = self.services.build_service_provider()
        
        # Resolve the service
        service = provider.get_service(SimpleService)
        
        # Verify it's the correct type
        self.assertIsInstance(service, SimpleService)
    
    def test_add_transient(self):
        """Test adding a transient service."""
        # Add a transient service using a factory function
        result = self.services.add_transient_factory(IService, lambda resolver: SimpleService())
        
        # Should return self for fluent API
        self.assertIs(result, self.services)
        
        # Build a service provider
        provider = self.services.build_service_provider()
        
        # Resolve the service twice
        service1 = provider.get_service(IService)
        service2 = provider.get_service(IService)
        
        # Verify they are different instances
        self.assertIsNot(service1, service2)
        self.assertIsInstance(service1, SimpleService)
        self.assertIsInstance(service2, SimpleService)
    
    def test_add_transient_same_type(self):
        """Test adding a transient where service type and implementation type are the same."""
        # Add a transient service using a factory function
        result = self.services.add_transient_factory(SimpleService, lambda resolver: SimpleService())
        
        # Should return self for fluent API
        self.assertIs(result, self.services)
        
        # Build a service provider
        provider = self.services.build_service_provider()
        
        # Resolve the service
        service = provider.get_service(SimpleService)
        
        # Verify it's the correct type
        self.assertIsInstance(service, SimpleService)
    
    def test_add_singleton_factory(self):
        """Test adding a singleton with a factory."""
        # Create a factory that tracks how many times it's called
        call_count = 0
        
        def factory(resolver):
            nonlocal call_count
            call_count += 1
            return SimpleService()
        
        # Add a singleton factory
        result = self.services.add_singleton_factory(IService, factory)
        
        # Should return self for fluent API
        self.assertIs(result, self.services)
        
        # Build a service provider
        provider = self.services.build_service_provider()
        
        # Resolve the service twice
        service1 = provider.get_service(IService)
        service2 = provider.get_service(IService)
        
        # Verify they are the same instance and the factory was called once
        self.assertIs(service1, service2)
        self.assertIsInstance(service1, SimpleService)
        self.assertEqual(call_count, 1)
    
    def test_add_transient_factory(self):
        """Test adding a transient with a factory."""
        # Create a factory that tracks how many times it's called
        call_count = 0
        
        def factory(resolver):
            nonlocal call_count
            call_count += 1
            return SimpleService()
        
        # Add a transient factory
        result = self.services.add_transient_factory(IService, factory)
        
        # Should return self for fluent API
        self.assertIs(result, self.services)
        
        # Build a service provider
        provider = self.services.build_service_provider()
        
        # Resolve the service twice
        service1 = provider.get_service(IService)
        service2 = provider.get_service(IService)
        
        # Verify they are different instances and the factory was called twice
        self.assertIsNot(service1, service2)
        self.assertIsInstance(service1, SimpleService)
        self.assertIsInstance(service2, SimpleService)
        self.assertEqual(call_count, 2)
    
    def test_add_instance(self):
        """Test adding an existing instance."""
        # Create an instance
        instance = SimpleService()
        
        # Add the instance
        result = self.services.add_instance(IService, instance)
        
        # Should return self for fluent API
        self.assertIs(result, self.services)
        
        # Build a service provider
        provider = self.services.build_service_provider()
        
        # Resolve the service
        service = provider.get_service(IService)
        
        # Verify it's the same instance
        self.assertIs(service, instance)
    
    def test_fluent_api_chaining(self):
        """Test chaining multiple registrations with the fluent API."""
        # Add multiple services with chaining, using factories for type safety
        self.services.add_singleton_factory(IService, lambda resolver: SimpleService()) \
            .add_transient_factory(ComplexService, lambda resolver: ComplexService(SimpleService())) \
            .add_instance(str, "test")
        
        # Build a service provider
        provider = self.services.build_service_provider()
        
        # Verify all services were registered
        service1 = provider.get_service(IService)
        service2 = provider.get_service(ComplexService)
        service3 = provider.get_service(str)
        
        # Verify they are the correct types
        self.assertIsInstance(service1, SimpleService)
        self.assertIsInstance(service2, ComplexService)
        self.assertEqual(service3, "test")


class TestServiceProvider(unittest.TestCase):
    """Tests for the ServiceProvider class."""
    
    def setUp(self):
        """Set up a new service provider for each test."""
        # Create a service provider with some test services
        self.container = ServiceContainer()
        # Use factory registration to avoid type annotation issues
        self.container.register_factory(IService, lambda resolver: SimpleService())
        self.provider = ServiceProvider(self.container)
    
    def test_get_service(self):
        """Test getting a service from the provider."""
        # Get a service
        service = self.provider.get_service(IService)
        
        # Verify it's the correct type
        self.assertIsInstance(service, SimpleService)
    
    def test_get_service_optional_exists(self):
        """Test getting an optional service that exists."""
        # Get an optional service that exists
        service = self.provider.get_service_optional(IService)
        
        # Verify it's the correct type
        self.assertIsInstance(service, SimpleService)
    
    def test_get_service_optional_missing(self):
        """Test getting an optional service that doesn't exist."""
        # Get an optional service that doesn't exist
        service = self.provider.get_service_optional(ComplexService)
        
        # Verify it's None
        self.assertIsNone(service)
    
    def test_get_services(self):
        """Test getting all services of a type."""
        # Register multiple implementations using factories
        self.container.register_factory(
            IService, 
            lambda resolver: ComplexService(SimpleService())
        )
        
        # Get all services
        services = self.provider.get_services(IService)
        
        # Verify we got all implementations
        self.assertEqual(len(services), 2)
        self.assertIsInstance(services[0], SimpleService)
        self.assertIsInstance(services[1], ComplexService)
    
    def test_get_services_empty(self):
        """Test getting all services of a type that has no implementations."""
        # Get all services of a type that has no implementations
        services = self.provider.get_services(ComplexService)
        
        # Verify we got an empty list
        self.assertEqual(len(services), 0)


class TestDefaultServiceProvider(unittest.TestCase):
    """Tests for the create_default_service_provider function."""
    
    @patch('refactor.common.di.service_provider.create_default_config')
    @patch('refactor.common.di.service_provider.get_logger')
    def test_create_default_provider(self, mock_get_logger, mock_create_default_config):
        """Test creating a default service provider."""
        # Mock the dependencies
        mock_config = MagicMock(spec=ConfigManager)
        mock_create_default_config.return_value = mock_config
        
        mock_logger = MagicMock(spec=Logger)
        mock_get_logger.return_value = mock_logger
        
        # Create a default service provider
        provider = create_default_service_provider()
        
        # Verify the required services are registered
        config = provider.get_service(ConfigManager)
        logger = provider.get_service(Logger)
        
        # Verify they are the mocked instances
        self.assertIs(config, mock_config)
        self.assertIs(logger, mock_logger)
    
    def test_create_with_custom_config(self):
        """Test creating a default service provider with a custom config."""
        # Create a custom config
        custom_config = MagicMock(spec=ConfigManager)
        
        # Create a default service provider with the custom config
        provider = create_default_service_provider(custom_config)
        
        # Verify the config is the custom one
        config = provider.get_service(ConfigManager)
        self.assertIs(config, custom_config)


if __name__ == "__main__":
    unittest.main() 