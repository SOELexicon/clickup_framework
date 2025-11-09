"""
Notification System

This package provides notification functionality for the ClickUp JSON Manager.
It includes the notification manager, notification classes, and utilities for
sending and receiving notifications through various channels.
"""

from .notification_manager import NotificationManager, notification_manager

__all__ = [
    "NotificationManager",
    "notification_manager",
] 