"""
Notification CLI Commands

This module provides CLI commands for interacting with the notification system.
"""

import argparse
import sys
from typing import Any, Dict, List, Optional

from ..plugin_manager import plugin_manager
from .notification_manager import notification_manager, Notification, NotificationPriority, NotificationType


def setup_notification_commands(subparsers: argparse._SubParsersAction) -> None:
    """
    Set up notification-related CLI commands.
    
    Args:
        subparsers: Subparsers object to add commands to
    """
    # send-notification command
    send_parser = subparsers.add_parser(
        "send-notification",
        help="Send a notification through the notification system"
    )
    send_parser.add_argument(
        "subject",
        help="Subject/title of the notification"
    )
    send_parser.add_argument(
        "message",
        help="Message content of the notification"
    )
    send_parser.add_argument(
        "--type",
        choices=[t.name.lower() for t in NotificationType],
        default="info",
        help="Type of notification"
    )
    send_parser.add_argument(
        "--priority",
        choices=[p.name.lower() for p in NotificationPriority],
        default="medium",
        help="Priority of the notification"
    )
    send_parser.add_argument(
        "--recipients",
        nargs="+",
        help="Recipients of the notification (space-separated list)"
    )
    send_parser.add_argument(
        "--channels",
        nargs="+",
        help="Channels to send through (space-separated list)"
    )
    send_parser.add_argument(
        "--data",
        help="JSON string with additional data for the notification"
    )
    send_parser.set_defaults(func=cmd_send_notification)
    
    # list-channels command
    list_channels_parser = subparsers.add_parser(
        "list-notification-channels",
        help="List available notification channels"
    )
    list_channels_parser.set_defaults(func=cmd_list_notification_channels)
    
    # set-default-channels command
    set_default_parser = subparsers.add_parser(
        "set-default-channels",
        help="Set default notification channels"
    )
    set_default_parser.add_argument(
        "channels",
        nargs="+",
        help="Channels to use by default (space-separated list)"
    )
    set_default_parser.set_defaults(func=cmd_set_default_channels)
    
    # list-notification-plugins command
    list_plugins_parser = subparsers.add_parser(
        "list-notification-plugins",
        help="List installed notification plugins"
    )
    list_plugins_parser.add_argument(
        "--details",
        action="store_true",
        help="Show detailed plugin information"
    )
    list_plugins_parser.set_defaults(func=cmd_list_notification_plugins)


def cmd_send_notification(args: argparse.Namespace) -> int:
    """
    Send a notification.
    
    Args:
        args: Command line arguments
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Initialize notification manager if not already initialized
    if not notification_manager.notification_plugins:
        notification_manager.initialize()
    
    # Parse data if provided
    data = {}
    if args.data:
        try:
            import json
            data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"Error parsing data JSON: {e}")
            return 1
    
    # Create notification
    notification = Notification(
        subject=args.subject,
        message=args.message,
        notification_type=args.type.upper(),
        priority=args.priority.upper(),
        recipients=args.recipients or [],
        data=data,
        channels=args.channels or []
    )
    
    # Send notification
    if notification_manager.send_notification(notification):
        print(f"Notification sent successfully")
        return 0
    else:
        print(f"Failed to send notification")
        return 1


def cmd_list_notification_channels(args: argparse.Namespace) -> int:
    """
    List available notification channels.
    
    Args:
        args: Command line arguments
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Initialize notification manager if not already initialized
    if not notification_manager.notification_plugins:
        notification_manager.initialize()
    
    # Get available channels
    channels = notification_manager.get_available_channels()
    
    if not channels:
        print("No notification channels available")
        print("Try installing notification plugins or check plugin configuration")
        return 0
    
    # Get default channels
    default_channels = notification_manager.default_channels
    
    print(f"Available Notification Channels ({len(channels)}):")
    print("-" * 40)
    
    for channel in sorted(channels):
        is_default = channel in default_channels
        default_marker = " (default)" if is_default else ""
        plugins = notification_manager.channel_mapping.get(channel, [])
        
        print(f"* {channel}{default_marker}")
        print(f"  Provided by: {', '.join(plugins)}")
    
    return 0


def cmd_set_default_channels(args: argparse.Namespace) -> int:
    """
    Set default notification channels.
    
    Args:
        args: Command line arguments
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Initialize notification manager if not already initialized
    if not notification_manager.notification_plugins:
        notification_manager.initialize()
    
    # Get available channels
    available_channels = notification_manager.get_available_channels()
    
    # Validate channels
    invalid_channels = [ch for ch in args.channels if ch not in available_channels]
    if invalid_channels:
        print(f"Error: The following channels are not available: {', '.join(invalid_channels)}")
        print(f"Available channels: {', '.join(available_channels)}")
        return 1
    
    # Set default channels
    notification_manager.set_default_channels(args.channels)
    print(f"Default notification channels set to: {', '.join(args.channels)}")
    
    return 0


def cmd_list_notification_plugins(args: argparse.Namespace) -> int:
    """
    List installed notification plugins.
    
    Args:
        args: Command line arguments
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Initialize plugin manager if needed
    if not plugin_manager.is_initialized:
        plugin_manager.initialize()
    
    # Initialize notification manager if not already initialized
    if not notification_manager.notification_plugins:
        notification_manager.initialize()
    
    # Get notification plugins
    notification_plugins = notification_manager.notification_plugins
    
    if not notification_plugins:
        print("No notification plugins installed")
        return 0
    
    print(f"Installed Notification Plugins ({len(notification_plugins)}):")
    print("-" * 60)
    
    for plugin_id, plugin in notification_plugins.items():
        plugin_info = plugin_manager.get_plugin_info(plugin_id)
        if not plugin_info:
            continue
            
        channels = plugin.get_notification_channels()
        
        print(f"Plugin: {plugin_info.name} ({plugin_id})")
        print(f"Version: {plugin_info.version}")
        print(f"Channels: {', '.join(channels)}")
        
        if args.details:
            print(f"Description: {plugin_info.description}")
            print(f"Author: {plugin_info.author}")
            print(f"Status: {plugin_info.status.name}")
            
            # Show configuration schema if available
            if hasattr(plugin, 'get_config_schema'):
                schema = plugin.get_config_schema()
                if schema:
                    print("Configuration Options:")
                    for key, details in schema.items():
                        required = " (required)" if details.get("required") else ""
                        default = f" (default: {details.get('default')})" if "default" in details else ""
                        print(f"  - {key}{required}{default}: {details.get('description', '')}")
        
        print("-" * 60)
    
    return 0 