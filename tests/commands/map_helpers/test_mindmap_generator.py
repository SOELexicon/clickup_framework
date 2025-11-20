"""Tests for MindmapGenerator.

This module tests the mindmap diagram generator functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from clickup_framework.commands.map_helpers.mermaid.generators.mindmap_generator import MindmapGenerator


@pytest.fixture
def sample_stats():
    """Sample statistics dictionary with symbols_by_file and by_language data."""
    return {
        'total_symbols': 150,
        'files_analyzed': 5,
        'by_language': {
            'Python': {'function': 50, 'class': 20},
            'JavaScript': {'function': 40, 'class': 15},
            'TypeScript': {'function': 20, 'class': 5}
        },
        'symbols_by_file': {
            '/project/main.py': [
                {'name': 'func1', 'language': 'Python', 'kind': 'function'},
                {'name': 'func2', 'language': 'Python', 'kind': 'function'},
                {'name': 'MyClass', 'language': 'Python', 'kind': 'class'}
            ],
            '/project/utils.py': [
                {'name': 'helper1', 'language': 'Python', 'kind': 'function'},
                {'name': 'helper2', 'language': 'Python', 'kind': 'function'}
            ],
            '/project/app.js': [
                {'name': 'init', 'language': 'JavaScript', 'kind': 'function'},
                {'name': 'run', 'language': 'JavaScript', 'kind': 'function'},
                {'name': 'App', 'language': 'JavaScript', 'kind': 'class'}
            ],
            '/project/types.ts': [
                {'name': 'UserType', 'language': 'TypeScript', 'kind': 'class'}
            ]
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


class TestMindmapValidation:
    """Test mindmap diagram validation."""

    def test_validate_inputs_passes_with_valid_data(self, sample_stats, temp_output_file):
        """Test validation passes when both symbols_by_file and by_language exist."""
        generator = MindmapGenerator(sample_stats, temp_output_file)

        # Should not raise any exceptions
        generator.validate_inputs()

    def test_validate_inputs_fails_without_symbols_by_file(self, temp_output_file):
        """Test validation fails when symbols_by_file is missing."""
        stats_without_symbols = {
            'total_symbols': 100,
            'by_language': {'Python': {'function': 50}}
        }
        generator = MindmapGenerator(stats_without_symbols, temp_output_file)

        with pytest.raises(ValueError, match="No symbols_by_file or by_language data found in stats"):
            generator.validate_inputs()

    def test_validate_inputs_fails_without_by_language(self, temp_output_file):
        """Test validation fails when by_language is missing."""
        stats_without_language = {
            'total_symbols': 100,
            'symbols_by_file': {'/file.py': [{'name': 'func'}]}
        }
        generator = MindmapGenerator(stats_without_language, temp_output_file)

        with pytest.raises(ValueError, match="No symbols_by_file or by_language data found in stats"):
            generator.validate_inputs()

    def test_validate_inputs_fails_with_empty_data(self, temp_output_file):
        """Test validation fails when data structures are empty."""
        stats_empty = {
            'total_symbols': 0,
            'by_language': {},
            'symbols_by_file': {}
        }
        generator = MindmapGenerator(stats_empty, temp_output_file)

        with pytest.raises(ValueError, match="No symbols_by_file or by_language data found in stats"):
            generator.validate_inputs()


class TestMindmapBodyGeneration:
    """Test mindmap diagram body generation."""

    def test_generate_body_adds_mindmap_declaration(self, sample_stats, temp_output_file):
        """Test generate_body adds mindmap declaration."""
        generator = MindmapGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        assert len(generator.lines) > 0
        assert generator.lines[0] == "mindmap"

    def test_generate_body_adds_root_node(self, sample_stats, temp_output_file):
        """Test generate_body adds root Codebase node."""
        generator = MindmapGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        assert "root((Codebase))" in generator.lines[1]

    def test_generate_body_adds_language_nodes(self, sample_stats, temp_output_file):
        """Test generate_body adds language nodes."""
        generator = MindmapGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        assert "Python" in lines_str
        assert "JavaScript" in lines_str
        assert "TypeScript" in lines_str

    def test_generate_body_limits_languages_to_five(self, temp_output_file):
        """Test generate_body limits to top 5 languages."""
        stats_many_langs = {
            'total_symbols': 200,
            'by_language': {f'Lang{i}': {'function': i * 10} for i in range(1, 11)},
            'symbols_by_file': {
                f'/file{i}.ext': [{'name': f'func{i}', 'language': f'Lang{i}', 'kind': 'function'}]
                for i in range(1, 11)
            }
        }
        generator = MindmapGenerator(stats_many_langs, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Count language nodes (lines with just language name, indented 4 spaces)
        lang_nodes = [line for line in generator.lines if line.startswith('    ') and not '(' in line and 'Lang' in line]
        # Should have exactly 5 languages (alphabetically sorted)
        assert len(lang_nodes) == 5
        # Verify it's alphabetically sorted - first 5 should be Lang1, Lang10, Lang2, Lang3, Lang4
        expected_langs = ['Lang1', 'Lang10', 'Lang2', 'Lang3', 'Lang4']
        for expected_lang in expected_langs:
            assert expected_lang in lines_str

    def test_generate_body_adds_file_nodes_with_symbol_counts(self, sample_stats, temp_output_file):
        """Test generate_body adds file nodes with symbol counts."""
        generator = MindmapGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # main.py has 3 symbols
        assert "main.py (3)" in lines_str
        # utils.py has 2 symbols
        assert "utils.py (2)" in lines_str
        # app.js has 3 symbols
        assert "app.js (3)" in lines_str

    def test_generate_body_sorts_files_by_symbol_count(self, temp_output_file):
        """Test generate_body sorts files by symbol count (descending)."""
        stats_sorted = {
            'total_symbols': 50,
            'by_language': {'Python': {'function': 50}},
            'symbols_by_file': {
                '/file1.py': [{'language': 'Python', 'kind': 'function'}] * 1,
                '/file2.py': [{'language': 'Python', 'kind': 'function'}] * 5,
                '/file3.py': [{'language': 'Python', 'kind': 'function'}] * 3,
            }
        }
        generator = MindmapGenerator(stats_sorted, temp_output_file)

        generator.generate_body()

        # Find the indices of each file in the output
        file1_idx = None
        file2_idx = None
        file3_idx = None
        for i, line in enumerate(generator.lines):
            if 'file1.py' in line:
                file1_idx = i
            elif 'file2.py' in line:
                file2_idx = i
            elif 'file3.py' in line:
                file3_idx = i

        # file2 (5 symbols) should come before file3 (3 symbols) before file1 (1 symbol)
        assert file2_idx < file3_idx < file1_idx

    def test_generate_body_limits_files_to_five_per_language(self, temp_output_file):
        """Test generate_body limits to top 5 files per language."""
        stats_many_files = {
            'total_symbols': 100,
            'by_language': {'Python': {'function': 100}},
            'symbols_by_file': {
                f'/file{i}.py': [{'language': 'Python', 'kind': 'function'}] * (10 - i)
                for i in range(10)
            }
        }
        generator = MindmapGenerator(stats_many_files, temp_output_file)

        generator.generate_body()

        # Count Python file nodes
        python_file_count = sum(1 for line in generator.lines if '.py' in line and '(' in line)
        assert python_file_count <= 5


class TestMindmapEndToEnd:
    """Test complete end-to-end mindmap generation."""

    def test_full_generation_creates_valid_diagram(self, sample_stats, temp_output_file):
        """Test complete generation workflow produces valid mindmap."""
        generator = MindmapGenerator(sample_stats, temp_output_file)

        result_path = generator.generate()

        assert result_path == temp_output_file
        assert os.path.exists(temp_output_file)

        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify structure
        assert "```mermaid" in content
        assert "mindmap" in content
        assert "root((Codebase))" in content
        assert "Python" in content
        assert "JavaScript" in content
        assert "```" in content
        assert "## Statistics" in content


class TestMindmapEdgeCases:
    """Test edge cases specific to mindmap generation."""

    def test_generate_with_single_language_single_file(self, temp_output_file):
        """Test generation with only one language and one file."""
        minimal_stats = {
            'total_symbols': 5,
            'by_language': {'Python': {'function': 5}},
            'symbols_by_file': {
                '/single.py': [
                    {'name': 'func1', 'language': 'Python', 'kind': 'function'},
                    {'name': 'func2', 'language': 'Python', 'kind': 'function'},
                    {'name': 'func3', 'language': 'Python', 'kind': 'function'}
                ]
            }
        }
        generator = MindmapGenerator(minimal_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "Python" in content
        assert "single.py (3)" in content

    def test_generate_with_files_without_matching_language(self, temp_output_file):
        """Test generation handles files where language doesn't match by_language."""
        mismatched_stats = {
            'total_symbols': 10,
            'by_language': {'Python': {'function': 10}},
            'symbols_by_file': {
                '/python_file.py': [{'language': 'Python', 'kind': 'function'}] * 5,
                '/mystery_file.xyz': [{'language': 'Mystery', 'kind': 'function'}] * 5  # Not in by_language
            }
        }
        generator = MindmapGenerator(mismatched_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        # Should not crash, only Python files should appear
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "python_file.py" in content
        # mystery_file might not appear since its language isn't in by_language top 5

    def test_generate_with_empty_symbol_list(self, temp_output_file):
        """Test generation handles files with empty symbol lists."""
        empty_symbols_stats = {
            'total_symbols': 5,
            'by_language': {'Python': {'function': 5}},
            'symbols_by_file': {
                '/has_symbols.py': [{'language': 'Python', 'kind': 'function'}] * 5,
                '/no_symbols.py': []  # Empty list
            }
        }
        generator = MindmapGenerator(empty_symbols_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "has_symbols.py" in content
        # File with no symbols should not appear

    def test_generate_with_complex_file_paths(self, temp_output_file):
        """Test generation handles complex file paths correctly."""
        complex_path_stats = {
            'total_symbols': 10,
            'by_language': {'Python': {'function': 10}},
            'symbols_by_file': {
                '/very/deep/nested/path/to/file.py': [{'language': 'Python', 'kind': 'function'}] * 5,
                'C:\\Windows\\Path\\file.py': [{'language': 'Python', 'kind': 'function'}] * 3,
                'relative/path/file.py': [{'language': 'Python', 'kind': 'function'}] * 2
            }
        }
        generator = MindmapGenerator(complex_path_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should extract just the filename, not the full path
        assert "file.py" in content
        # Should not include full paths
        assert "/very/deep" not in content
        assert "C:\\Windows" not in content
