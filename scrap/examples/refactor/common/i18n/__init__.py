"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/i18n/__init__.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CommandSystem: Uses for CLI command output localization
    - RESTfulAPI: Provides localized API responses
    - ErrorHandler: Uses for localized error messages
    - UIComponents: Displays localized text in user interfaces
    - NotificationSystem: Sends notifications in the user's preferred language

Purpose:
    Provides internationalization support for the application,
    enabling user interface text, error messages, and notifications
    to be presented in multiple languages based on user preferences.

Requirements:
    - Must support multiple languages through JSON-based translation files
    - Must provide fallback mechanisms for missing translations
    - Must handle parameter substitution in translated strings
    - CRITICAL: Must preserve message formatting across translations
    - CRITICAL: Must properly handle text encoding (UTF-8)

Internationalization (i18n) support module.

This module provides internationalization support for the application,
allowing for localized text and messages based on language preferences.
"""

from .translator import Translator, get_translator

__all__ = [
    'Translator',
    'get_translator',
] 