"""
Automation module for ClickUp Framework.

This module provides intelligent automation features for task management,
including automatic parent task updates when subtasks transition to active states.
"""

from clickup_framework.automation.config import AutomationConfig, load_automation_config, save_automation_config
from clickup_framework.automation.models import TaskUpdateEvent, ParentUpdateResult
from clickup_framework.automation.parent_updater import ParentTaskAutomationEngine
from clickup_framework.automation.status_matcher import StatusMatcher

__all__ = [
    'AutomationConfig',
    'load_automation_config',
    'save_automation_config',
    'TaskUpdateEvent',
    'ParentUpdateResult',
    'ParentTaskAutomationEngine',
    'StatusMatcher',
]
