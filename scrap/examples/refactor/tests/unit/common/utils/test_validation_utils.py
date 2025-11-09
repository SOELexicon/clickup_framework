"""
Unit tests for validation utility functions.

This module tests the functionality of validation utility functions:
- validate_required
- validate_type
- validate_enum
- validate_custom
- validate_min_length
- validate_max_length
- validate_regex
"""
import unittest
from enum import Enum
import re

from refactor.common.utils import (
    validate_required,
    validate_type,
    validate_enum,
    validate_custom,
    validate_min_length,
    validate_max_length,
    validate_regex
)
from refactor.common.exceptions import RequiredFieldError, InvalidValueError


class Status(Enum):
    """Mock enum for testing validate_enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class TestValidateRequired(unittest.TestCase):
    """Tests for the validate_required function."""
    
    def test_field_present_with_value(self):
        """Test validating a field that is present with a value."""
        data = {"name": "Test", "age": 30}
        # Should not raise an exception
        validate_required(data, "name")
    
    def test_field_present_with_empty_string(self):
        """Test validating a field that is present with an empty string."""
        data = {"name": "", "age": 30}
        # Empty string is a valid value, not None
        validate_required(data, "name")
    
    def test_field_present_with_zero(self):
        """Test validating a field that is present with zero."""
        data = {"name": "Test", "age": 0}
        # Zero is a valid value, not None
        validate_required(data, "age")
    
    def test_field_present_with_false(self):
        """Test validating a field that is present with False."""
        data = {"name": "Test", "active": False}
        # False is a valid value, not None
        validate_required(data, "active")
    
    def test_field_missing(self):
        """Test validating a field that is missing."""
        data = {"name": "Test"}
        with self.assertRaises(RequiredFieldError):
            validate_required(data, "age")
    
    def test_field_with_none(self):
        """Test validating a field that has None value."""
        data = {"name": "Test", "age": None}
        with self.assertRaises(RequiredFieldError):
            validate_required(data, "age")
    
    def test_with_context(self):
        """Test validating with context information."""
        data = {"name": "Test"}
        context = {"entity_id": "123", "entity_type": "User"}
        try:
            validate_required(data, "age", context)
            self.fail("Expected RequiredFieldError")
        except RequiredFieldError as e:
            self.assertEqual(e.field_name, "age")
            self.assertEqual(e.context, context)


class TestValidateType(unittest.TestCase):
    """Tests for the validate_type function."""
    
    def test_correct_type_string(self):
        """Test validating a string field with the correct type."""
        data = {"name": "Test"}
        # Should not raise an exception
        validate_type(data, "name", str)
    
    def test_correct_type_int(self):
        """Test validating an integer field with the correct type."""
        data = {"age": 30}
        # Should not raise an exception
        validate_type(data, "age", int)
    
    def test_correct_type_bool(self):
        """Test validating a boolean field with the correct type."""
        data = {"active": True}
        # Should not raise an exception
        validate_type(data, "active", bool)
    
    def test_correct_type_list(self):
        """Test validating a list field with the correct type."""
        data = {"tags": ["tag1", "tag2"]}
        # Should not raise an exception
        validate_type(data, "tags", list)
    
    def test_correct_type_dict(self):
        """Test validating a dictionary field with the correct type."""
        data = {"metadata": {"key": "value"}}
        # Should not raise an exception
        validate_type(data, "metadata", dict)
    
    def test_incorrect_type(self):
        """Test validating a field with an incorrect type."""
        data = {"age": "thirty"}
        with self.assertRaises(InvalidValueError):
            validate_type(data, "age", int)
    
    def test_field_missing(self):
        """Test validating a field that is missing."""
        data = {"name": "Test"}
        # Should not raise an exception for missing fields
        validate_type(data, "age", int)
    
    def test_field_none(self):
        """Test validating a field that is None."""
        data = {"name": "Test", "age": None}
        # Should not raise an exception for None values
        validate_type(data, "age", int)
    
    def test_with_context(self):
        """Test validating with context information."""
        data = {"age": "thirty"}
        context = {"entity_id": "123", "entity_type": "User"}
        try:
            validate_type(data, "age", int, context)
            self.fail("Expected InvalidValueError")
        except InvalidValueError as e:
            self.assertEqual(e.field_name, "age")
            self.assertEqual(e.value, "thirty")
            self.assertIn("Expected type int", e.reason)
            self.assertEqual(e.context, context)


class TestValidateEnum(unittest.TestCase):
    """Tests for the validate_enum function."""
    
    def test_valid_enum_value(self):
        """Test validating a field with a valid enum value."""
        data = {"status": "active"}
        # Should not raise an exception
        validate_enum(data, "status", ["active", "inactive", "pending"])
    
    def test_valid_enum_instance(self):
        """Test validating a field with valid enum instances."""
        data = {"status": Status.ACTIVE}
        # Should not raise an exception
        validate_enum(data, "status", [Status.ACTIVE, Status.INACTIVE, Status.PENDING])
    
    def test_invalid_enum_value(self):
        """Test validating a field with an invalid enum value."""
        data = {"status": "unknown"}
        with self.assertRaises(InvalidValueError):
            validate_enum(data, "status", ["active", "inactive", "pending"])
    
    def test_case_sensitive_match(self):
        """Test validating with case-sensitive matching."""
        data = {"status": "ACTIVE"}
        with self.assertRaises(InvalidValueError):
            validate_enum(data, "status", ["active", "inactive", "pending"], case_sensitive=True)
    
    def test_case_insensitive_match(self):
        """Test validating with case-insensitive matching."""
        data = {"status": "ACTIVE"}
        # Should not raise an exception
        validate_enum(data, "status", ["active", "inactive", "pending"], case_sensitive=False)
    
    def test_field_missing(self):
        """Test validating a field that is missing."""
        data = {"name": "Test"}
        # Should not raise an exception for missing fields
        validate_enum(data, "status", ["active", "inactive", "pending"])
    
    def test_field_none(self):
        """Test validating a field that is None."""
        data = {"name": "Test", "status": None}
        # Should not raise an exception for None values
        validate_enum(data, "status", ["active", "inactive", "pending"])
    
    def test_with_none_in_valid_values(self):
        """Test validating against a list of valid values that includes None."""
        data = {"status": None}
        # Should not raise an exception
        validate_enum(data, "status", ["active", "inactive", "pending", None])
    
    def test_with_context(self):
        """Test validating with context information."""
        data = {"status": "unknown"}
        context = {"entity_id": "123", "entity_type": "User"}
        try:
            validate_enum(data, "status", ["active", "inactive", "pending"], context=context)
            self.fail("Expected InvalidValueError")
        except InvalidValueError as e:
            self.assertEqual(e.field_name, "status")
            self.assertEqual(e.value, "unknown")
            self.assertIn("Value must be one of", e.reason)
            self.assertEqual(e.context, context)


class TestValidateCustom(unittest.TestCase):
    """Tests for the validate_custom function."""
    
    def test_valid_custom_validation(self):
        """Test validating a field with custom validation that passes."""
        data = {"age": 30}
        # Should not raise an exception
        validate_custom(data, "age", lambda x: x > 18, "Age must be greater than 18")
    
    def test_invalid_custom_validation(self):
        """Test validating a field with custom validation that fails."""
        data = {"age": 16}
        with self.assertRaises(InvalidValueError):
            validate_custom(data, "age", lambda x: x > 18, "Age must be greater than 18")
    
    def test_field_missing(self):
        """Test validating a field that is missing."""
        data = {"name": "Test"}
        # Should not raise an exception for missing fields
        validate_custom(data, "age", lambda x: x > 18, "Age must be greater than 18")
    
    def test_field_none(self):
        """Test validating a field that is None."""
        data = {"name": "Test", "age": None}
        # Should not raise an exception for None values
        validate_custom(data, "age", lambda x: x > 18, "Age must be greater than 18")
    
    def test_with_context(self):
        """Test validating with context information."""
        data = {"age": 16}
        context = {"entity_id": "123", "entity_type": "User"}
        try:
            validate_custom(data, "age", lambda x: x > 18, "Age must be greater than 18", context)
            self.fail("Expected InvalidValueError")
        except InvalidValueError as e:
            self.assertEqual(e.field_name, "age")
            self.assertEqual(e.value, 16)
            self.assertEqual(e.reason, "Age must be greater than 18")
            self.assertEqual(e.context, context)


class TestValidateMinLength(unittest.TestCase):
    """Tests for the validate_min_length function."""
    
    def test_string_valid_length(self):
        """Test validating a string with valid length."""
        data = {"name": "John Doe"}
        # Should not raise an exception
        validate_min_length(data, "name", 5)
    
    def test_string_exact_length(self):
        """Test validating a string with exactly the minimum length."""
        data = {"name": "John"}
        # Should not raise an exception
        validate_min_length(data, "name", 4)
    
    def test_string_too_short(self):
        """Test validating a string that is too short."""
        data = {"name": "Joe"}
        with self.assertRaises(InvalidValueError):
            validate_min_length(data, "name", 4)
    
    def test_list_valid_length(self):
        """Test validating a list with valid length."""
        data = {"tags": ["tag1", "tag2", "tag3"]}
        # Should not raise an exception
        validate_min_length(data, "tags", 3)
    
    def test_list_too_short(self):
        """Test validating a list that is too short."""
        data = {"tags": ["tag1"]}
        with self.assertRaises(InvalidValueError):
            validate_min_length(data, "tags", 2)
    
    def test_unsupported_type(self):
        """Test validating a field with a type that doesn't support length."""
        data = {"age": 30}
        with self.assertRaises(InvalidValueError):
            validate_min_length(data, "age", 1)
    
    def test_field_missing(self):
        """Test validating a field that is missing."""
        data = {"name": "Test"}
        # Should not raise an exception for missing fields
        validate_min_length(data, "tags", 1)
    
    def test_field_none(self):
        """Test validating a field that is None."""
        data = {"name": "Test", "tags": None}
        # Should not raise an exception for None values
        validate_min_length(data, "tags", 1)
    
    def test_with_context(self):
        """Test validating with context information."""
        data = {"name": "Joe"}
        context = {"entity_id": "123", "entity_type": "User"}
        try:
            validate_min_length(data, "name", 4, context)
            self.fail("Expected InvalidValueError")
        except InvalidValueError as e:
            self.assertEqual(e.field_name, "name")
            self.assertEqual(e.value, "Joe")
            self.assertIn("must have at least 4", e.reason)
            self.assertEqual(e.context, context)


