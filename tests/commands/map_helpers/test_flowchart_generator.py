"""Tests for FlowchartGenerator.

This module tests the flowchart diagram generator functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from clickup_framework.commands.map_helpers.mermaid.generators.flowchart_generator import FlowchartGenerator


@pytest.fixture
def sample_stats():
    """Sample statistics dictionary with symbols_by_file data."""
    return {
        'total_symbols': 50,
        'files_analyzed': 5,
        'symbols_by_file': {
            '/project/src/main.py': [
                {'name': 'func1', 'kind': 'function'},
                {'name': 'func2', 'kind': 'function'},
                {'name': 'MyClass', 'kind': 'class'},
                {'name': 'method1', 'kind': 'method', 'scope': 'MyClass'}
            ],
            '/project/src/utils.py': [
                {'name': 'helper1', 'kind': 'function'},
                {'name': 'helper2', 'kind': 'function'},
                {'name': 'var1', 'kind': 'variable'}
            ],
            '/project/lib/module.py': [
                {'name': 'ClassA', 'kind': 'class'},
                {'name': 'ClassB', 'kind': 'class'}
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


class TestFlowchartValidation:
    """Test flowchart diagram validation."""

    def test_validate_inputs_passes_with_valid_data(self, sample_stats, temp_output_file):
        """Test validation passes when symbols_by_file data exists."""
        generator = FlowchartGenerator(sample_stats, temp_output_file)

        # Should not raise any exceptions
        generator.validate_inputs()

    def test_validate_inputs_fails_without_symbols_by_file(self, temp_output_file):
        """Test validation fails when symbols_by_file is missing."""
        stats_without_symbols = {
            'total_symbols': 100,
            'files_analyzed': 10
        }
        generator = FlowchartGenerator(stats_without_symbols, temp_output_file)

        with pytest.raises(ValueError, match="No symbols_by_file data found in stats"):
            generator.validate_inputs()

    def test_validate_inputs_fails_with_empty_symbols_by_file(self, temp_output_file):
        """Test validation fails when symbols_by_file is empty."""
        stats_empty_symbols = {
            'total_symbols': 0,
            'files_analyzed': 0,
            'symbols_by_file': {}
        }
        generator = FlowchartGenerator(stats_empty_symbols, temp_output_file)

        with pytest.raises(ValueError, match="No symbols_by_file data found in stats"):
            generator.validate_inputs()


class TestFlowchartBodyGeneration:
    """Test flowchart diagram body generation."""

    def test_generate_body_adds_flowchart_declaration(self, sample_stats, temp_output_file):
        """Test generate_body adds flowchart declaration."""
        generator = FlowchartGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        assert len(generator.lines) > 0
        assert generator.lines[0] == "graph TB"

    def test_generate_body_creates_directory_nodes(self, sample_stats, temp_output_file):
        """Test generate_body creates directory nodes."""
        generator = FlowchartGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should have directory nodes for /project/src and /project/lib
        assert 'DIR0' in lines_str
        assert 'DIR1' in lines_str
        assert 'symbols"]' in lines_str  # Directory nodes show symbol counts

    def test_generate_body_groups_files_by_directory(self, sample_stats, temp_output_file):
        """Test generate_body groups files by their parent directory."""
        generator = FlowchartGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # main.py and utils.py should be in same directory (src)
        assert 'main.py' in lines_str
        assert 'utils.py' in lines_str
        # module.py should be in different directory (lib)
        assert 'module.py' in lines_str

    def test_generate_body_limits_directories_to_ten(self, temp_output_file):
        """Test generate_body limits to top 10 directories."""
        # Create stats with 15 directories
        stats_many_dirs = {
            'total_symbols': 150,
            'files_analyzed': 15,
            'symbols_by_file': {
                f'/project/dir{i}/file.py': [{'name': f'func{i}', 'kind': 'function'}]
                for i in range(15)
            }
        }
        generator = FlowchartGenerator(stats_many_dirs, temp_output_file)

        generator.generate_body()

        # Count DIR nodes (should be max 10)
        dir_nodes = [line for line in generator.lines if line.strip().startswith('DIR')]
        assert len(dir_nodes) <= 10 * 2  # Each dir has 2 lines (node + style)

    def test_generate_body_adds_file_nodes_with_symbol_breakdown(self, sample_stats, temp_output_file):
        """Test generate_body adds file nodes with symbol type breakdowns."""
        generator = FlowchartGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # main.py has classes and functions, should show breakdown
        assert 'main.py' in lines_str
        assert 'classes' in lines_str or 'funcs' in lines_str

    def test_generate_body_limits_files_per_directory(self, temp_output_file):
        """Test generate_body limits to 5 files per directory."""
        # Create stats with 10 files in one directory
        stats_many_files = {
            'total_symbols': 100,
            'files_analyzed': 10,
            'symbols_by_file': {
                f'/project/src/file{i}.py': [
                    {'name': f'func{i}', 'kind': 'function'} for _ in range(10 - i)
                ]
                for i in range(10)
            }
        }
        generator = FlowchartGenerator(stats_many_files, temp_output_file)

        generator.generate_body()

        # Count file nodes (F0, F1, etc.)
        file_nodes = [line for line in generator.lines if 'F' in line and '[' in line and 'file' in line.lower()]
        assert len(file_nodes) <= 5  # Max 5 files per directory

    def test_generate_body_limits_total_files_to_thirty(self, temp_output_file):
        """Test generate_body limits to 30 files total."""
        # Create stats with 50 files across multiple directories
        stats_many_files = {
            'total_symbols': 500,
            'files_analyzed': 50,
            'symbols_by_file': {
                f'/project/dir{i}/file{j}.py': [{'name': 'func', 'kind': 'function'}]
                for i in range(10)
                for j in range(5)
            }
        }
        generator = FlowchartGenerator(stats_many_files, temp_output_file)

        generator.generate_body()

        # Count file nodes
        file_nodes = [line for line in generator.lines if line.strip().startswith('F') and '[' in line]
        assert len(file_nodes) <= 30

    def test_generate_body_adds_class_nodes_for_small_class_counts(self, sample_stats, temp_output_file):
        """Test generate_body adds class detail nodes when there are 1-5 classes."""
        generator = FlowchartGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # module.py has 2 classes, should create class nodes
        assert 'ClassA' in lines_str or 'ClassB' in lines_str
        assert 'methods"]' in lines_str

    def test_generate_body_skips_class_nodes_for_large_class_counts(self, temp_output_file):
        """Test generate_body skips class details when there are >5 classes."""
        stats_many_classes = {
            'total_symbols': 60,
            'files_analyzed': 1,
            'symbols_by_file': {
                '/project/big_file.py': [
                    {'name': f'Class{i}', 'kind': 'class'}
                    for i in range(10)
                ]
            }
        }
        generator = FlowchartGenerator(stats_many_classes, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should have file node but no individual class nodes (>5 classes)
        assert 'big_file.py' in lines_str
        # Count class nodes (C0_0, C0_1, etc.) - should be 0 or minimal
        class_nodes = [line for line in generator.lines if 'C' in line and '_' in line and '[' in line]
        assert len(class_nodes) == 0  # Should skip when >5 classes

    def test_generate_body_creates_directory_to_file_connections(self, sample_stats, temp_output_file):
        """Test generate_body creates arrows from directories to files."""
        generator = FlowchartGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should have connections like DIR0 --> F0
        assert 'DIR' in lines_str and '-->' in lines_str and 'F' in lines_str

    def test_generate_body_creates_file_to_class_connections(self, sample_stats, temp_output_file):
        """Test generate_body creates arrows from files to classes."""
        generator = FlowchartGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should have connections like F2 --> C2_0 (file to class)
        if 'C' in lines_str and '_' in lines_str:  # Only if class nodes exist
            assert '-->' in lines_str


class TestFlowchartEndToEnd:
    """Test complete end-to-end flowchart generation."""

    def test_full_generation_creates_valid_diagram(self, sample_stats, temp_output_file):
        """Test complete generation workflow produces valid flowchart."""
        generator = FlowchartGenerator(sample_stats, temp_output_file)

        result_path = generator.generate()

        assert result_path == temp_output_file
        assert os.path.exists(temp_output_file)

        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify structure
        assert "```mermaid" in content
        assert "graph TB" in content
        assert "DIR" in content  # Directory nodes
        assert "symbols" in content  # Symbol counts
        assert "```" in content
        assert "## Statistics" in content


class TestFlowchartEdgeCases:
    """Test edge cases specific to flowchart generation."""

    def test_generate_with_single_directory(self, temp_output_file):
        """Test generation with only one directory."""
        single_dir_stats = {
            'total_symbols': 10,
            'files_analyzed': 2,
            'symbols_by_file': {
                '/project/file1.py': [{'name': 'func1', 'kind': 'function'}],
                '/project/file2.py': [{'name': 'func2', 'kind': 'function'}]
            }
        }
        generator = FlowchartGenerator(single_dir_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "DIR0" in content
        assert "file1.py" in content
        assert "file2.py" in content

    def test_generate_with_files_without_classes(self, temp_output_file):
        """Test generation handles files with no class symbols."""
        no_class_stats = {
            'total_symbols': 10,
            'files_analyzed': 1,
            'symbols_by_file': {
                '/project/functions.py': [
                    {'name': 'func1', 'kind': 'function'},
                    {'name': 'func2', 'kind': 'function'},
                    {'name': 'func3', 'kind': 'function'}
                ]
            }
        }
        generator = FlowchartGenerator(no_class_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "functions.py" in content
        assert "funcs" in content  # Should show function count

    def test_generate_with_empty_symbol_lists(self, temp_output_file):
        """Test generation handles files with empty symbol lists."""
        empty_symbols_stats = {
            'total_symbols': 5,
            'files_analyzed': 2,
            'symbols_by_file': {
                '/project/has_symbols.py': [
                    {'name': 'func1', 'kind': 'function'}
                ],
                '/project/empty.py': []  # Empty list
            }
        }
        generator = FlowchartGenerator(empty_symbols_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        # File with symbols should appear
        assert "has_symbols.py" in content
        # Empty file should not appear (filtered out)
        assert "empty.py" not in content

    def test_generate_with_root_directory(self, temp_output_file):
        """Test generation handles files in root directory (parent is '.')."""
        root_dir_stats = {
            'total_symbols': 5,
            'files_analyzed': 1,
            'symbols_by_file': {
                'main.py': [{'name': 'func1', 'kind': 'function'}]
            }
        }
        generator = FlowchartGenerator(root_dir_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "main.py" in content
        assert "root" in content  # Should label as 'root' directory

    def test_generate_with_symbol_type_variety(self, temp_output_file):
        """Test generation handles various symbol types correctly."""
        variety_stats = {
            'total_symbols': 20,
            'files_analyzed': 1,
            'symbols_by_file': {
                '/project/mixed.py': [
                    {'name': 'MyClass', 'kind': 'class'},
                    {'name': 'func1', 'kind': 'function'},
                    {'name': 'func2', 'kind': 'function'},
                    {'name': 'method1', 'kind': 'method', 'scope': 'MyClass'},
                    {'name': 'var1', 'kind': 'variable'},
                    {'name': 'var2', 'kind': 'member'},
                ]
            }
        }
        generator = FlowchartGenerator(variety_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "mixed.py" in content
        # Should count: 1 class, 2 functions/methods, 2 variables/members
        assert "classes" in content or "class" in content
        assert "funcs" in content or "func" in content
        assert "vars" in content or "var" in content
