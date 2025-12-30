"""Tests for CodeFlowGenerator.

This module tests the code flow diagram generator functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from clickup_framework.commands.map_helpers.mermaid.exceptions import DataValidationError, FileOperationError
from clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator import CodeFlowGenerator


@pytest.fixture
def sample_stats():
    """Sample statistics dictionary with function_calls and all_symbols data."""
    return {
        'total_symbols': 30,
        'files_analyzed': 5,
        'function_calls': {
            'App.main': ['App.init', 'Utils.process'],
            'App.init': ['Config.load'],
            'Utils.process': ['Utils.validate', 'Utils.transform'],
            'Utils.validate': [],
            'Utils.transform': [],
            'Config.load': [],
            'Service.run': ['App.main'],  # Calls main
            'Helper.assist': []  # Not called by anyone (entry point)
        },
        'all_symbols': {
            'App.main': {'name': 'main', 'scope': 'App', 'kind': 'function', 'path': '/project/app.py', 'line': 10},
            'App.init': {'name': 'init', 'scope': 'App', 'kind': 'function', 'path': '/project/app.py', 'line': 20},
            'Utils.process': {'name': 'process', 'scope': 'Utils', 'kind': 'function', 'path': '/project/utils.py', 'line': 5},
            'Utils.validate': {'name': 'validate', 'scope': 'Utils', 'kind': 'function', 'path': '/project/utils.py', 'line': 15},
            'Utils.transform': {'name': 'transform', 'scope': 'Utils', 'kind': 'function', 'path': '/project/utils.py', 'line': 25},
            'Config.load': {'name': 'load', 'scope': 'Config', 'kind': 'function', 'path': '/project/config.py', 'line': 3},
            'Service.run': {'name': 'run', 'scope': 'Service', 'kind': 'function', 'path': '/project/service.py', 'line': 8},
            'Helper.assist': {'name': 'assist', 'scope': 'Helper', 'kind': 'function', 'path': '/project/helper.py', 'line': 12}
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


class TestCodeFlowValidation:
    """Test code flow diagram validation."""

    def test_validate_inputs_passes_with_valid_data(self, sample_stats, temp_output_file):
        """Test validation passes when function_calls and all_symbols data exists."""
        generator = CodeFlowGenerator(sample_stats, temp_output_file)

        # Should not raise any exceptions
        generator.validate_inputs()

    def test_validate_inputs_fails_without_function_calls(self, temp_output_file):
        """Test validation fails when function_calls is missing."""
        stats_without_calls = {
            'total_symbols': 10,
            'all_symbols': {'func1': {'name': 'func1', 'scope': 'Module'}}
        }
        generator = CodeFlowGenerator(stats_without_calls, temp_output_file)

        with pytest.raises(DataValidationError, match="Required field .* not found in stats data"):
            generator.validate_inputs()

    def test_validate_inputs_fails_without_all_symbols(self, temp_output_file):
        """Test validation fails when all_symbols is missing."""
        stats_without_symbols = {
            'total_symbols': 10,
            'function_calls': {'func1': ['func2']}
        }
        generator = CodeFlowGenerator(stats_without_symbols, temp_output_file)

        with pytest.raises(DataValidationError, match="Required field .* not found in stats data"):
            generator.validate_inputs()

    def test_validate_inputs_fails_with_empty_data(self, temp_output_file):
        """Test validation fails when data structures are empty."""
        stats_empty = {
            'total_symbols': 0,
            'function_calls': {},
            'all_symbols': {}
        }
        generator = CodeFlowGenerator(stats_empty, temp_output_file)

        with pytest.raises(DataValidationError, match="Required field .* not found in stats data"):
            generator.validate_inputs()


class TestCodeFlowHeader:
    """Test code flow header generation."""

    def test_add_header_includes_custom_mermaid_config(self, sample_stats, temp_output_file):
        """Test _add_header adds custom mermaid initialization config."""
        generator = CodeFlowGenerator(sample_stats, temp_output_file)

        generator._add_header()

        lines_str = '\n'.join(generator.lines)
        assert "Code Map - Execution Flow (Call Graph)" in lines_str
        assert "```mermaid" in lines_str
        assert "%%{init:" in lines_str
        assert "'flowchart'" in lines_str
        assert "'curve': 'linear'" in lines_str
        assert "'defaultRenderer': 'elk'" in lines_str


class TestCodeFlowBodyGeneration:
    """Test code flow diagram body generation."""

    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.NodeManager')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.TreeBuilder')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.LabelFormatter')
    def test_generate_body_adds_graph_declaration(self, mock_label_formatter, mock_tree_builder, mock_node_manager, sample_stats, temp_output_file):
        """Test generate_body adds graph TD declaration."""
        # Mock the dependencies
        mock_nm_instance = Mock()
        mock_nm_instance.processed = []
        mock_nm_instance.node_ids = {}
        mock_nm_instance.collect_functions_recursive.return_value = []
        mock_node_manager.return_value = mock_nm_instance

        mock_tb_instance = Mock()
        mock_tb_instance.scan_directory_structure.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.populate_tree_with_functions.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.has_functions_in_tree.return_value = False
        mock_tree_builder.return_value = mock_tb_instance

        generator = CodeFlowGenerator(sample_stats, temp_output_file)
        generator.generate_body()

        assert len(generator.lines) > 0
        assert generator.lines[0] == "graph TD"

    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.NodeManager')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.TreeBuilder')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.LabelFormatter')
    def test_generate_body_detects_entry_points(self, mock_label_formatter, mock_tree_builder, mock_node_manager, sample_stats, temp_output_file):
        """Test generate_body detects functions not called by others as entry points."""
        # Mock the dependencies
        mock_nm_instance = Mock()
        mock_nm_instance.processed = []
        mock_nm_instance.node_ids = {}
        mock_nm_instance.collect_functions_recursive.return_value = []
        mock_node_manager.return_value = mock_nm_instance

        mock_tb_instance = Mock()
        mock_tb_instance.scan_directory_structure.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.populate_tree_with_functions.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.has_functions_in_tree.return_value = False
        mock_tree_builder.return_value = mock_tb_instance

        generator = CodeFlowGenerator(sample_stats, temp_output_file)
        generator.generate_body()

        # Service.run and Helper.assist are entry points (not called by anyone)
        assert hasattr(generator, '_entry_points')
        entry_points = generator._entry_points
        assert 'Service.run' in entry_points or 'Helper.assist' in entry_points

    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.NodeManager')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.TreeBuilder')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.LabelFormatter')
    def test_generate_body_limits_entry_points_to_ten(self, mock_label_formatter, mock_tree_builder, mock_node_manager, temp_output_file):
        """Test generate_body limits to top 10 entry points."""
        # Create stats with 15 entry points
        many_entry_stats = {
            'function_calls': {f'entry{i}': [] for i in range(15)},
            'all_symbols': {f'entry{i}': {'name': f'entry{i}', 'path': f'/file{i}.py'} for i in range(15)}
        }

        # Mock the dependencies
        mock_nm_instance = Mock()
        mock_nm_instance.processed = []
        mock_nm_instance.node_ids = {}
        mock_nm_instance.collect_functions_recursive.return_value = []
        mock_node_manager.return_value = mock_nm_instance

        mock_tb_instance = Mock()
        mock_tb_instance.scan_directory_structure.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.populate_tree_with_functions.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.has_functions_in_tree.return_value = False
        mock_tree_builder.return_value = mock_tb_instance

        generator = CodeFlowGenerator(many_entry_stats, temp_output_file)
        generator.generate_body()

        entry_points = generator._entry_points
        assert len(entry_points) <= 10

    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.NodeManager')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.TreeBuilder')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.LabelFormatter')
    def test_generate_body_limits_total_nodes_to_eighty(self, mock_label_formatter, mock_tree_builder, mock_node_manager, sample_stats, temp_output_file):
        """Test generate_body limits to 80 total nodes."""
        # Mock NodeManager to track collection behavior
        mock_nm_instance = Mock()
        mock_nm_instance.processed = [f'func{i}' for i in range(80)]  # Simulate 80 collected
        mock_nm_instance.node_ids = {f'func{i}': f'N{i}' for i in range(80)}
        mock_nm_instance.collect_functions_recursive.return_value = [f'func{i}' for i in range(80)]
        mock_node_manager.return_value = mock_nm_instance

        mock_tb_instance = Mock()
        mock_tb_instance.scan_directory_structure.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.populate_tree_with_functions.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.has_functions_in_tree.return_value = False
        mock_tree_builder.return_value = mock_tb_instance

        generator = CodeFlowGenerator(sample_stats, temp_output_file)
        generator.generate_body()

        # Check that processed count doesn't exceed 80
        processed = generator._processed
        assert len(processed) <= 80

    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.NodeManager')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.TreeBuilder')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.LabelFormatter')
    def test_generate_body_uses_tree_builder(self, mock_label_formatter, mock_tree_builder, mock_node_manager, sample_stats, temp_output_file):
        """Test generate_body uses TreeBuilder to scan directory structure."""
        mock_nm_instance = Mock()
        mock_nm_instance.processed = []
        mock_nm_instance.node_ids = {}
        mock_nm_instance.collect_functions_recursive.return_value = []
        mock_node_manager.return_value = mock_nm_instance

        mock_tb_instance = Mock()
        mock_tb_instance.scan_directory_structure.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.populate_tree_with_functions.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.has_functions_in_tree.return_value = False
        mock_tree_builder.return_value = mock_tb_instance

        generator = CodeFlowGenerator(sample_stats, temp_output_file)
        generator.generate_body()

        # Verify TreeBuilder was instantiated
        mock_tree_builder.assert_called_once()
        # Verify scan_directory_structure was called
        mock_tb_instance.scan_directory_structure.assert_called_once()
        # Verify populate_tree_with_functions was called
        mock_tb_instance.populate_tree_with_functions.assert_called_once()

    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.NodeManager')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.TreeBuilder')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.LabelFormatter')
    def test_generate_body_creates_directory_subgraphs(self, mock_label_formatter, mock_tree_builder, mock_node_manager, sample_stats, temp_output_file):
        """Test generate_body creates DIR subgraphs."""
        mock_nm_instance = Mock()
        mock_nm_instance.processed = ['App.main']
        mock_nm_instance.node_ids = {'App.main': 'N0'}
        mock_nm_instance.collect_functions_recursive.return_value = ['App.main']
        mock_nm_instance.get_node_id.return_value = 'N0'
        mock_node_manager.return_value = mock_nm_instance

        mock_lf_instance = Mock()
        mock_lf_instance.format_function_label.return_value = "main()"
        mock_label_formatter.return_value = mock_lf_instance

        # Simulate tree structure with proper root-level __files__ and __subdirs__
        mock_tb_instance = Mock()
        mock_tb_instance.scan_directory_structure.return_value = {
            '__files__': {},  # Root level files
            '__subdirs__': {
                'project': {
                    '__files__': {
                        'app': {
                            'App': ['App.main']
                        }
                    },
                    '__subdirs__': {}
                }
            }
        }
        mock_tb_instance.populate_tree_with_functions.return_value = {
            '__files__': {},
            '__subdirs__': {
                'project': {
                    '__files__': {
                        'app': {
                            'App': ['App.main']
                        }
                    },
                    '__subdirs__': {}
                }
            }
        }
        mock_tb_instance.has_functions_in_tree.return_value = True
        mock_tree_builder.return_value = mock_tb_instance

        generator = CodeFlowGenerator(sample_stats, temp_output_file)
        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should have subgraph declarations
        assert 'subgraph' in lines_str
        assert 'DIR:' in lines_str

    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.NodeManager')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.TreeBuilder')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.LabelFormatter')
    def test_generate_body_creates_file_subgraphs(self, mock_label_formatter, mock_tree_builder, mock_node_manager, sample_stats, temp_output_file):
        """Test generate_body creates FILE subgraphs."""
        mock_nm_instance = Mock()
        mock_nm_instance.processed = ['App.main']
        mock_nm_instance.node_ids = {'App.main': 'N0'}
        mock_nm_instance.collect_functions_recursive.return_value = ['App.main']
        mock_nm_instance.get_node_id.return_value = 'N0'
        mock_node_manager.return_value = mock_nm_instance

        mock_lf_instance = Mock()
        mock_lf_instance.format_function_label.return_value = "main()"
        mock_label_formatter.return_value = mock_lf_instance

        # Simulate tree with proper root-level structure
        mock_tb_instance = Mock()
        mock_tb_instance.scan_directory_structure.return_value = {
            '__files__': {},
            '__subdirs__': {
                'project': {
                    '__files__': {
                        'app': {
                            'App': ['App.main']
                        }
                    },
                    '__subdirs__': {}
                }
            }
        }
        mock_tb_instance.populate_tree_with_functions.return_value = {
            '__files__': {},
            '__subdirs__': {
                'project': {
                    '__files__': {
                        'app': {
                            'App': ['App.main']
                        }
                    },
                    '__subdirs__': {}
                }
            }
        }
        mock_tb_instance.has_functions_in_tree.return_value = True
        mock_tree_builder.return_value = mock_tb_instance

        generator = CodeFlowGenerator(sample_stats, temp_output_file)
        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        assert 'FILE:' in lines_str


class TestCodeFlowFooter:
    """Test code flow footer generation."""

    def test_footer_includes_legend(self, sample_stats, temp_output_file):
        """Test footer includes legend section."""
        generator = CodeFlowGenerator(sample_stats, temp_output_file)
        # Set attributes that _add_footer expects
        generator._processed = ['func1', 'func2']
        generator._functions_by_folder = {'folder1': {'file1': {'Class1': ['func1']}}}
        generator._entry_points = ['func1']

        generator._add_footer()

        lines_str = '\n'.join(generator.lines)
        assert "## Legend" in lines_str
        assert "Purple nodes" in lines_str
        assert "Entry points" in lines_str
        assert "Green-bordered nodes" in lines_str
        assert "DIR subgraphs" in lines_str

    def test_footer_includes_detailed_statistics(self, sample_stats, temp_output_file):
        """Test footer includes detailed statistics."""
        generator = CodeFlowGenerator(sample_stats, temp_output_file)
        generator.stats = sample_stats
        generator._processed = ['func1', 'func2', 'func3']
        generator._functions_by_folder = {
            'folder1': {'file1': {'Class1': ['func1', 'func2']}},
            'folder2': {'file2': {'Class2': ['func3']}}
        }
        generator._entry_points = ['func1']

        generator._add_footer()

        lines_str = '\n'.join(generator.lines)
        assert "## Statistics" in lines_str
        assert "Total Functions Mapped" in lines_str
        assert "Folders" in lines_str
        assert "File Components" in lines_str
        assert "Entry Points Found" in lines_str
        assert "Directory Tree Depth" in lines_str


class TestCodeFlowEndToEnd:
    """Test complete end-to-end code flow generation."""

    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.NodeManager')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.TreeBuilder')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.LabelFormatter')
    def test_full_generation_creates_valid_diagram(self, mock_label_formatter, mock_tree_builder, mock_node_manager, sample_stats, temp_output_file):
        """Test complete generation workflow produces valid code flow diagram."""
        # Mock dependencies
        mock_nm_instance = Mock()
        mock_nm_instance.processed = ['App.main', 'Utils.process']
        mock_nm_instance.node_ids = {'App.main': 'N0', 'Utils.process': 'N1'}
        mock_nm_instance.collect_functions_recursive.return_value = ['App.main', 'Utils.process']
        mock_nm_instance.get_node_id.side_effect = lambda x: mock_nm_instance.node_ids.get(x, None)
        mock_node_manager.return_value = mock_nm_instance

        mock_lf_instance = Mock()
        mock_lf_instance.format_function_label.side_effect = lambda name, symbol: f"{name}()"
        mock_label_formatter.return_value = mock_lf_instance

        mock_tb_instance = Mock()
        mock_tb_instance.scan_directory_structure.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.populate_tree_with_functions.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.has_functions_in_tree.return_value = False
        mock_tree_builder.return_value = mock_tb_instance

        generator = CodeFlowGenerator(sample_stats, temp_output_file)
        result_path = generator.generate()

        assert result_path == temp_output_file
        assert os.path.exists(temp_output_file)

        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify structure
        assert "# Code Map - Execution Flow (Call Graph)" in content
        assert "```mermaid" in content
        assert "%%{init:" in content
        assert "graph TD" in content
        assert "```" in content
        assert "## Legend" in content
        assert "## Statistics" in content


class TestCodeFlowEdgeCases:
    """Test edge cases specific to code flow generation."""

    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.NodeManager')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.TreeBuilder')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.LabelFormatter')
    def test_generate_with_no_entry_points(self, mock_label_formatter, mock_tree_builder, mock_node_manager, temp_output_file):
        """Test generation when all functions are called by others."""
        circular_stats = {
            'function_calls': {
                'funcA': ['funcB'],
                'funcB': ['funcC'],
                'funcC': ['funcA']  # Circular - no entry points
            },
            'all_symbols': {
                'funcA': {'name': 'funcA', 'path': '/file.py'},
                'funcB': {'name': 'funcB', 'path': '/file.py'},
                'funcC': {'name': 'funcC', 'path': '/file.py'}
            }
        }

        mock_nm_instance = Mock()
        mock_nm_instance.processed = []
        mock_nm_instance.node_ids = {}
        mock_nm_instance.collect_functions_recursive.return_value = []
        mock_node_manager.return_value = mock_nm_instance

        mock_tb_instance = Mock()
        mock_tb_instance.scan_directory_structure.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.populate_tree_with_functions.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.has_functions_in_tree.return_value = False
        mock_tree_builder.return_value = mock_tb_instance

        generator = CodeFlowGenerator(circular_stats, temp_output_file)
        result = generator.generate()

        assert os.path.exists(result)
        # Should handle gracefully with empty entry_points list

    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.NodeManager')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.TreeBuilder')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.LabelFormatter')
    def test_generate_with_functions_without_path(self, mock_label_formatter, mock_tree_builder, mock_node_manager, temp_output_file):
        """Test generation handles functions without path field."""
        no_path_stats = {
            'function_calls': {
                'func1': ['func2'],
                'func2': []
            },
            'all_symbols': {
                'func1': {'name': 'func1'},  # No path
                'func2': {'name': 'func2'}   # No path
            }
        }

        mock_nm_instance = Mock()
        mock_nm_instance.processed = ['func1', 'func2']
        mock_nm_instance.node_ids = {'func1': 'N0', 'func2': 'N1'}
        mock_nm_instance.collect_functions_recursive.return_value = ['func1', 'func2']
        mock_node_manager.return_value = mock_nm_instance

        mock_tb_instance = Mock()
        mock_tb_instance.scan_directory_structure.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.populate_tree_with_functions.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.has_functions_in_tree.return_value = False
        mock_tree_builder.return_value = mock_tb_instance

        generator = CodeFlowGenerator(no_path_stats, temp_output_file)
        result = generator.generate()

        assert os.path.exists(result)
        # Should group under 'root'/'unknown'/'global' when no path

    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.NodeManager')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.TreeBuilder')
    @patch('clickup_framework.commands.map_helpers.mermaid.generators.code_flow_generator.LabelFormatter')
    def test_generate_limits_calls_to_five_per_function(self, mock_label_formatter, mock_tree_builder, mock_node_manager, temp_output_file):
        """Test generation limits to 5 calls per function."""
        many_calls_stats = {
            'function_calls': {
                'main': ['call1', 'call2', 'call3', 'call4', 'call5', 'call6', 'call7'],
                'call1': [], 'call2': [], 'call3': [], 'call4': [], 'call5': [], 'call6': [], 'call7': []
            },
            'all_symbols': {
                'main': {'name': 'main', 'path': '/app.py'},
                **{f'call{i}': {'name': f'call{i}', 'path': '/app.py'} for i in range(1, 8)}
            }
        }

        mock_nm_instance = Mock()
        mock_nm_instance.processed = ['main']
        mock_nm_instance.node_ids = {'main': 'N0', 'call1': 'N1', 'call2': 'N2', 'call3': 'N3', 'call4': 'N4', 'call5': 'N5'}
        mock_nm_instance.collect_functions_recursive.return_value = ['main']
        mock_node_manager.return_value = mock_nm_instance

        mock_tb_instance = Mock()
        mock_tb_instance.scan_directory_structure.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.populate_tree_with_functions.return_value = {'__files__': {}, '__subdirs__': {}}
        mock_tb_instance.has_functions_in_tree.return_value = False
        mock_tree_builder.return_value = mock_tb_instance

        generator = CodeFlowGenerator(many_calls_stats, temp_output_file)
        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Count arrows from main (should be limited to 5)
        arrow_count = lines_str.count('N0 -->')
        assert arrow_count <= 5
