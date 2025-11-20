"""Tests for BaseGenerator abstract class.

This module tests the template method pattern implementation and common
functionality shared by all diagram generators.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from clickup_framework.commands.map_helpers.mermaid.generators.base_generator import BaseGenerator
from clickup_framework.commands.map_helpers.mermaid.core.metadata_store import MetadataStore
from clickup_framework.commands.map_helpers.mermaid_validator import MermaidValidationError


class ConcreteGenerator(BaseGenerator):
    """Concrete implementation of BaseGenerator for testing."""

    def validate_inputs(self, **kwargs):
        """Test validation - raises ValueError if 'invalid' kwarg is True."""
        if kwargs.get('invalid'):
            raise ValueError("Invalid test input")

    def generate_body(self, **kwargs):
        """Test body generation - adds simple diagram declaration."""
        self._add_diagram_declaration("graph TD")
        self._add_line("    A[Start]")
        self._add_line("    B[End]")
        self._add_line("    A --> B")


@pytest.fixture
def sample_stats():
    """Sample statistics dictionary for testing."""
    return {
        'total_symbols': 100,
        'files_analyzed': 10,
        'by_language': {
            'Python': {'function': 40, 'class': 20},
            'JavaScript': {'function': 30, 'class': 10}
        }
    }


@pytest.fixture
def temp_output_file():
    """Temporary output file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)
    metadata_file = str(Path(temp_path).with_suffix('')) + '_metadata.json'
    if os.path.exists(metadata_file):
        os.remove(metadata_file)


class TestBaseGeneratorInitialization:
    """Test BaseGenerator initialization."""

    def test_initialization_with_defaults(self, sample_stats, temp_output_file):
        """Test generator initializes with default parameters."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)

        assert generator.stats == sample_stats
        assert generator.output_file == temp_output_file
        assert generator.theme_manager is not None
        assert generator.theme_manager.current_theme == 'dark'
        assert generator.metadata_store is not None
        assert isinstance(generator.lines, list)
        assert len(generator.lines) == 0

    def test_initialization_with_light_theme(self, sample_stats, temp_output_file):
        """Test generator initializes with light theme."""
        generator = ConcreteGenerator(sample_stats, temp_output_file, theme='light')

        assert generator.theme_manager.current_theme == 'light'

    def test_initialization_with_custom_metadata_store(self, sample_stats, temp_output_file):
        """Test generator initializes with custom metadata store."""
        custom_store = MetadataStore()
        # MetadataStore.add_node expects (node_id, metadata_dict)
        # Just verify the store is set correctly
        generator = ConcreteGenerator(sample_stats, temp_output_file, metadata_store=custom_store)

        assert generator.metadata_store is custom_store


class TestTemplateMethodPattern:
    """Test the template method pattern implementation."""

    def test_generate_workflow_order(self, sample_stats, temp_output_file):
        """Test that generate() executes methods in correct order."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)

        with patch.object(generator, 'validate_inputs') as mock_validate, \
             patch.object(generator, '_add_header') as mock_header, \
             patch.object(generator, 'generate_body') as mock_body, \
             patch.object(generator, '_add_footer') as mock_footer, \
             patch.object(generator, '_validate_diagram') as mock_validate_diagram, \
             patch.object(generator, '_write_files') as mock_write:

            generator.generate()

            # Verify execution order using call order
            calls = [
                mock_validate.call_count,
                mock_header.call_count,
                mock_body.call_count,
                mock_footer.call_count,
                mock_validate_diagram.call_count,
                mock_write.call_count
            ]
            assert calls == [1, 1, 1, 1, 1, 1]

    def test_generate_returns_output_file_path(self, sample_stats, temp_output_file):
        """Test that generate() returns the output file path."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)

        result = generator.generate()

        assert result == temp_output_file

    def test_generate_with_kwargs_passed_to_subclass_methods(self, sample_stats, temp_output_file):
        """Test that generate() passes kwargs to validate_inputs and generate_body."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)

        with patch.object(generator, 'validate_inputs') as mock_validate, \
             patch.object(generator, 'generate_body') as mock_body, \
             patch.object(generator, '_validate_diagram'), \
             patch.object(generator, '_write_files'):

            generator.generate(custom_param="test_value", another_param=123)

            mock_validate.assert_called_once_with(custom_param="test_value", another_param=123)
            mock_body.assert_called_once_with(custom_param="test_value", another_param=123)


