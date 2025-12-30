"""Tests for SequenceGenerator.

This module tests the sequence diagram generator functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from clickup_framework.commands.map_helpers.mermaid.exceptions import DataValidationError, FileOperationError
from clickup_framework.commands.map_helpers.mermaid.generators.sequence_generator import SequenceGenerator


@pytest.fixture
def sample_stats():
    """Sample statistics dictionary with function_calls and all_symbols data."""
    return {
        'total_symbols': 20,
        'files_analyzed': 3,
        'function_calls': {
            'App.main': ['App.init', 'Utils.process'],
            'App.init': ['Config.load'],
            'Utils.process': ['Utils.validate', 'Utils.transform'],
            'Utils.validate': [],
            'Utils.transform': [],
            'Config.load': []
        },
        'all_symbols': {
            'App.main': {'name': 'main', 'scope': 'App', 'kind': 'function'},
            'App.init': {'name': 'init', 'scope': 'App', 'kind': 'function'},
            'Utils.process': {'name': 'process', 'scope': 'Utils', 'kind': 'function'},
            'Utils.validate': {'name': 'validate', 'scope': 'Utils', 'kind': 'function'},
            'Utils.transform': {'name': 'transform', 'scope': 'Utils', 'kind': 'function'},
            'Config.load': {'name': 'load', 'scope': 'Config', 'kind': 'function'}
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


class TestSequenceValidation:
    """Test sequence diagram validation."""

    def test_validate_inputs_passes_with_valid_data(self, sample_stats, temp_output_file):
        """Test validation passes when function_calls and all_symbols data exists."""
        generator = SequenceGenerator(sample_stats, temp_output_file)

        # Should not raise any exceptions
        generator.validate_inputs()

    def test_validate_inputs_fails_without_function_calls(self, temp_output_file):
        """Test validation fails when function_calls is missing."""
        stats_without_calls = {
            'total_symbols': 10,
            'all_symbols': {'func1': {'name': 'func1', 'scope': 'Module'}}
        }
        generator = SequenceGenerator(stats_without_calls, temp_output_file)

        with pytest.raises(DataValidationError, match="Required field .* not found in stats data"):
            generator.validate_inputs()

    def test_validate_inputs_fails_without_all_symbols(self, temp_output_file):
        """Test validation fails when all_symbols is missing."""
        stats_without_symbols = {
            'total_symbols': 10,
            'function_calls': {'func1': ['func2']}
        }
        generator = SequenceGenerator(stats_without_symbols, temp_output_file)

        with pytest.raises(DataValidationError, match="Required field .* not found in stats data"):
            generator.validate_inputs()

    def test_validate_inputs_fails_with_empty_data(self, temp_output_file):
        """Test validation fails when data structures are empty."""
        stats_empty = {
            'total_symbols': 0,
            'function_calls': {},
            'all_symbols': {}
        }
        generator = SequenceGenerator(stats_empty, temp_output_file)

        with pytest.raises(DataValidationError, match="Required field .* not found in stats data"):
            generator.validate_inputs()


class TestSequenceBodyGeneration:
    """Test sequence diagram body generation."""

    def test_generate_body_adds_sequence_declaration(self, sample_stats, temp_output_file):
        """Test generate_body adds sequenceDiagram declaration."""
        generator = SequenceGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        assert len(generator.lines) > 0
        assert generator.lines[0] == "sequenceDiagram"

    def test_generate_body_detects_main_as_entry_point(self, sample_stats, temp_output_file):
        """Test generate_body detects 'main' as an entry point."""
        generator = SequenceGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should detect main() and start from it
        assert 'main()' in lines_str

    def test_generate_body_detects_init_as_entry_point(self, temp_output_file):
        """Test generate_body detects '__init__' pattern as entry point."""
        init_stats = {
            'function_calls': {
                'App.__init__': ['setup'],
                'setup': []
            },
            'all_symbols': {
                'App.__init__': {'name': '__init__', 'scope': 'App'},
                'setup': {'name': 'setup', 'scope': 'Module'}
            }
        }
        generator = SequenceGenerator(init_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        assert '__init__()' in lines_str or 'starts' in lines_str

    def test_generate_body_falls_back_to_most_called_functions(self, temp_output_file):
        """Test generate_body falls back to most-called functions when no entry patterns match."""
        no_entry_stats = {
            'function_calls': {
                'helper': ['utility'],
                'utility': [],
                'process_data': ['helper']
            },
            'all_symbols': {
                'helper': {'name': 'helper', 'scope': 'Utils'},
                'utility': {'name': 'utility', 'scope': 'Utils'},
                'process_data': {'name': 'process_data', 'scope': 'Data'}
            }
        }
        generator = SequenceGenerator(no_entry_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should pick the function with most calls (process_data has 1, helper has 1)
        assert 'sequenceDiagram' in lines_str
        assert len(generator.lines) > 1

    def test_generate_body_uses_scopes_in_arrows(self, sample_stats, temp_output_file):
        """Test generate_body uses scope names in call arrows."""
        generator = SequenceGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should reference scopes (App, Utils, Config) in arrows
        assert 'App' in lines_str or 'Utils' in lines_str or 'Config' in lines_str

    def test_generate_body_creates_call_arrows(self, sample_stats, temp_output_file):
        """Test generate_body creates call arrows between participants."""
        generator = SequenceGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should have call arrows (->>) between participants
        assert '->>' in lines_str

    def test_generate_body_creates_return_arrows(self, sample_stats, temp_output_file):
        """Test generate_body creates return arrows."""
        generator = SequenceGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should have return arrows (-->>)
        assert '-->>' in lines_str
        assert 'return' in lines_str

    def test_generate_body_limits_recursion_depth(self, temp_output_file):
        """Test generate_body limits recursion to prevent infinite loops."""
        # Create deep recursion scenario
        deep_stats = {
            'function_calls': {
                'level0': ['level1'],
                'level1': ['level2'],
                'level2': ['level3'],
                'level3': ['level4'],
                'level4': ['level5'],
                'level5': ['level6'],
                'level6': []
            },
            'all_symbols': {
                f'level{i}': {'name': f'level{i}', 'scope': 'Deep'}
                for i in range(7)
            }
        }
        generator = SequenceGenerator(deep_stats, temp_output_file)

        generator.generate_body()

        # Should not crash and should limit depth
        assert len(generator.lines) > 0
        lines_str = '\n'.join(generator.lines)
        # With max_depth=4, allows 5 levels (0-4), each creates call+return arrow = 10 arrows
        call_count = lines_str.count('->>')
        assert call_count <= 10  # Max depth 4 allows 5 levels of calls

    def test_generate_body_limits_calls_per_function(self, temp_output_file):
        """Test generate_body limits to 3 calls per function."""
        many_calls_stats = {
            'function_calls': {
                'main': ['call1', 'call2', 'call3', 'call4', 'call5'],
                'call1': [],
                'call2': [],
                'call3': [],
                'call4': [],
                'call5': []
            },
            'all_symbols': {
                'main': {'name': 'main', 'scope': 'App'},
                **{f'call{i}': {'name': f'call{i}', 'scope': 'Utils'} for i in range(1, 6)}
            }
        }
        generator = SequenceGenerator(many_calls_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should only show 3 calls from main (limited by [:3] in code)
        call_arrows = [line for line in generator.lines if '->>' in line and 'return' not in line]
        # Main calls at most 3 functions
        assert len(call_arrows) <= 3


class TestSequenceFooter:
    """Test sequence diagram footer generation."""

    def test_footer_includes_description(self, sample_stats, temp_output_file):
        """Test footer includes sequence-specific description."""
        generator = SequenceGenerator(sample_stats, temp_output_file)

        generator._add_footer()

        lines_str = '\n'.join(generator.lines)
        assert "## Description" in lines_str
        assert "sequence diagram" in lines_str.lower()
        assert "execution flow" in lines_str.lower()

    def test_footer_includes_entry_point_info(self, sample_stats, temp_output_file):
        """Test footer includes entry point information."""
        generator = SequenceGenerator(sample_stats, temp_output_file)

        generator._add_footer()

        lines_str = '\n'.join(generator.lines)
        assert "## Entry Point" in lines_str
        assert "Starting from:" in lines_str


class TestSequenceEndToEnd:
    """Test complete end-to-end sequence generation."""

    def test_full_generation_creates_valid_diagram(self, sample_stats, temp_output_file):
        """Test complete generation workflow produces valid sequence diagram."""
        generator = SequenceGenerator(sample_stats, temp_output_file)

        result_path = generator.generate()

        assert result_path == temp_output_file
        assert os.path.exists(temp_output_file)

        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify structure
        assert "```mermaid" in content
        assert "sequenceDiagram" in content
        assert "->>" in content  # Call arrows
        assert "-->>" in content  # Return arrows
        assert "```" in content
        assert "## Description" in content
        assert "## Entry Point" in content


class TestSequenceEdgeCases:
    """Test edge cases specific to sequence generation."""

    def test_generate_with_single_function_no_calls(self, temp_output_file):
        """Test generation with single function that makes no calls."""
        single_func_stats = {
            'function_calls': {
                'standalone': []
            },
            'all_symbols': {
                'standalone': {'name': 'standalone', 'scope': 'Module'}
            }
        }
        generator = SequenceGenerator(single_func_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "sequenceDiagram" in content

    def test_generate_with_circular_calls(self, temp_output_file):
        """Test generation handles circular function calls."""
        circular_stats = {
            'function_calls': {
                'funcA': ['funcB'],
                'funcB': ['funcC'],
                'funcC': ['funcA']  # Circular reference
            },
            'all_symbols': {
                'funcA': {'name': 'funcA', 'scope': 'Module'},
                'funcB': {'name': 'funcB', 'scope': 'Module'},
                'funcC': {'name': 'funcC', 'scope': 'Module'}
            }
        }
        generator = SequenceGenerator(circular_stats, temp_output_file)

        result = generator.generate()

        # Should not crash or infinite loop due to depth limit
        assert os.path.exists(result)

    def test_generate_with_functions_without_scope(self, temp_output_file):
        """Test generation handles functions without scope field."""
        no_scope_stats = {
            'function_calls': {
                'func1': ['func2'],
                'func2': []
            },
            'all_symbols': {
                'func1': {'name': 'func1'},  # No scope
                'func2': {'name': 'func2'}   # No scope
            }
        }
        generator = SequenceGenerator(no_scope_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should use 'Module' as default scope
        assert "Module" in content

    def test_generate_with_multiple_entry_patterns(self, temp_output_file):
        """Test generation prioritizes first matching entry pattern."""
        multi_entry_stats = {
            'function_calls': {
                'App.main': ['helper'],
                'Service.run': ['process'],
                'helper': [],
                'process': []
            },
            'all_symbols': {
                'App.main': {'name': 'main', 'scope': 'App'},
                'Service.run': {'name': 'run', 'scope': 'Service'},
                'helper': {'name': 'helper', 'scope': 'Utils'},
                'process': {'name': 'process', 'scope': 'Utils'}
            }
        }
        generator = SequenceGenerator(multi_entry_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should pick first matching pattern (main or run)
        assert 'main()' in content or 'run()' in content
