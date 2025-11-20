"""Tests for PieChartGenerator.

This module tests the pie chart diagram generator functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from clickup_framework.commands.map_helpers.mermaid.exceptions import DataValidationError, FileOperationError
from clickup_framework.commands.map_helpers.mermaid.generators.pie_chart_generator import PieChartGenerator


@pytest.fixture
def sample_stats():
    """Sample statistics dictionary with language data."""
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


class TestPieChartValidation:
    """Test pie chart diagram validation."""

    def test_validate_inputs_passes_with_valid_data(self, sample_stats, temp_output_file):
        """Test validation passes when by_language data exists."""
        generator = PieChartGenerator(sample_stats, temp_output_file)

        # Should not raise any exceptions
        generator.validate_inputs()

    def test_validate_inputs_fails_without_by_language_data(self, temp_output_file):
        """Test validation fails when by_language data is missing."""
        stats_without_language = {
            'total_symbols': 100,
            'files_analyzed': 10
        }
        generator = PieChartGenerator(stats_without_language, temp_output_file)

        with pytest.raises(DataValidationError, match="Required field \'by_language\' not found in stats data"):
            generator.validate_inputs()

    def test_validate_inputs_fails_with_empty_by_language(self, temp_output_file):
        """Test validation fails when by_language is empty."""
        stats_empty_language = {
            'total_symbols': 100,
            'files_analyzed': 10,
            'by_language': {}
        }
        generator = PieChartGenerator(stats_empty_language, temp_output_file)

        with pytest.raises(DataValidationError, match="Required field \'by_language\' not found in stats data"):
            generator.validate_inputs()


class TestPieChartBodyGeneration:
    """Test pie chart diagram body generation."""

    def test_generate_body_adds_pie_declaration(self, sample_stats, temp_output_file):
        """Test generate_body adds pie chart declaration."""
        generator = PieChartGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        assert len(generator.lines) > 0
        assert generator.lines[0] == "pie title Code Distribution by Language"

    def test_generate_body_adds_language_data(self, sample_stats, temp_output_file):
        """Test generate_body adds language count data."""
        generator = PieChartGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Python: 40 functions + 20 classes = 60
        assert '"Python" : 60' in lines_str
        # JavaScript: 30 functions + 10 classes = 40
        assert '"JavaScript" : 40' in lines_str

    def test_generate_body_sorts_languages_alphabetically(self, temp_output_file):
        """Test generate_body sorts languages in alphabetical order."""
        stats_multiple_langs = {
            'total_symbols': 100,
            'files_analyzed': 10,
            'by_language': {
                'Zebra': {'function': 10},
                'Apple': {'function': 20},
                'Mango': {'function': 15}
            }
        }
        generator = PieChartGenerator(stats_multiple_langs, temp_output_file)

        generator.generate_body()

        # Find the index of each language in the lines
        apple_idx = None
        mango_idx = None
        zebra_idx = None
        for i, line in enumerate(generator.lines):
            if '"Apple"' in line:
                apple_idx = i
            elif '"Mango"' in line:
                mango_idx = i
            elif '"Zebra"' in line:
                zebra_idx = i

        assert apple_idx < mango_idx < zebra_idx

    def test_generate_body_calculates_total_count_per_language(self, temp_output_file):
        """Test generate_body correctly sums symbol counts per language."""
        stats_complex = {
            'total_symbols': 200,
            'files_analyzed': 20,
            'by_language': {
                'Python': {
                    'function': 50,
                    'class': 20,
                    'variable': 10,
                    'method': 30
                }
            }
        }
        generator = PieChartGenerator(stats_complex, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Python total: 50 + 20 + 10 + 30 = 110
        assert '"Python" : 110' in lines_str


class TestPieChartEndToEnd:
    """Test complete end-to-end pie chart generation."""

    def test_full_generation_creates_valid_diagram(self, sample_stats, temp_output_file):
        """Test complete generation workflow produces valid pie chart."""
        generator = PieChartGenerator(sample_stats, temp_output_file)

        result_path = generator.generate()

        assert result_path == temp_output_file
        assert os.path.exists(temp_output_file)

        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify structure
        assert "```mermaid" in content
        assert "pie title Code Distribution by Language" in content
        assert '"Python" : 60' in content
        assert '"JavaScript" : 40' in content
        assert "```" in content
        assert "## Statistics" in content


class TestPieChartEdgeCases:
    """Test edge cases specific to pie chart generation."""

    def test_generate_with_single_language(self, temp_output_file):
        """Test generation with only one language."""
        single_lang_stats = {
            'total_symbols': 50,
            'files_analyzed': 5,
            'by_language': {
                'Python': {'function': 30, 'class': 20}
            }
        }
        generator = PieChartGenerator(single_lang_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert '"Python" : 50' in content

    def test_generate_with_many_languages(self, temp_output_file):
        """Test generation with many languages."""
        many_langs = {f'Lang{i}': {'function': i * 10} for i in range(1, 11)}
        many_lang_stats = {
            'total_symbols': 550,
            'files_analyzed': 50,
            'by_language': many_langs
        }
        generator = PieChartGenerator(many_lang_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify all languages are present
        for i in range(1, 11):
            expected_count = i * 10
            assert f'"Lang{i}" : {expected_count}' in content

    def test_generate_with_zero_count_language(self, temp_output_file):
        """Test generation handles languages with zero symbol count."""
        zero_count_stats = {
            'total_symbols': 50,
            'files_analyzed': 5,
            'by_language': {
                'Python': {'function': 50},
                'EmptyLang': {}  # No symbols
            }
        }
        generator = PieChartGenerator(zero_count_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert '"Python" : 50' in content
        assert '"EmptyLang" : 0' in content

    def test_generate_with_special_characters_in_language_name(self, temp_output_file):
        """Test generation handles language names with special characters."""
        special_char_stats = {
            'total_symbols': 50,
            'files_analyzed': 5,
            'by_language': {
                'C++': {'function': 30},
                'C#': {'function': 20}
            }
        }
        generator = PieChartGenerator(special_char_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert '"C++" : 30' in content
        assert '"C#" : 20' in content