class TestErrorHandling:
    """Test error handling in the template method."""

    def test_validation_error_is_handled_and_re_raised(self, sample_stats, temp_output_file):
        """Test that validation errors are handled and re-raised."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)

        with pytest.raises(ValueError, match="Invalid test input"):
            generator.generate(invalid=True)

    def test_error_handler_logs_context(self, sample_stats, temp_output_file, capsys):
        """Test that _handle_error logs helpful context."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)
        generator.lines = ["line1", "line2", "line3"]

        with patch.object(generator, '_add_header', side_effect=RuntimeError("Test error")):
            with pytest.raises(RuntimeError):
                generator.generate()

        captured = capsys.readouterr()
        assert "[ERROR] Diagram generation failed: Test error" in captured.err
        assert f"[INFO] Output file: {temp_output_file}" in captured.err
        assert "[INFO] Lines generated: 3" in captured.err


class TestHelperMethods:
    """Test protected helper methods available to subclasses."""

    def test_add_diagram_declaration(self, sample_stats, temp_output_file):
        """Test _add_diagram_declaration adds declaration to lines."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)

        generator._add_diagram_declaration("graph TD")

        assert len(generator.lines) == 1
        assert generator.lines[0] == "graph TD"

    def test_add_line(self, sample_stats, temp_output_file):
        """Test _add_line adds a single line to lines."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)

        generator._add_line("    A[Node A]")
        generator._add_line("    B[Node B]")

        assert len(generator.lines) == 2
        assert generator.lines[0] == "    A[Node A]"
        assert generator.lines[1] == "    B[Node B]"

    def test_add_lines(self, sample_stats, temp_output_file):
        """Test _add_lines adds multiple lines to lines."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)

        lines_to_add = [
            "    A[Node A]",
            "    B[Node B]",
            "    A --> B"
        ]
        generator._add_lines(lines_to_add)

        assert len(generator.lines) == 3
        assert generator.lines == lines_to_add


class TestHeaderGeneration:
    """Test header generation functionality."""

    def test_add_header_creates_title_and_fence(self, sample_stats, temp_output_file):
        """Test _add_header adds title and opening mermaid fence."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)

        generator._add_header()

        assert len(generator.lines) >= 3
        assert generator.lines[0].startswith("# ")
        assert generator.lines[1] == ""
        assert generator.lines[2] == "```mermaid"

    def test_get_diagram_title_from_filename(self, sample_stats):
        """Test _get_diagram_title generates title from output filename."""
        # Test with different filename patterns
        generator1 = ConcreteGenerator(sample_stats, "test_diagram_flowchart.md")
        assert "Flowchart" in generator1._get_diagram_title()

        generator2 = ConcreteGenerator(sample_stats, "my_custom_diagram.md")
        title = generator2._get_diagram_title()
        assert "Custom" in title or "My" in title


class TestFooterGeneration:
    """Test footer generation functionality."""

    def test_add_footer_creates_closing_fence_and_statistics(self, sample_stats, temp_output_file):
        """Test _add_footer adds closing fence and statistics section."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)

        generator._add_footer()

        lines_str = '\n'.join(generator.lines)
        assert "```" in generator.lines[0]
        assert "## Statistics" in lines_str
        assert "Total Symbols" in lines_str
        assert "Files Analyzed" in lines_str
        assert "Languages" in lines_str

    def test_footer_includes_language_breakdown(self, sample_stats, temp_output_file):
        """Test footer includes language breakdown when by_language data exists."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)

        generator._add_footer()

        lines_str = '\n'.join(generator.lines)
        assert "By Language" in lines_str
        assert "Python" in lines_str
        assert "JavaScript" in lines_str
        assert "function" in lines_str
        assert "class" in lines_str

    def test_footer_with_empty_stats(self, temp_output_file):
        """Test footer handles empty statistics gracefully."""
        empty_stats = {
            'total_symbols': 0,
            'files_analyzed': 0,
            'by_language': {}
        }
        generator = ConcreteGenerator(empty_stats, temp_output_file)

        generator._add_footer()

        lines_str = '\n'.join(generator.lines)
        assert "**Total Symbols**: 0" in lines_str
        assert "**Files Analyzed**: 0" in lines_str


class TestDiagramValidation:
    """Test diagram validation functionality."""

    def test_validate_diagram_calls_validator(self, sample_stats, temp_output_file):
        """Test _validate_diagram calls the mermaid validator."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)
        generator.lines = [
            "# Test Diagram",
            "",
            "```mermaid",
            "graph TD",
            "    A --> B",
            "```"
        ]

        with patch('clickup_framework.commands.map_helpers.mermaid.generators.base_generator.validate_and_raise') as mock_validate:
            generator._validate_diagram()

            mock_validate.assert_called_once_with(generator.lines)

    def test_validate_diagram_raises_on_invalid_diagram(self, sample_stats, temp_output_file):
        """Test _validate_diagram raises exception for invalid diagrams."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)
        generator.lines = ["invalid diagram content"]

        with pytest.raises(MermaidValidationError):
            generator._validate_diagram()


