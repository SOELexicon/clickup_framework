"""
Unit tests for string utility functions.

This module tests the functionality of string utility functions:
- slugify
- normalize_newlines
- truncate
- platform detection helpers
"""
import unittest
import os
import sys
from unittest.mock import patch

from refactor.common.utils import (
    slugify,
    normalize_newlines,
    truncate
)
from refactor.common.utils.string_utils import (
    get_platform_newline,
    is_windows
)


class TestSlugify(unittest.TestCase):
    """Tests for the slugify function."""
    
    def test_basic_slugify(self):
        """Test basic slugification of a string."""
        self.assertEqual(slugify("Hello World"), "hello-world")
    
    def test_special_characters(self):
        """Test slugification with special characters."""
        self.assertEqual(slugify("Hello, World! How are you?"), "hello-world-how-are-you")
    
    def test_multiple_spaces(self):
        """Test slugification with multiple spaces."""
        self.assertEqual(slugify("Hello   World"), "hello-world")
    
    def test_leading_trailing_spaces(self):
        """Test slugification with leading/trailing spaces."""
        self.assertEqual(slugify("  Hello World  "), "hello-world")
    
    def test_uppercase(self):
        """Test slugification with uppercase letters."""
        self.assertEqual(slugify("HELLO WORLD"), "hello-world")
    
    def test_numbers(self):
        """Test slugification with numbers."""
        self.assertEqual(slugify("Hello 123"), "hello-123")
    
    def test_special_characters_only(self):
        """Test slugification with only special characters."""
        self.assertEqual(slugify("!@#$%^&*()"), "")
    
    def test_empty_string(self):
        """Test slugification with an empty string."""
        self.assertEqual(slugify(""), "")
    
    def test_multiple_hyphens(self):
        """Test that multiple hyphens are compressed."""
        self.assertEqual(slugify("Hello---World"), "hello-world")
    
    def test_leading_trailing_hyphens(self):
        """Test that leading/trailing hyphens are removed."""
        self.assertEqual(slugify("-Hello World-"), "hello-world")


class TestNormalizeNewlines(unittest.TestCase):
    """Tests for the normalize_newlines function."""
    
    def test_normalize_crlf_to_lf(self):
        """Test normalizing CRLF to LF."""
        self.assertEqual(normalize_newlines("Hello\r\nWorld", "\n"), "Hello\nWorld")
    
    def test_normalize_cr_to_lf(self):
        """Test normalizing CR to LF."""
        self.assertEqual(normalize_newlines("Hello\rWorld", "\n"), "Hello\nWorld")
    
    def test_normalize_mixed_to_lf(self):
        """Test normalizing mixed newlines to LF."""
        self.assertEqual(normalize_newlines("Hello\r\nWorld\rAnd\nEveryone", "\n"), 
                       "Hello\nWorld\nAnd\nEveryone")
    
    def test_normalize_to_crlf(self):
        """Test normalizing to CRLF."""
        self.assertEqual(normalize_newlines("Hello\nWorld", "\r\n"), "Hello\r\nWorld")
    
    def test_normalize_to_cr(self):
        """Test normalizing to CR."""
        self.assertEqual(normalize_newlines("Hello\nWorld", "\r"), "Hello\rWorld")
    
    def test_no_newlines(self):
        """Test normalizing a string with no newlines."""
        self.assertEqual(normalize_newlines("Hello World", "\n"), "Hello World")
    
    def test_default_target(self):
        """Test normalizing with default target (platform-specific)."""
        with patch('os.linesep', '\n'):
            self.assertEqual(normalize_newlines("Hello\r\nWorld"), "Hello\nWorld")
    
    def test_empty_string(self):
        """Test normalizing an empty string."""
        self.assertEqual(normalize_newlines("", "\n"), "")
    
    def test_multiple_consecutive_newlines(self):
        """Test normalizing multiple consecutive newlines."""
        self.assertEqual(normalize_newlines("Hello\r\n\r\n\r\nWorld", "\n"), "Hello\n\n\nWorld")


class TestTruncate(unittest.TestCase):
    """Tests for the truncate function."""
    
    def test_no_truncation_needed(self):
        """Test when no truncation is needed."""
        self.assertEqual(truncate("Hello", 10), "Hello")
    
    def test_exact_length(self):
        """Test when the string is exactly the maximum length."""
        self.assertEqual(truncate("Hello", 5), "Hello")
    
    def test_truncation_with_default_suffix(self):
        """Test truncation with the default suffix."""
        self.assertEqual(truncate("Hello, World!", 8), "Hello...")
    
    def test_truncation_with_custom_suffix(self):
        """Test truncation with a custom suffix."""
        self.assertEqual(truncate("Hello, World!", 8, ".."), "Hello,..")
    
    def test_empty_suffix(self):
        """Test truncation with an empty suffix."""
        self.assertEqual(truncate("Hello, World!", 5, ""), "Hello")
    
    def test_max_length_less_than_suffix(self):
        """Test when max_length is less than the suffix length."""
        self.assertEqual(truncate("Hello", 2, "..."), "..")
    
    def test_max_length_zero(self):
        """Test when max_length is zero."""
        self.assertEqual(truncate("Hello", 0, "..."), "")
    
    def test_empty_string(self):
        """Test truncating an empty string."""
        self.assertEqual(truncate("", 5), "")


class TestPlatformHelpers(unittest.TestCase):
    """Tests for platform detection helper functions."""
    
    def test_get_platform_newline(self):
        """Test getting the platform-specific newline character."""
        # This should return os.linesep
        self.assertEqual(get_platform_newline(), os.linesep)
    
    def test_is_windows_on_windows(self):
        """Test is_windows detection on Windows."""
        with patch('sys.platform', 'win32'):
            self.assertTrue(is_windows())
    
    def test_is_windows_on_linux(self):
        """Test is_windows detection on Linux."""
        with patch('sys.platform', 'linux'):
            self.assertFalse(is_windows())
    
    def test_is_windows_on_mac(self):
        """Test is_windows detection on macOS."""
        with patch('sys.platform', 'darwin'):
            self.assertFalse(is_windows())


if __name__ == "__main__":
    unittest.main() 