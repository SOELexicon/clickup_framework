"""
Custom Field Validation plugin for ClickUp JSON Manager.

This plugin provides validation for custom fields in tasks, including
due dates, story points, and fields that can be validated with regex patterns.
"""

from . import validation_plugin

__all__ = ["validation_plugin"] 