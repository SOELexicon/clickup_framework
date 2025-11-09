"""
Unit tests for the Translator class.

This module tests the functionality of the Translator class and related functions.
"""

import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from refactor.common.i18n.translator import Translator, get_translator
from refactor.common.exceptions import ConfigurationError


class TestTranslator(unittest.TestCase):
    """Tests for the Translator class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test translations
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample translation files
        self.en_translations = {
            "greeting": "Hello",
            "farewell": "Goodbye",
            "welcome": "Welcome, {name}!",
            "nested": {
                "key": "Nested value",
                "params": "Nested with {param}"
            }
        }
        
        self.es_translations = {
            "greeting": "Hola",
            "farewell": "Adiós",
            "welcome": "¡Bienvenido, {name}!",
            "nested": {
                "key": "Valor anidado",
                "params": "Anidado con {param}"
            }
        }
        
        # Write test translation files
        with open(os.path.join(self.temp_dir, "en.json"), "w", encoding="utf-8") as f:
            json.dump(self.en_translations, f)
        
        with open(os.path.join(self.temp_dir, "es.json"), "w", encoding="utf-8") as f:
            json.dump(self.es_translations, f)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
        
        # Reset the singleton instance
        from refactor.common.i18n.translator import _translator_instance
        globals()["_translator_instance"] = None
    
    def test_init_with_locale(self):
        """Test initializing translator with a specific locale."""
        translator = Translator("en", self.temp_dir)
        
        self.assertEqual(translator.locale, "en")
        self.assertEqual(translator.locales_dir, self.temp_dir)
        self.assertEqual(translator.translations, self.en_translations)
    
    def test_translate_basic(self):
        """Test basic translation lookup."""
        translator = Translator("en", self.temp_dir)
        
        self.assertEqual(translator.translate("greeting"), "Hello")
        self.assertEqual(translator.translate("farewell"), "Goodbye")
    
    def test_translate_with_parameters(self):
        """Test translation with parameter substitution."""
        translator = Translator("en", self.temp_dir)
        
        self.assertEqual(
            translator.translate("welcome", name="John"),
            "Welcome, John!"
        )
    
    def test_translate_nested_key(self):
        """Test translation with nested keys."""
        translator = Translator("en", self.temp_dir)
        
        self.assertEqual(translator.translate("nested.key"), "Nested value")
        self.assertEqual(
            translator.translate("nested.params", param="test"),
            "Nested with test"
        )
    
    def test_translate_missing_key(self):
        """Test translation with a missing key."""
        translator = Translator("en", self.temp_dir)
        
        # Without default, should return the key
        self.assertEqual(translator.translate("missing_key"), "missing_key")
        
        # With default, should return the default
        self.assertEqual(
            translator.translate("missing_key", default="Default"),
            "Default"
        )
    
    def test_translate_missing_nested_key(self):
        """Test translation with a missing nested key."""
        translator = Translator("en", self.temp_dir)
        
        # Without default, should return the key
        self.assertEqual(translator.translate("nested.missing"), "nested.missing")
        
        # With default, should return the default
        self.assertEqual(
            translator.translate("nested.missing", default="Default"),
            "Default"
        )
    
    def test_translate_with_missing_param(self):
        """Test translation with missing parameter."""
        # Mock the logger to avoid actual logging
        translator = Translator("en", self.temp_dir)
        translator.logger = MagicMock()
        
        # Should return the raw string with unfilled placeholder
        result = translator.translate("welcome")
        self.assertEqual(result, "Welcome, {name}!")
        
        # No need to assert the logging here as it's implementation-specific
    
    def test_set_locale(self):
        """Test changing locale."""
        translator = Translator("en", self.temp_dir)
        
        # Initial locale is English
        self.assertEqual(translator.translate("greeting"), "Hello")
        
        # Change to Spanish
        translator.set_locale("es")
        
        # Should now get Spanish translations
        self.assertEqual(translator.translate("greeting"), "Hola")
        self.assertEqual(translator.translate("farewell"), "Adiós")
        self.assertEqual(
            translator.translate("welcome", name="Juan"),
            "¡Bienvenido, Juan!"
        )
    
    def test_set_same_locale(self):
        """Test setting the same locale (should be a no-op)."""
        translator = Translator("en", self.temp_dir)
        
        # Mock _load_translations to check if it's called
        translator._load_translations = MagicMock()
        
        # Set to the same locale
        translator.set_locale("en")
        
        # _load_translations should not be called
        translator._load_translations.assert_not_called()
    
    def test_missing_locale_file(self):
        """Test handling of missing locale file."""
        # Use a non-existent locale
        translator = Translator("fr", self.temp_dir)
        
        # Should have created an empty translation file
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "fr.json")))
        
        # Should return the key for missing translations
        self.assertEqual(translator.translate("greeting"), "greeting")
    
    def test_invalid_locale_file(self):
        """Test handling of invalid locale file."""
        # Create an invalid JSON file
        with open(os.path.join(self.temp_dir, "invalid.json"), "w") as f:
            f.write("invalid json content")
        
        # Should raise ConfigurationError
        with self.assertRaises(ConfigurationError):
            Translator("invalid", self.temp_dir)
    
    def test_add_translation(self):
        """Test adding a new translation."""
        translator = Translator("en", self.temp_dir)
        
        # Add a new translation
        translator.add_translation("new_key", "New Value")
        
        # Should be able to retrieve it
        self.assertEqual(translator.translate("new_key"), "New Value")
        
        # Should have been saved to the file
        with open(os.path.join(self.temp_dir, "en.json"), "r", encoding="utf-8") as f:
            saved_translations = json.load(f)
            self.assertEqual(saved_translations["new_key"], "New Value")
    
    def test_add_nested_translation(self):
        """Test adding a nested translation."""
        translator = Translator("en", self.temp_dir)
        
        # Add a new nested translation
        translator.add_translation("nested.new_key", "New Nested Value")
        
        # Should be able to retrieve it
        self.assertEqual(translator.translate("nested.new_key"), "New Nested Value")
        
        # Original nested values should still be accessible
        self.assertEqual(translator.translate("nested.key"), "Nested value")
        
        # Should have been saved to the file
        with open(os.path.join(self.temp_dir, "en.json"), "r", encoding="utf-8") as f:
            saved_translations = json.load(f)
            self.assertEqual(saved_translations["nested"]["new_key"], "New Nested Value")
    
    def test_add_translation_to_missing_locale(self):
        """Test adding a translation to a missing locale file."""
        # Use a non-existent locale
        translator = Translator("fr", self.temp_dir)
        
        # Add a translation
        translator.add_translation("greeting", "Bonjour")
        
        # Should be able to retrieve it
        self.assertEqual(translator.translate("greeting"), "Bonjour")
        
        # Should have been saved to the file
        with open(os.path.join(self.temp_dir, "fr.json"), "r", encoding="utf-8") as f:
            saved_translations = json.load(f)
            self.assertEqual(saved_translations["greeting"], "Bonjour")
    
    def test_format_error_handling(self):
        """Test error handling in string formatting."""
        translator = Translator("en", self.temp_dir)
        translator.logger = MagicMock()
        
        # Add a translation with an invalid format
        translator.add_translation("invalid_format", "Value: {value:.2f}")
        
        # Format with incompatible type should return the raw string
        result = translator.translate("invalid_format", value="not-a-number")
        self.assertEqual(result, "Value: {value:.2f}")
        
        # Verify that logger.error was called
        translator.logger.error.assert_called_once()


class TestGetTranslator(unittest.TestCase):
    """Tests for the get_translator function."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test translations
        self.temp_dir = tempfile.mkdtemp()
        
        # Reset the singleton instance
        from refactor.common.i18n.translator import _translator_instance
        globals()["_translator_instance"] = None
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
        
        # Reset the singleton instance
        from refactor.common.i18n.translator import _translator_instance
        globals()["_translator_instance"] = None
    
    def test_get_translator_creates_singleton(self):
        """Test that get_translator creates a singleton instance."""
        translator1 = get_translator("en", self.temp_dir)
        translator2 = get_translator("en", self.temp_dir)
        
        # Should be the same instance
        self.assertIs(translator1, translator2)
    
    def test_get_translator_with_different_locale(self):
        """Test get_translator with a different locale."""
        # Get translator with initial locale
        translator1 = get_translator("en", self.temp_dir)
        
        # Get translator with different locale
        translator2 = get_translator("es", self.temp_dir)
        
        # Should be the same instance but with updated locale
        self.assertIs(translator1, translator2)
        self.assertEqual(translator2.locale, "es")
    
    def test_get_translator_with_different_dir(self):
        """Test get_translator with a different directory."""
        # Get translator with initial locale and directory
        translator1 = get_translator("en", self.temp_dir)
        
        # Create another temp dir
        temp_dir2 = tempfile.mkdtemp()
        
        try:
            # Get translator with same locale but different directory
            translator2 = get_translator("en", temp_dir2)
            
            # Should have updated the directory and created a new instance
            self.assertEqual(translator2.locales_dir, temp_dir2)
            
            # Since we create a new instance, it should be different
            # We can't test for identity here, so we verify the directory
            self.assertTrue(os.path.exists(os.path.join(temp_dir2, "en.json")))
        finally:
            # Clean up
            shutil.rmtree(temp_dir2)


if __name__ == "__main__":
    unittest.main() 