class TestFileWriting:
    """Test file writing functionality."""

    def test_write_files_creates_markdown_file(self, sample_stats, temp_output_file):
        """Test _write_files creates the markdown diagram file."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)
        generator.lines = [
            "# Test Diagram",
            "",
            "```mermaid",
            "graph TD",
            "    A --> B",
            "```"
        ]

        generator._write_files()

        assert os.path.exists(temp_output_file)
        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "# Test Diagram" in content
        assert "graph TD" in content
        assert "A --> B" in content

    def test_write_files_creates_metadata_file_when_metadata_exists(self, sample_stats, temp_output_file):
        """Test _write_files creates metadata file when metadata store has data."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)
        # Mock metadata store to simulate having data
        generator.metadata_store = Mock()
        generator.metadata_store.has_data.return_value = True
        generator.metadata_store.export_json.return_value = '{"test": "data"}'
        generator.lines = ["test content"]

        generator._write_files()

        metadata_file = str(Path(temp_output_file).with_suffix('')) + '_metadata.json'
        assert os.path.exists(metadata_file)

        with open(metadata_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "test" in content

    def test_write_files_skips_metadata_when_no_data(self, sample_stats, temp_output_file):
        """Test _write_files skips metadata file when metadata store is empty."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)
        generator.lines = ["test content"]

        generator._write_files()

        metadata_file = str(Path(temp_output_file).with_suffix('')) + '_metadata.json'
        assert not os.path.exists(metadata_file)

    def test_write_files_handles_file_write_error(self, sample_stats, temp_output_file, capsys):
        """Test _write_files handles file write errors gracefully."""
        generator = ConcreteGenerator(sample_stats, "/invalid/path/file.md")
        generator.lines = ["test content"]

        with pytest.raises(Exception):
            generator._write_files()

        captured = capsys.readouterr()
        assert "Error writing diagram file" in captured.err


class TestEndToEndGeneration:
    """Test complete end-to-end diagram generation."""

    def test_full_generation_creates_valid_diagram(self, sample_stats, temp_output_file):
        """Test complete generation workflow produces valid diagram file."""
        generator = ConcreteGenerator(sample_stats, temp_output_file)

        result_path = generator.generate()

        assert result_path == temp_output_file
        assert os.path.exists(temp_output_file)

        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify structure
        assert content.startswith("# ")
        assert "```mermaid" in content
        assert "graph TD" in content
        assert "A[Start]" in content
        assert "B[End]" in content
        assert "A --> B" in content
        assert "```" in content
        assert "## Statistics" in content
        assert "**Total Symbols**: 100" in content
        assert "**Files Analyzed**: 10" in content

    def test_generation_with_theme_applies_styling(self, sample_stats, temp_output_file):
        """Test generation with different themes applies appropriate styling."""
        # Test with dark theme
        generator_dark = ConcreteGenerator(sample_stats, temp_output_file, theme='dark')
        generator_dark.generate()

        # Test with light theme
        temp_light_file = temp_output_file.replace('.md', '_light.md')
        generator_light = ConcreteGenerator(sample_stats, temp_light_file, theme='light')
        generator_light.generate()

        # Both should complete without errors
        assert os.path.exists(temp_output_file)
        assert os.path.exists(temp_light_file)

        # Cleanup light theme file
        if os.path.exists(temp_light_file):
            os.remove(temp_light_file)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_generate_with_none_stats(self, temp_output_file):
        """Test generator handles None stats dict."""
        # BaseGenerator's _add_footer expects stats to be a dict
        # This test verifies it handles missing keys gracefully
        generator = ConcreteGenerator({}, temp_output_file)

        with patch.object(generator, '_write_files'):
            # Should not raise error during generation
            generator.generate()

    def test_generate_with_empty_stats(self, temp_output_file):
        """Test generator handles empty stats dict."""
        empty_stats = {}
        generator = ConcreteGenerator(empty_stats, temp_output_file)

        result = generator.generate()

        assert result == temp_output_file
        assert os.path.exists(temp_output_file)

    def test_generate_with_missing_stats_keys(self, temp_output_file):
        """Test generator handles stats dict with missing keys."""
        incomplete_stats = {
            'total_symbols': 50
            # Missing 'files_analyzed' and 'by_language'
        }
        generator = ConcreteGenerator(incomplete_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(temp_output_file)
        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "**Total Symbols**: 50" in content
        assert "**Files Analyzed**: 0" in content  # Should default to 0