class TestValidateMaxLength(unittest.TestCase):
    """Tests for the validate_max_length function."""
    
    def test_string_valid_length(self):
        """Test validating a string with valid length."""
        data = {"name": "John"}
        # Should not raise an exception
        validate_max_length(data, "name", 10)
    
    def test_string_exact_length(self):
        """Test validating a string with exactly the maximum length."""
        data = {"name": "John Doe"}
        # Should not raise an exception
        validate_max_length(data, "name", 8)
    
    def test_string_too_long(self):
        """Test validating a string that is too long."""
        data = {"name": "John Doe Smith"}
        with self.assertRaises(InvalidValueError):
            validate_max_length(data, "name", 10)
    
    def test_list_valid_length(self):
        """Test validating a list with valid length."""
        data = {"tags": ["tag1", "tag2"]}
        # Should not raise an exception
        validate_max_length(data, "tags", 2)
    
    def test_list_too_long(self):
        """Test validating a list that is too long."""
        data = {"tags": ["tag1", "tag2", "tag3"]}
        with self.assertRaises(InvalidValueError):
            validate_max_length(data, "tags", 2)
    
    def test_unsupported_type(self):
        """Test validating a field with a type that doesn't support length."""
        data = {"age": 30}
        with self.assertRaises(InvalidValueError):
            validate_max_length(data, "age", 1)
    
    def test_field_missing(self):
        """Test validating a field that is missing."""
        data = {"name": "Test"}
        # Should not raise an exception for missing fields
        validate_max_length(data, "tags", 1)
    
    def test_field_none(self):
        """Test validating a field that is None."""
        data = {"name": "Test", "tags": None}
        # Should not raise an exception for None values
        validate_max_length(data, "tags", 1)
    
    def test_with_context(self):
        """Test validating with context information."""
        data = {"name": "John Doe Smith"}
        context = {"entity_id": "123", "entity_type": "User"}
        try:
            validate_max_length(data, "name", 10, context)
            self.fail("Expected InvalidValueError")
        except InvalidValueError as e:
            self.assertEqual(e.field_name, "name")
            self.assertEqual(e.value, "John Doe Smith")
            self.assertIn("must have at most 10", e.reason)
            self.assertEqual(e.context, context)


