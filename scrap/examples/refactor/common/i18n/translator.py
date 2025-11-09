"""
Task: tsk_7e3a4709 - Update Common Module Comments
Document: refactor/common/i18n/translator.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CommandSystem: Translates command outputs and help text
    - ErrorHandler: Provides localized error messages
    - RESTfulAPI: Returns localized API responses
    - UIComponents: Displays text in the user's preferred language
    - PluginSystem: Allows plugins to access translation services

Purpose:
    Implements a translation system that loads language-specific strings
    from JSON files, supporting nested translation keys, parameter substitution,
    and runtime locale switching. Provides both instance-based and singleton
    access patterns.

Requirements:
    - Must support hierarchical translation keys using dot notation
    - Must gracefully handle missing translations with fallbacks
    - Must support parameter substitution in translated strings
    - Must create default translation files if missing
    - CRITICAL: Must handle string encoding correctly (UTF-8)
    - CRITICAL: Must preserve string formatting across translations
    - CRITICAL: Must support dynamic locale switching at runtime

Translator module for handling language translations.

This module provides the Translator class for loading and accessing translations
from language-specific JSON files.
"""

import os
import json
from typing import Dict, Optional, Any
import logging
from pathlib import Path

from refactor.common.exceptions import ConfigurationError

# Singleton instance
_translator_instance = None


class Translator:
    """
    Handles translation lookups based on a specified locale.
    
    Translations are loaded from JSON files in the locales directory.
    """
    
    def __init__(self, locale: str = "en", locales_dir: Optional[str] = None):
        """
        Initialize the translator with a locale and translations directory.
        
        Args:
            locale: The locale code (e.g., 'en', 'fr', 'es')
            locales_dir: Directory containing translation files
        """
        self.logger = logging.getLogger(__name__)
        self.locale = locale
        self.locales_dir = locales_dir or os.path.join(os.path.dirname(__file__), "locales")
        self.translations: Dict[str, Dict[str, str]] = {}
        
        # Ensure the locales directory exists
        if not os.path.exists(self.locales_dir):
            os.makedirs(self.locales_dir, exist_ok=True)
        
        # Load translations for the specified locale
        self._load_translations()
    
    def _load_translations(self) -> None:
        """
        Load translations from JSON files for the current locale.
        
        Translation files are expected to be named {locale}.json
        (e.g., en.json, fr.json).
        """
        locale_file = os.path.join(self.locales_dir, f"{self.locale}.json")
        
        # Check if the translation file exists
        if not os.path.exists(locale_file):
            # Create a default empty translation file
            default_translations = {}
            os.makedirs(os.path.dirname(locale_file), exist_ok=True)
            with open(locale_file, "w", encoding="utf-8") as f:
                json.dump(default_translations, f, indent=4)
            
            self.logger.warning(f"Created empty translation file: {locale_file}")
            self.translations = default_translations
            return
        
        # Load translations from the file
        try:
            with open(locale_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
                self.logger.debug(f"Loaded translations for locale '{self.locale}'")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid translation file format: {locale_file}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load translations: {str(e)}") from e
    
    def translate(self, key: str, default: Optional[str] = None, **params) -> str:
        """
        Get a translated string for the given key.
        
        Args:
            key: Translation key (dot notation supported for nested lookups)
            default: Default text if translation is not found
            **params: Parameters to format the translation string
        
        Returns:
            Translated string or default if not found
        """
        # Split the key for nested lookups (e.g., "errors.not_found")
        keys = key.split('.')
        current = self.translations
        
        # Traverse the nested dictionary
        for part in keys:
            if not isinstance(current, dict) or part not in current:
                if default is not None:
                    return self._format_string(default, **params)
                return key
            current = current[part]
        
        if not isinstance(current, str):
            if default is not None:
                return self._format_string(default, **params)
            return key
        
        return self._format_string(current, **params)
    
    def _format_string(self, text: str, **params) -> str:
        """Format a string with the provided parameters."""
        if not params:
            return text
        
        try:
            return text.format(**params)
        except KeyError as e:
            self.logger.warning(f"Missing parameter in translation: {e}")
            return text
        except Exception as e:
            self.logger.error(f"Error formatting translation: {e}")
            return text
    
    def add_translation(self, key: str, value: str) -> None:
        """
        Add or update a translation for the current locale.
        
        Args:
            key: Translation key (dot notation supported for nested keys)
            value: Translation text
        """
        # Split the key for nested creation
        keys = key.split('.')
        current = self.translations
        
        # Navigate to the correct location in the nested dict
        for i, part in enumerate(keys[:-1]):
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        
        # Set the value
        current[keys[-1]] = value
        
        # Save the updated translations
        locale_file = os.path.join(self.locales_dir, f"{self.locale}.json")
        try:
            with open(locale_file, "w", encoding="utf-8") as f:
                json.dump(self.translations, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save translations: {e}")
    
    def set_locale(self, locale: str) -> None:
        """
        Change the current locale and reload translations.
        
        Args:
            locale: The new locale code
        """
        if self.locale == locale:
            return
        
        self.locale = locale
        self._load_translations()


def get_translator(locale: str = "en", locales_dir: Optional[str] = None) -> Translator:
    """
    Get or create the singleton translator instance.
    
    Args:
        locale: The locale code
        locales_dir: Directory containing translation files
    
    Returns:
        Translator instance
    """
    global _translator_instance
    
    # If directory is specified and different from current, create a new instance
    if _translator_instance is not None and locales_dir is not None:
        if locales_dir != _translator_instance.locales_dir:
            _translator_instance = Translator(locale, locales_dir)
            return _translator_instance
    
    # If no instance exists, create one
    if _translator_instance is None:
        _translator_instance = Translator(locale, locales_dir)
    # If locale is different, update it
    elif locale != _translator_instance.locale:
        _translator_instance.set_locale(locale)
    
    return _translator_instance 