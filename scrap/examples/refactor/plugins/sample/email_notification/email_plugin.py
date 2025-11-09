"""
Task: tsk_3f55d115 - Update Plugins Module Comments
Document: refactor/plugins/sample/email_notification/email_plugin.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)

Used By:
    - NotificationManager: Uses this plugin to send email notifications
    - PluginManager: Loads and manages this plugin
    - PluginRegistry: Registers this plugin's notification channels

Purpose:
    Implements an email notification plugin for the ClickUp JSON Manager.
    Sends notification messages via SMTP with support for HTML formatting
    and customizable email templates.

Requirements:
    - Must properly configure SMTP connection with TLS support
    - Must handle connection errors gracefully
    - Email credentials must be securely stored
    - CRITICAL: Must close SMTP connections after use
    - CRITICAL: Must not expose sensitive information in logs
    - CRITICAL: Must validate email format for recipients

Email Notification Plugin

This plugin sends notifications via email using SMTP.
"""

import logging
import smtplib
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import formataddr
from typing import Any, Dict, List, Optional, Set, Tuple

from ....common.exceptions import PluginError
from ...plugin_interface import NotificationPlugin
from ...plugin_manager import Plugin


logger = logging.getLogger(__name__)


class EmailNotificationPlugin(NotificationPlugin):
    """
    Email notification plugin for ClickUp JSON Manager.
    
    This plugin allows sending notifications via email using SMTP.
    """
    
    def __init__(self, plugin_id: str, manager: 'PluginManager'):
        """Initialize the email notification plugin."""
        super().__init__(plugin_id, manager)
        self.smtp_connection = None
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        config = self.get_config()
        
        # Validate required configuration
        required_fields = ["smtp_server", "smtp_port", "username", "password", "sender_email"]
        for field in required_fields:
            if not config.get(field):
                logger.error(f"Missing required configuration field: {field}")
                return False
        
        logger.info(f"Email notification plugin initialized with SMTP server: {config.get('smtp_server')}")
        return super().initialize()
    
    def cleanup(self) -> bool:
        """
        Clean up resources used by the plugin.
        
        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        # Close SMTP connection if it exists
        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
            except Exception:
                pass
            self.smtp_connection = None
        
        return super().cleanup()
    
    def get_notification_channels(self) -> List[str]:
        """
        Get the notification channels supported by this plugin.
        
        Returns:
            List[str]: Names of supported notification channels
        """
        return ["email"]
    
    def send_notification(self, channel: str, message: str, options: Dict[str, Any]) -> bool:
        """
        Send a notification using the specified channel.
        
        Args:
            channel: Notification channel to use
            message: Notification message
            options: Notification options
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise
        """
        if channel != "email":
            logger.warning(f"Unsupported notification channel: {channel}")
            return False
        
        # Get configuration
        config = self.get_config()
        
        # Get options
        subject = options.get("subject", "Notification from ClickUp JSON Manager")
        recipients = options.get("recipients", [])
        
        # If no recipients specified, use default recipients from config
        if not recipients:
            recipients = config.get("default_recipients", [])
            
        # If still no recipients, can't send
        if not recipients:
            logger.warning("No recipients specified for email notification")
            return False
        
        # Create email message
        email_msg = self._create_email_message(subject, message, recipients, options)
        
        # Send the email
        try:
            self._send_email(email_msg)
            logger.info(f"Email notification sent to {len(recipients)} recipients")
            return True
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            return False
    
    def _create_email_message(
        self, 
        subject: str, 
        content: str, 
        recipients: List[str],
        options: Dict[str, Any]
    ) -> EmailMessage:
        """
        Create an email message.
        
        Args:
            subject: Email subject
            content: Email content
            recipients: List of recipient email addresses
            options: Additional options for the email
            
        Returns:
            EmailMessage: Configured email message
        """
        config = self.get_config()
        
        # Create message
        msg = EmailMessage()
        msg["Subject"] = subject
        
        # Set sender
        sender_name = config.get("sender_name", "ClickUp JSON Manager")
        sender_email = config.get("sender_email")
        msg["From"] = formataddr((sender_name, sender_email))
        
        # Set recipients
        msg["To"] = ", ".join(recipients)
        
        # Set content
        use_html = config.get("html_format", True)
        
        if use_html:
            # Convert plain text to HTML if needed
            if not content.startswith("<html>") and not content.startswith("<!DOCTYPE html>"):
                html_content = f"<html><body><p>{content.replace('\\n', '<br>')}</p>"
                
                # Add task details if included in options and enabled in config
                if config.get("include_task_details", True) and "data" in options and "task" in options["data"]:
                    task = options["data"]["task"]
                    html_content += "<hr><h3>Task Details</h3>"
                    html_content += f"<p><strong>ID:</strong> {task.get('id', 'N/A')}<br>"
                    html_content += f"<strong>Name:</strong> {task.get('name', 'N/A')}<br>"
                    html_content += f"<strong>Status:</strong> {task.get('status', 'N/A')}<br>"
                    html_content += f"<strong>Priority:</strong> {task.get('priority', 'N/A')}</p>"
                
                html_content += "</body></html>"
                content = html_content
                
            msg.set_content(content, subtype="html")
        else:
            msg.set_content(content)
        
        return msg
    
    def _send_email(self, msg: EmailMessage) -> None:
        """
        Send an email message using SMTP.
        
        Args:
            msg: Email message to send
            
        Raises:
            PluginError: If the email could not be sent
        """
        config = self.get_config()
        
        smtp_server = config.get("smtp_server")
        smtp_port = config.get("smtp_port")
        use_tls = config.get("use_tls", True)
        username = config.get("username")
        password = config.get("password")
        
        try:
            # Create a new connection for each send for reliability
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                # Use TLS if enabled
                if use_tls:
                    server.starttls()
                
                # Login if credentials provided
                if username and password:
                    server.login(username, password)
                
                # Send message
                server.send_message(msg)
        except Exception as e:
            raise PluginError(f"Failed to send email: {str(e)}")
    
    def get_config_schema(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the configuration schema for this plugin.
        
        Returns:
            Dict[str, Dict[str, Any]]: Configuration schema
        """
        return {
            "smtp_server": {
                "type": "string",
                "description": "SMTP server hostname",
                "default": "smtp.gmail.com",
                "required": True
            },
            "smtp_port": {
                "type": "integer",
                "description": "SMTP server port",
                "default": 587,
                "required": True
            },
            "use_tls": {
                "type": "boolean",
                "description": "Whether to use TLS for connection",
                "default": True
            },
            "username": {
                "type": "string",
                "description": "SMTP username for authentication",
                "required": True
            },
            "password": {
                "type": "string",
                "description": "SMTP password for authentication",
                "required": True,
                "sensitive": True
            },
            "sender_email": {
                "type": "string",
                "description": "Email address to send notifications from",
                "required": True
            },
            "sender_name": {
                "type": "string",
                "description": "Name to display for the sender",
                "default": "ClickUp JSON Manager"
            },
            "default_recipients": {
                "type": "array",
                "description": "Default recipient email addresses",
                "default": [],
                "items": {
                    "type": "string"
                }
            },
            "include_task_details": {
                "type": "boolean",
                "description": "Include detailed task information in notifications",
                "default": True
            },
            "html_format": {
                "type": "boolean",
                "description": "Send emails in HTML format",
                "default": True
            }
        } 