class TestValidateRegex(unittest.TestCase):
    """Tests for the validate_regex function."""
    
    def test_valid_pattern(self):
        """Test validating a string that matches the pattern."""
        data = {"email": "user@example.com"}
        # Should not raise an exception
        validate_regex(data, "email", r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$')
    
    def test_invalid_pattern(self):
        """Test validating a string that doesn't match the pattern."""
        data = {"email": "invalid-email"}
        with self.assertRaises(InvalidValueError):
            validate_regex(data, "email", r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$')
    
    def test_non_string_value(self):
        """Test validating a non-string value."""
        data = {"count": 30}
        with self.assertRaises(InvalidValueError):
            validate_regex(data, "count", r'^\d+$')
    
    def test_field_missing(self):
        """Test validating a field that is missing."""
        data = {"name": "Test"}
        # Should not raise an exception for missing fields
        validate_regex(data, "email", r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$')
    
    def test_field_none(self):
        """Test validating a field that is None."""
        data = {"name": "Test", "email": None}
        # Should not raise an exception for None values
        validate_regex(data, "email", r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$')
    
    def test_with_context(self):
        """Test validating with context information."""
        data = {"email": "invalid-email"}
        context = {"entity_id": "123", "entity_type": "User"}
        try:
            validate_regex(data, "email", r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', context)
            self.fail("Expected InvalidValueError")
        except InvalidValueError as e:
            self.assertEqual(e.field_name, "email")
            self.assertEqual(e.value, "invalid-email")
            self.assertIn("must match pattern", e.reason)
            self.assertEqual(e.context, context)


if __name__ == "__main__":
    unittest.main() 