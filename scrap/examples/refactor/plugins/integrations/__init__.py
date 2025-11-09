"""
ClickUp JSON Manager Integrations

This package contains integrations between different modules and components.
"""

from . import task_notification_integration


def initialize() -> bool:
    """Initialize all integrations."""
    # Initialize task notification integration
    task_notification_integration.initialize()
    
    return True


__all__ = [
    "initialize",
    "task_notification_integration",
] 