"""Tests for custom exception classes and error handling."""

import pytest
from clickup_framework.commands.map_helpers.mermaid.exceptions import (
    MermaidGenerationError,
    DataValidationError,
    ConfigurationError,
    FileOperationError,
    DiagramSyntaxError,
    ResourceLimitError
)


class TestMermaidGenerationError:
    """Test base MermaidGenerationError class."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = MermaidGenerationError("Test error message")
        assert str(error) == "Test error message"
        assert error.suggestions == []
        assert error.context == {}

    def test_error_with_suggestions(self):
        """Test error with suggestions."""
        suggestions = ["Try option A", "Try option B"]
        error = MermaidGenerationError("Test error", suggestions=suggestions)
        assert error.suggestions == suggestions

    def test_error_with_context(self):
        """Test error with context."""
        context = {"file": "test.py", "line": 42}
        error = MermaidGenerationError("Test error", context=context)
        assert error.context == context

    def test_format_error(self):
        """Test error formatting."""
        error = MermaidGenerationError(
            "Test error",
            suggestions=["Suggestion 1", "Suggestion 2"],
            context={"key1": "value1", "key2": "value2"}
        )
        formatted = error.format_error()

        assert "ERROR: Test error" in formatted
        assert "Context:" in formatted
        assert "key1: value1" in formatted
        assert "key2: value2" in formatted
        assert "Suggestions:" in formatted
        assert "\u2022 Suggestion 1" in formatted
        assert "\u2022 Suggestion 2" in formatted


class TestDataValidationError:
    """Test DataValidationError class."""

    def test_missing_required_field(self):
        """Test missing required field error."""
        error = DataValidationError.missing_required_field(
            field_name="symbols_by_file",
            generator_type="flowchart",
            stats_keys=["total_symbols", "by_language"]
        )

        assert "symbols_by_file" in str(error)
        assert "flowchart" in str(error)
        assert "total_symbols" in error.context["available_fields"]
        assert "by_language" in error.context["available_fields"]
        assert len(error.suggestions) > 0

    def test_empty_data_structure(self):
        """Test empty data structure error."""
        error = DataValidationError.empty_data_structure(
            field_name="function_calls",
            generator_type="sequence",
            data_size=0
        )

        assert "function_calls" in str(error)
        assert "empty" in str(error)
        assert error.context["data_size"] == 0
        assert len(error.suggestions) > 0


class TestConfigurationError:
    """Test ConfigurationError class."""

    def test_invalid_value(self):
        """Test invalid configuration value."""
        error = ConfigurationError.invalid_value(
            config_name="theme",
            value="invalid_theme",
            valid_values=["dark", "light", "neutral"]
        )

        assert "theme" in str(error)
        assert "invalid_theme" in str(error)
        assert error.context["valid_values"] == ["dark", "light", "neutral"]
        assert any("dark" in s for s in error.suggestions)

    def test_out_of_range(self):
        """Test out of range configuration value."""
        error = ConfigurationError.out_of_range(
            config_name="max_nodes",
            value=10000,
            min_value=1,
            max_value=1000
        )

        assert "max_nodes" in str(error)
        assert "10000" in str(error)
        assert error.context["min_value"] == 1
        assert error.context["max_value"] == 1000
        assert len(error.suggestions) > 0


class TestFileOperationError:
    """Test FileOperationError class."""

    def test_cannot_write(self):
        """Test cannot write file error."""
        error = FileOperationError.cannot_write(
            file_path="/path/to/output.md",
            reason="Permission denied"
        )

        assert "/path/to/output.md" in str(error)
        assert "Permission denied" in str(error)
        assert error.context["file_path"] == "/path/to/output.md"
        assert error.context["reason"] == "Permission denied"
        assert any("permission" in s.lower() for s in error.suggestions)

    def test_cannot_read(self):
        """Test cannot read file error."""
        error = FileOperationError.cannot_read(
            file_path="/path/to/input.json",
            reason="File not found"
        )

        assert "/path/to/input.json" in str(error)
        assert "File not found" in str(error)
        assert error.context["file_path"] == "/path/to/input.json"
        assert len(error.suggestions) > 0


class TestDiagramSyntaxError:
    """Test DiagramSyntaxError class."""

    def test_validation_failed(self):
        """Test validation failed error."""
        validation_errors = [
            "Invalid node ID: node-1",
            "Malformed edge syntax: A --> B C",
            "Unescaped special character: node[test{value}]"
        ]

        error = DiagramSyntaxError.validation_failed(
            errors=validation_errors,
            diagram_type="flowchart",
            line_count=150
        )

        assert "flowchart" in str(error)
        assert "3 validation error" in str(error)
        assert error.context["error_count"] == 3
        assert error.context["line_count"] == 150
        assert len(error.context["errors"]) == 3


class TestResourceLimitError:
    """Test ResourceLimitError class."""

    def test_diagram_too_large(self):
        """Test diagram too large error."""
        error = ResourceLimitError.diagram_too_large(
            node_count=1500,
            max_nodes=1000,
            diagram_type="code_flow"
        )

        assert "1500" in str(error)
        assert "1000" in str(error)
        assert error.context["node_count"] == 1500
        assert error.context["max_nodes"] == 1000
        assert error.context["overflow"] == 500
        assert any("max_nodes" in s for s in error.suggestions)

    def test_memory_exceeded(self):
        """Test memory exceeded error."""
        error = ResourceLimitError.memory_exceeded(
            current_mb=512.5,
            peak_mb=550.0,
            threshold_mb=500.0
        )

        assert "512.5" in str(error)
        assert "500.0" in str(error)
        assert error.context["current_memory_mb"] == 512.5
        assert error.context["threshold_mb"] == 500.0
        assert error.context["overflow_mb"] == pytest.approx(12.5)


class TestErrorIntegration:
    """Integration tests for error handling."""

    def test_all_errors_inherit_from_base(self):
        """Test all custom errors inherit from base class."""
        error_classes = [
            DataValidationError,
            ConfigurationError,
            FileOperationError,
            DiagramSyntaxError,
            ResourceLimitError
        ]

        for error_cls in error_classes:
            error = error_cls("Test message")
            assert isinstance(error, MermaidGenerationError)
            assert isinstance(error, Exception)

    def test_formatted_errors_are_readable(self):
        """Test formatted errors are human-readable."""
        error = DataValidationError.missing_required_field(
            field_name="test_field",
            generator_type="test_generator",
            stats_keys=["key1", "key2"]
        )

        formatted = error.format_error()
        lines = formatted.split('\n')

        # Should have at least error message, context section, and suggestions section
        assert len(lines) >= 5
        assert lines[0].startswith("ERROR:")
        assert any("Context:" in line for line in lines)
        assert any("Suggestions:" in line for line in lines)
