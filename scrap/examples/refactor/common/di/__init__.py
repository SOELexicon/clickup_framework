"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/di/__init__.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CoreManager: Uses for core service management and bootstrapping
    - PluginSystem: Uses for plugin service registration
    - CommandSystem: Uses to access application services
    - RESTfulAPI: Uses for service dependency resolution
    - TestFramework: Uses for test service mocking

Purpose:
    Provides a complete dependency injection system that enables
    loose coupling between components, simplifies testing through
    service substitution, and centralizes application configuration.

Requirements:
    - Must support different service lifetimes (singleton, transient)
    - Must support registration by type, factory, and instance
    - Must detect circular dependencies during resolution
    - Must provide both low-level container and high-level provider APIs
    - CRITICAL: Must properly dispose of services that implement IDisposable
    - CRITICAL: Must maintain thread safety for singleton instances
    - CRITICAL: Must ensure deterministic service resolution order

Dependency Injection Package

This package provides a simple dependency injection container system for the ClickUp JSON Manager.
It includes components for service registration, resolution, and application-level bootstrapping:

- Container interfaces for service registration and resolution
- Service descriptor with lifetime management (singleton, transient)
- Circular dependency detection
- Higher-level APIs for application bootstrapping with ServiceProvider
- Default service provider with common application services
"""

from .container import (
    ServiceContainer,
    ServiceLifetime,
    ServiceDescriptor,
    ServiceRegistration,
    ServiceResolver
)

from .service_provider import (
    ServiceCollection,
    ServiceProvider,
    create_default_service_provider
)

__all__ = [
    # Container
    'ServiceContainer',
    'ServiceLifetime',
    'ServiceDescriptor',
    'ServiceRegistration',
    'ServiceResolver',
    
    # Service Provider
    'ServiceCollection',
    'ServiceProvider',
    'create_default_service_provider'
]
