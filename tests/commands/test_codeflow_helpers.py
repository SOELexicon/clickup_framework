"""Unit tests for codeflow_helpers module.

Tests for the pure utility functions extracted from TreeBuilder:
- has_functions_in_tree
- populate_tree_with_functions
"""

import pytest
from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import (
    has_functions_in_tree,
    populate_tree_with_functions,
    DirectoryTreeBuilder
)


class TestHasFunctionsInTree:
    """Tests for has_functions_in_tree function."""

    def test_empty_tree_node(self):
        """Test that empty tree node returns False."""
        tree_node = {'__files__': {}, '__subdirs__': {}}
        assert has_functions_in_tree(tree_node) is False

    def test_node_with_single_function(self):
        """Test that node with a single function returns True."""
        tree_node = {
            '__files__': {'module.py': {'MyClass': ['func1']}},
            '__subdirs__': {}
        }
        assert has_functions_in_tree(tree_node) is True

    def test_node_with_multiple_functions(self):
        """Test that node with multiple functions returns True."""
        tree_node = {
            '__files__': {'module.py': {'MyClass': ['func1', 'func2', 'func3']}},
            '__subdirs__': {}
        }
        assert has_functions_in_tree(tree_node) is True

    def test_node_with_multiple_classes(self):
        """Test that node with multiple classes returns True."""
        tree_node = {
            '__files__': {
                'module.py': {
                    'ClassA': ['method1'],
                    'ClassB': ['method2', 'method3']
                }
            },
            '__subdirs__': {}
        }
        assert has_functions_in_tree(tree_node) is True

    def test_node_with_empty_class(self):
        """Test that node with empty class dict returns False."""
        tree_node = {
            '__files__': {'module.py': {'MyClass': []}},
            '__subdirs__': {}
        }
        assert has_functions_in_tree(tree_node) is False

    def test_node_with_nested_functions_in_subdirs(self):
        """Test that functions in subdirectories are detected."""
        tree_node = {
            '__files__': {},
            '__subdirs__': {
                'subdir1': {
                    '__files__': {'test.py': {'TestClass': ['test_func']}},
                    '__subdirs__': {}
                }
            }
        }
        assert has_functions_in_tree(tree_node) is True

    def test_deep_nesting_with_functions(self):
        """Test that deeply nested functions are detected."""
        tree_node = {
            '__files__': {},
            '__subdirs__': {
                'level1': {
                    '__files__': {},
                    '__subdirs__': {
                        'level2': {
                            '__files__': {},
                            '__subdirs__': {
                                'level3': {
                                    '__files__': {'deep.py': {'DeepClass': ['deep_func']}},
                                    '__subdirs__': {}
                                }
                            }
                        }
                    }
                }
            }
        }
        assert has_functions_in_tree(tree_node) is True

    def test_multiple_subdirs_one_with_functions(self):
        """Test that functions in any subdir are detected."""
        tree_node = {
            '__files__': {},
            '__subdirs__': {
                'empty1': {'__files__': {}, '__subdirs__': {}},
                'empty2': {'__files__': {}, '__subdirs__': {}},
                'with_funcs': {
                    '__files__': {'code.py': {'Code': ['run']}},
                    '__subdirs__': {}
                }
            }
        }
        assert has_functions_in_tree(tree_node) is True

    def test_node_without_files_key(self):
        """Test node missing __files__ key defaults to empty dict."""
        tree_node = {'__subdirs__': {}}
        assert has_functions_in_tree(tree_node) is False

    def test_node_without_subdirs_key(self):
        """Test node missing __subdirs__ key defaults to empty dict."""
        tree_node = {'__files__': {}}
        assert has_functions_in_tree(tree_node) is False

    def test_minimal_node(self):
        """Test completely empty node returns False."""
        tree_node = {}
        assert has_functions_in_tree(tree_node) is False

    def test_complex_mixed_structure(self):
        """Test complex structure with mixed empty and populated nodes."""
        tree_node = {
            '__files__': {'main.py': {'Main': []}},  # Empty class
            '__subdirs__': {
                'utils': {
                    '__files__': {'helpers.py': {'Helper': []}},  # Empty class
                    '__subdirs__': {
                        'core': {
                            '__files__': {'engine.py': {'Engine': ['start', 'stop']}},
                            '__subdirs__': {}
                        }
                    }
                }
            }
        }
        assert has_functions_in_tree(tree_node) is True


class TestPopulateTreeWithFunctions:
    """Tests for populate_tree_with_functions function."""

    def test_empty_functions_dict(self):
        """Test that empty functions dict doesn't modify tree."""
        tree = {'__files__': {}, '__subdirs__': {}}
        functions = {}
        result = populate_tree_with_functions(tree, functions)
        assert result == {'__files__': {}, '__subdirs__': {}}

    def test_populate_root_functions(self):
        """Test populating functions at root level."""
        tree = {'__files__': {}, '__subdirs__': {}}
        functions = {'root': {'module': {'MyClass': ['func1', 'func2']}}}
        result = populate_tree_with_functions(tree, functions)
        assert result['__files__'] == {'module': {'MyClass': ['func1', 'func2']}}

    def test_populate_single_subdirectory(self):
        """Test populating functions in a single subdirectory."""
        tree = {
            '__files__': {},
            '__subdirs__': {
                'src': {'__files__': {}, '__subdirs__': {}}
            }
        }
        functions = {'src': {'main': {'App': ['run']}}}
        result = populate_tree_with_functions(tree, functions)
        assert result['__subdirs__']['src']['__files__'] == {'main': {'App': ['run']}}

    def test_populate_nested_directory(self):
        """Test populating functions in nested directories."""
        tree = {
            '__files__': {},
            '__subdirs__': {
                'src': {
                    '__files__': {},
                    '__subdirs__': {
                        'utils': {'__files__': {}, '__subdirs__': {}}
                    }
                }
            }
        }
        functions = {'src/utils': {'helpers': {'Helper': ['help']}}}
        result = populate_tree_with_functions(tree, functions)
        expected_files = {'helpers': {'Helper': ['help']}}
        assert result['__subdirs__']['src']['__subdirs__']['utils']['__files__'] == expected_files

    def test_populate_with_backslash_paths(self):
        """Test that backslash paths are normalized to forward slashes."""
        tree = {
            '__files__': {},
            '__subdirs__': {
                'src': {
                    '__files__': {},
                    '__subdirs__': {
                        'core': {'__files__': {}, '__subdirs__': {}}
                    }
                }
            }
        }
        functions = {'src\\core': {'engine': {'Engine': ['start']}}}
        result = populate_tree_with_functions(tree, functions)
        expected_files = {'engine': {'Engine': ['start']}}
        assert result['__subdirs__']['src']['__subdirs__']['core']['__files__'] == expected_files

    def test_skip_nonexistent_directories(self):
        """Test that functions for nonexistent directories are skipped."""
        tree = {
            '__files__': {},
            '__subdirs__': {
                'src': {'__files__': {}, '__subdirs__': {}}
            }
        }
        # Try to populate nonexistent 'lib' directory
        functions = {'lib': {'utils': {'Utils': ['util_func']}}}
        result = populate_tree_with_functions(tree, functions)
        # Tree should remain unchanged
        assert result['__subdirs__']['src']['__files__'] == {}
        assert '__files__' not in result or 'utils' not in result.get('__files__', {})

    def test_populate_multiple_folders(self):
        """Test populating functions in multiple folders."""
        tree = {
            '__files__': {},
            '__subdirs__': {
                'src': {'__files__': {}, '__subdirs__': {}},
                'tests': {'__files__': {}, '__subdirs__': {}}
            }
        }
        functions = {
            'src': {'main': {'Main': ['run']}},
            'tests': {'test_main': {'TestMain': ['test_run']}}
        }
        result = populate_tree_with_functions(tree, functions)
        assert result['__subdirs__']['src']['__files__'] == {'main': {'Main': ['run']}}
        assert result['__subdirs__']['tests']['__files__'] == {'test_main': {'TestMain': ['test_run']}}

    def test_populate_creates_files_dict_if_missing(self):
        """Test that __files__ dict is created if it doesn't exist."""
        tree = {
            '__subdirs__': {
                'src': {'__subdirs__': {}}  # Missing __files__ key
            }
        }
        functions = {'src': {'module': {'Module': ['func']}}}
        result = populate_tree_with_functions(tree, functions)
        assert '__files__' in result['__subdirs__']['src']
        assert result['__subdirs__']['src']['__files__'] == {'module': {'Module': ['func']}}

    def test_populate_root_creates_files_dict(self):
        """Test that root __files__ dict is created if missing."""
        tree = {'__subdirs__': {}}  # Missing __files__ at root
        functions = {'root': {'main': {'Main': ['main']}}}
        result = populate_tree_with_functions(tree, functions)
        assert '__files__' in result
        assert result['__files__'] == {'main': {'Main': ['main']}}

    def test_populate_handles_dot_paths(self):
        """Test that paths with dots are handled correctly."""
        tree = {
            '__files__': {},
            '__subdirs__': {
                'src': {'__files__': {}, '__subdirs__': {}}
            }
        }
        functions = {'./src': {'code': {'Code': ['method']}}}
        result = populate_tree_with_functions(tree, functions)
        assert result['__subdirs__']['src']['__files__'] == {'code': {'Code': ['method']}}

    def test_populate_handles_empty_path_parts(self):
        """Test that empty path parts are skipped."""
        tree = {
            '__files__': {},
            '__subdirs__': {
                'src': {'__files__': {}, '__subdirs__': {}}
            }
        }
        functions = {'src//': {'file': {'Class': ['func']}}}
        result = populate_tree_with_functions(tree, functions)
        # Should still populate 'src' correctly despite double slash
        assert result['__subdirs__']['src']['__files__'] == {'file': {'Class': ['func']}}

    def test_populate_updates_existing_files(self):
        """Test that existing files are updated with new functions."""
        tree = {
            '__files__': {'existing': {'ExistingClass': ['old_func']}},
            '__subdirs__': {}
        }
        functions = {'root': {'new_file': {'NewClass': ['new_func']}}}
        result = populate_tree_with_functions(tree, functions)
        # Should have both old and new files
        assert 'existing' in result['__files__']
        assert 'new_file' in result['__files__']
        assert result['__files__']['existing'] == {'ExistingClass': ['old_func']}
        assert result['__files__']['new_file'] == {'NewClass': ['new_func']}

    def test_populate_deep_three_levels(self):
        """Test populating functions three levels deep."""
        tree = {
            '__files__': {},
            '__subdirs__': {
                'a': {
                    '__files__': {},
                    '__subdirs__': {
                        'b': {
                            '__files__': {},
                            '__subdirs__': {
                                'c': {'__files__': {}, '__subdirs__': {}}
                            }
                        }
                    }
                }
            }
        }
        functions = {'a/b/c': {'deep': {'Deep': ['deep_func']}}}
        result = populate_tree_with_functions(tree, functions)
        expected = {'deep': {'Deep': ['deep_func']}}
        assert result['__subdirs__']['a']['__subdirs__']['b']['__subdirs__']['c']['__files__'] == expected

    def test_populate_returns_same_tree_object(self):
        """Test that function modifies and returns the same tree object."""
        tree = {'__files__': {}, '__subdirs__': {}}
        functions = {'root': {'module': {'Class': ['func']}}}
        result = populate_tree_with_functions(tree, functions)
        # Should be the same object (modified in place)
        assert result is tree
        assert tree['__files__'] == {'module': {'Class': ['func']}}


class TestIntegrationScenarios:
    """Integration tests combining both functions."""

    def test_populate_then_check_has_functions(self):
        """Test that populated tree is correctly detected by has_functions_in_tree."""
        tree = {
            '__files__': {},
            '__subdirs__': {
                'src': {'__files__': {}, '__subdirs__': {}}
            }
        }
        functions = {'src': {'main': {'Main': ['run']}}}

        # Initially should have no functions
        assert has_functions_in_tree(tree) is False

        # Populate tree
        populate_tree_with_functions(tree, functions)

        # Now should have functions
        assert has_functions_in_tree(tree) is True

    def test_complex_real_world_scenario(self):
        """Test a complex real-world scenario with multiple directories and files."""
        # Simulated directory structure
        tree = {
            '__files__': {},
            '__subdirs__': {
                'src': {
                    '__files__': {},
                    '__subdirs__': {
                        'core': {'__files__': {}, '__subdirs__': {}},
                        'utils': {'__files__': {}, '__subdirs__': {}}
                    }
                },
                'tests': {
                    '__files__': {},
                    '__subdirs__': {}
                }
            }
        }

        # Collected functions
        functions = {
            'root': {'__init__': {'module_init': ['setup']}},
            'src/core': {
                'engine': {'Engine': ['start', 'stop', 'restart']},
                'config': {'Config': ['load', 'save']}
            },
            'src/utils': {
                'helpers': {'Helper': ['format_string', 'validate_input']}
            },
            'tests': {
                'test_engine': {'TestEngine': ['test_start', 'test_stop']}
            }
        }

        # Populate
        populate_tree_with_functions(tree, functions)

        # Verify structure
        assert has_functions_in_tree(tree) is True
        assert '__init__' in tree['__files__']
        assert 'engine' in tree['__subdirs__']['src']['__subdirs__']['core']['__files__']
        assert 'helpers' in tree['__subdirs__']['src']['__subdirs__']['utils']['__files__']
        assert 'test_engine' in tree['__subdirs__']['tests']['__files__']

        # Verify specific functions
        core_engine = tree['__subdirs__']['src']['__subdirs__']['core']['__files__']['engine']
        assert core_engine['Engine'] == ['start', 'stop', 'restart']

    def test_empty_tree_stays_empty(self):
        """Test that empty tree with no functions stays empty."""
        tree = {'__files__': {}, '__subdirs__': {}}
        functions = {}

        assert has_functions_in_tree(tree) is False
        populate_tree_with_functions(tree, functions)
        assert has_functions_in_tree(tree) is False


class TestSubgraphGenerator:
    """Tests for SubgraphGenerator class."""

    class MockNodeManager:
        """Mock node manager for testing."""
        def __init__(self):
            self.counter = 0

        def get_node_id(self, func_name):
            """Return a mock node ID."""
            self.counter += 1
            return f"N{self.counter}"

    class MockLabelFormatter:
        """Mock label formatter for testing."""
        def format_function_label(self, func_name, symbol):
            """Return a formatted label."""
            line = symbol.get('line', 0)
            return f"{func_name}:{line}" if line else func_name

    def test_init(self):
        """Test SubgraphGenerator initialization."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        node_mgr = self.MockNodeManager()
        formatter = self.MockLabelFormatter()
        symbols = {'func1': {'line': 42}}

        gen = SubgraphGenerator(
            node_manager=node_mgr,
            label_formatter=formatter,
            collected_symbols=symbols,
            max_functions_per_class=5
        )

        assert gen.node_manager is node_mgr
        assert gen.label_formatter is formatter
        assert gen.collected_symbols == symbols
        assert gen.max_functions_per_class == 5
        assert gen.lines == []
        assert gen.subgraph_count == 0
        assert gen.file_sg_count == 0

    def test_init_default_max_functions(self):
        """Test default max_functions_per_class value."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={}
        )

        assert gen.max_functions_per_class == 10

    def test_generate_file_subgraphs_single_file_single_class(self):
        """Test generating subgraph for single file with single class."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={'func1': {'line': 10}, 'func2': {'line': 20}}
        )

        files = {'main.py': {'Main': ['func1', 'func2']}}
        gen.generate_file_subgraphs(files, depth=0)

        lines = gen.get_lines()
        assert len(lines) > 0
        assert any('FILE: main.py' in line for line in lines)
        assert any('func1:10' in line for line in lines)
        assert any('func2:20' in line for line in lines)
        assert gen.file_sg_count == 1

    def test_generate_file_subgraphs_multiple_classes(self):
        """Test generating subgraphs with multiple classes in one file."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={
                'create': {'line': 10},
                'delete': {'line': 20},
                'grant': {'line': 30}
            }
        )

        files = {
            'service.py': {
                'UserService': ['create', 'delete'],
                'AdminService': ['grant']
            }
        }
        gen.generate_file_subgraphs(files, depth=0)

        lines = gen.get_lines()
        assert any('FILE: service.py' in line for line in lines)
        assert any('CLASS: UserService' in line for line in lines)
        assert any('CLASS: AdminService' in line for line in lines)
        assert gen.file_sg_count == 1

    def test_generate_file_subgraphs_respects_max_functions(self):
        """Test that max_functions_per_class limit is respected."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={f'func{i}': {'line': i} for i in range(20)},
            max_functions_per_class=3
        )

        files = {
            'test.py': {
                'TestClass': [f'func{i}' for i in range(20)]
            }
        }
        gen.generate_file_subgraphs(files, depth=0)

        lines = gen.get_lines()
        # Should only have 3 function nodes
        function_nodes = [line for line in lines if 'func' in line and 'N' in line]
        assert len(function_nodes) == 3

    def test_generate_file_subgraphs_skips_empty_files(self):
        """Test that empty files are skipped."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={}
        )

        files = {'empty.py': {}}
        gen.generate_file_subgraphs(files, depth=0)

        assert len(gen.get_lines()) == 0
        assert gen.file_sg_count == 0

    def test_generate_file_subgraphs_skips_empty_classes(self):
        """Test that classes with no functions are skipped."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={}
        )

        files = {'test.py': {'EmptyClass': []}}
        gen.generate_file_subgraphs(files, depth=0)

        lines = gen.get_lines()
        # Should create file subgraph but no content
        assert any('FILE: test.py' in line for line in lines)
        assert not any('EmptyClass' in line for line in lines)

    def test_generate_nested_subgraphs_root_files(self):
        """Test generating subgraphs for root level files."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={'main': {'line': 1}}
        )

        tree = {
            '__files__': {'main.py': {'module_main': ['main']}},
            '__subdirs__': {}
        }

        gen.generate_nested_subgraphs(tree)

        lines = gen.get_lines()
        assert any('FILE: main.py' in line for line in lines)
        assert gen.subgraph_count == 0  # No directory subgraphs at root
        assert gen.file_sg_count == 1

    def test_generate_nested_subgraphs_single_directory(self):
        """Test generating subgraph for single directory."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={'helper': {'line': 10}}
        )

        tree = {
            '__files__': {},
            '__subdirs__': {
                'utils': {
                    '__files__': {'helpers.py': {'Helper': ['helper']}},
                    '__subdirs__': {}
                }
            }
        }

        gen.generate_nested_subgraphs(tree)

        lines = gen.get_lines()
        assert any('DIR: utils' in line for line in lines)
        assert any('FILE: helpers.py' in line for line in lines)
        assert gen.subgraph_count == 1
        assert gen.file_sg_count == 1

    def test_generate_nested_subgraphs_nested_directories(self):
        """Test generating subgraphs for nested directories."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={'core_func': {'line': 5}}
        )

        tree = {
            '__files__': {},
            '__subdirs__': {
                'src': {
                    '__files__': {},
                    '__subdirs__': {
                        'core': {
                            '__files__': {'engine.py': {'Engine': ['core_func']}},
                            '__subdirs__': {}
                        }
                    }
                }
            }
        }

        gen.generate_nested_subgraphs(tree)

        lines = gen.get_lines()
        assert any('DIR: src' in line for line in lines)
        assert any('DIR: core' in line for line in lines)
        assert any('FILE: engine.py' in line for line in lines)
        assert gen.subgraph_count == 2
        assert gen.file_sg_count == 1

    def test_generate_nested_subgraphs_skips_empty_directories(self):
        """Test that directories without functions are skipped."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={'func': {'line': 1}}
        )

        tree = {
            '__files__': {},
            '__subdirs__': {
                'empty_dir': {
                    '__files__': {},
                    '__subdirs__': {}
                },
                'with_code': {
                    '__files__': {'test.py': {'Test': ['func']}},
                    '__subdirs__': {}
                }
            }
        }

        gen.generate_nested_subgraphs(tree)

        lines = gen.get_lines()
        assert not any('DIR: empty_dir' in line for line in lines)
        assert any('DIR: with_code' in line for line in lines)
        assert gen.subgraph_count == 1

    def test_generate_nested_subgraphs_depth_indentation(self):
        """Test that subgraph indentation increases with depth."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={'func': {'line': 1}}
        )

        tree = {
            '__files__': {},
            '__subdirs__': {
                'level1': {
                    '__files__': {},
                    '__subdirs__': {
                        'level2': {
                            '__files__': {'deep.py': {'Deep': ['func']}},
                            '__subdirs__': {}
                        }
                    }
                }
            }
        }

        gen.generate_nested_subgraphs(tree)

        lines = gen.get_lines()
        # Level 1 should have 1 indent (4 spaces)
        level1_lines = [l for l in lines if 'DIR: level1' in l]
        assert len(level1_lines) > 0
        assert level1_lines[0].startswith('    subgraph')

        # Level 2 should have 2 indents (8 spaces)
        level2_lines = [l for l in lines if 'DIR: level2' in l]
        assert len(level2_lines) > 0
        assert level2_lines[0].startswith('        subgraph')

    def test_get_lines_returns_copy(self):
        """Test that get_lines returns the lines list."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={}
        )

        gen.lines = ['line1', 'line2', 'line3']
        result = gen.get_lines()

        assert result == ['line1', 'line2', 'line3']
        assert result is gen.lines  # Same object for efficiency

    def test_get_counts_returns_tuple(self):
        """Test that get_counts returns correct tuple."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={}
        )

        gen.subgraph_count = 5
        gen.file_sg_count = 3

        sg_count, file_count = gen.get_counts()
        assert sg_count == 5
        assert file_count == 3

    def test_complex_real_world_scenario(self):
        """Test a complex real-world scenario with mixed content."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={
                'main': {'line': 1},
                'start': {'line': 10},
                'stop': {'line': 20},
                'load': {'line': 30},
                'test_start': {'line': 40}
            },
            max_functions_per_class=10
        )

        tree = {
            '__files__': {'__init__.py': {'module___init__': ['main']}},
            '__subdirs__': {
                'src': {
                    '__files__': {},
                    '__subdirs__': {
                        'core': {
                            '__files__': {
                                'engine.py': {'Engine': ['start', 'stop']},
                                'config.py': {'Config': ['load']}
                            },
                            '__subdirs__': {}
                        }
                    }
                },
                'tests': {
                    '__files__': {'test_engine.py': {'TestEngine': ['test_start']}},
                    '__subdirs__': {}
                }
            }
        }

        gen.generate_nested_subgraphs(tree)

        lines = gen.get_lines()
        sg_count, file_count = gen.get_counts()

        # Verify structure
        assert any('FILE: __init__.py' in line for line in lines)
        assert any('DIR: src' in line for line in lines)
        assert any('DIR: core' in line for line in lines)
        assert any('DIR: tests' in line for line in lines)
        assert any('FILE: engine.py' in line for line in lines)
        assert any('FILE: config.py' in line for line in lines)
        assert any('FILE: test_engine.py' in line for line in lines)

        # Verify counts
        assert sg_count == 3  # src, core, tests
        assert file_count == 4  # __init__, engine, config, test_engine

    def test_module_level_functions_no_class_subgraph(self):
        """Test that module-level functions don't create class subgraphs."""
        from clickup_framework.commands.map_helpers.mermaid.generators.codeflow_helpers import SubgraphGenerator

        gen = SubgraphGenerator(
            node_manager=self.MockNodeManager(),
            label_formatter=self.MockLabelFormatter(),
            collected_symbols={'helper': {'line': 5}}
        )

        files = {'utils.py': {'module_utils': ['helper']}}
        gen.generate_file_subgraphs(files, depth=0)

        lines = gen.get_lines()
        # Should NOT have CLASS: subgraph for module_ prefixed classes
        assert not any('CLASS:' in line for line in lines)
        assert any('FILE: utils.py' in line for line in lines)


class TestDirectoryTreeBuilder:
    """Tests for DirectoryTreeBuilder wrapper class."""

    def test_init_with_defaults(self, tmp_path):
        """Test initialization with default parameters."""
        builder = DirectoryTreeBuilder(str(tmp_path))

        assert builder.base_path == tmp_path
        assert builder.max_depth == 5
        assert builder.exclude_dirs == DirectoryTreeBuilder._default_exclude_dirs()
        assert hasattr(builder, '_tree_builder')

    def test_init_with_custom_params(self, tmp_path):
        """Test initialization with custom parameters."""
        custom_exclude = {'.git', '__pycache__'}
        builder = DirectoryTreeBuilder(
            str(tmp_path),
            max_depth=3,
            exclude_dirs=custom_exclude
        )

        assert builder.base_path == tmp_path
        assert builder.max_depth == 3
        assert builder.exclude_dirs == custom_exclude

    def test_init_with_path_object(self, tmp_path):
        """Test initialization with Path object."""
        from pathlib import Path
        builder = DirectoryTreeBuilder(tmp_path, max_depth=2)

        assert builder.base_path == tmp_path
        assert isinstance(builder.base_path, Path)

    def test_default_exclude_dirs(self):
        """Test that default exclude dirs match TreeBuilder."""
        from clickup_framework.commands.map_helpers.mermaid.builders.tree_builder import TreeBuilder

        excluded = DirectoryTreeBuilder._default_exclude_dirs()
        expected = TreeBuilder.DEFAULT_EXCLUDE_DIRS

        assert excluded == expected
        assert '.git' in excluded
        assert '__pycache__' in excluded
        assert 'node_modules' in excluded

    def test_scan_empty_directory(self, tmp_path):
        """Test scanning an empty directory."""
        builder = DirectoryTreeBuilder(str(tmp_path))
        tree = builder.scan()

        assert '__files__' in tree
        assert '__subdirs__' in tree
        assert '__has_code__' in tree
        assert tree['__files__'] == {}
        assert tree['__subdirs__'] == {}
        assert tree['__has_code__'] is False

    def test_scan_with_python_files(self, tmp_path):
        """Test scanning a directory with Python files."""
        # Create test files
        (tmp_path / 'main.py').write_text('def main(): pass')
        (tmp_path / 'utils.py').write_text('def helper(): pass')

        builder = DirectoryTreeBuilder(str(tmp_path))
        tree = builder.scan()

        assert tree['__has_code__'] is True
        assert tree['__files__'] == {}  # Files not populated yet

    def test_scan_with_subdirectories(self, tmp_path):
        """Test scanning nested directories."""
        # Create nested structure
        src_dir = tmp_path / 'src'
        src_dir.mkdir()
        (src_dir / 'app.py').write_text('def run(): pass')

        tests_dir = tmp_path / 'tests'
        tests_dir.mkdir()
        (tests_dir / 'test_app.py').write_text('def test_run(): pass')

        builder = DirectoryTreeBuilder(str(tmp_path))
        tree = builder.scan()

        assert tree['__has_code__'] is True
        assert 'src' in tree['__subdirs__']
        assert 'tests' in tree['__subdirs__']
        assert tree['__subdirs__']['src']['__has_code__'] is True
        assert tree['__subdirs__']['tests']['__has_code__'] is True

    def test_scan_excludes_directories(self, tmp_path):
        """Test that excluded directories are not scanned."""
        # Create excluded directories
        (tmp_path / '.git').mkdir()
        (tmp_path / '.git' / 'config').write_text('gitconfig')

        (tmp_path / '__pycache__').mkdir()
        (tmp_path / '__pycache__' / 'module.pyc').write_text('bytecode')

        # Create included directory
        src_dir = tmp_path / 'src'
        src_dir.mkdir()
        (src_dir / 'app.py').write_text('def main(): pass')

        builder = DirectoryTreeBuilder(str(tmp_path))
        tree = builder.scan()

        assert '.git' not in tree['__subdirs__']
        assert '__pycache__' not in tree['__subdirs__']
        assert 'src' in tree['__subdirs__']

    def test_scan_respects_max_depth(self, tmp_path):
        """Test that scanning respects max_depth parameter."""
        # Create deep nested structure
        current = tmp_path
        for i in range(5):
            current = current / f'level{i}'
            current.mkdir()
            (current / f'file{i}.py').write_text(f'def func{i}(): pass')

        # Scan with max_depth=2
        builder = DirectoryTreeBuilder(str(tmp_path), max_depth=2)
        tree = builder.scan()

        # Should have level0 but not deeper levels
        assert 'level0' in tree['__subdirs__']
        level0 = tree['__subdirs__']['level0']
        assert level0['__has_code__'] is True

        # After max_depth, should stop
        # TreeBuilder stops at max_depth, so we shouldn't see level2 and beyond

    def test_populate_with_functions_root_level(self, tmp_path):
        """Test populating tree with root-level functions."""
        # Create simple file structure
        (tmp_path / 'main.py').write_text('def main(): pass')

        builder = DirectoryTreeBuilder(str(tmp_path))
        tree = builder.scan()

        functions_by_folder = {
            'root': {
                'main.py': {
                    'module_main': ['main', 'init']
                }
            }
        }

        populated = builder.populate_with_functions(tree, functions_by_folder)

        assert 'main.py' in populated['__files__']
        assert 'module_main' in populated['__files__']['main.py']
        assert populated['__files__']['main.py']['module_main'] == ['main', 'init']

    def test_populate_with_functions_nested(self, tmp_path):
        """Test populating tree with nested directory functions."""
        # Create nested structure
        src_dir = tmp_path / 'src'
        src_dir.mkdir()
        (src_dir / 'app.py').write_text('class App: pass')

        builder = DirectoryTreeBuilder(str(tmp_path))
        tree = builder.scan()

        functions_by_folder = {
            'src': {
                'app.py': {
                    'App': ['run', 'stop']
                }
            }
        }

        populated = builder.populate_with_functions(tree, functions_by_folder)

        assert 'src' in populated['__subdirs__']
        assert 'app.py' in populated['__subdirs__']['src']['__files__']
        assert 'App' in populated['__subdirs__']['src']['__files__']['app.py']
        assert populated['__subdirs__']['src']['__files__']['app.py']['App'] == ['run', 'stop']

    def test_populate_with_functions_multiple_classes(self, tmp_path):
        """Test populating with multiple classes in one file."""
        src_dir = tmp_path / 'src'
        src_dir.mkdir()
        (src_dir / 'models.py').write_text('class User: pass\nclass Post: pass')

        builder = DirectoryTreeBuilder(str(tmp_path))
        tree = builder.scan()

        functions_by_folder = {
            'src': {
                'models.py': {
                    'User': ['save', 'delete'],
                    'Post': ['publish', 'archive']
                }
            }
        }

        populated = builder.populate_with_functions(tree, functions_by_folder)

        models_file = populated['__subdirs__']['src']['__files__']['models.py']
        assert 'User' in models_file
        assert 'Post' in models_file
        assert models_file['User'] == ['save', 'delete']
        assert models_file['Post'] == ['publish', 'archive']

    def test_populate_with_missing_directory(self, tmp_path):
        """Test populating when functions reference non-existent directory."""
        builder = DirectoryTreeBuilder(str(tmp_path))
        tree = builder.scan()

        # Reference a directory that doesn't exist in tree
        functions_by_folder = {
            'nonexistent': {
                'phantom.py': {
                    'Phantom': ['disappear']
                }
            }
        }

        populated = builder.populate_with_functions(tree, functions_by_folder)

        # Should not add nonexistent directory
        assert 'nonexistent' not in populated['__subdirs__']
        assert '__files__' in populated
        assert 'phantom.py' not in populated['__files__']

    def test_end_to_end_workflow(self, tmp_path):
        """Test complete workflow: scan + populate."""
        # Create realistic project structure
        src_dir = tmp_path / 'src'
        src_dir.mkdir()
        (src_dir / '__init__.py').write_text('')
        (src_dir / 'main.py').write_text('class Main: pass')

        core_dir = src_dir / 'core'
        core_dir.mkdir()
        (core_dir / 'engine.py').write_text('class Engine: pass')

        tests_dir = tmp_path / 'tests'
        tests_dir.mkdir()
        (tests_dir / 'test_main.py').write_text('def test_main(): pass')

        # Build and populate
        builder = DirectoryTreeBuilder(str(tmp_path), max_depth=5)
        tree = builder.scan()

        functions_by_folder = {
            'src': {
                'main.py': {'Main': ['run', 'init']}
            },
            'src/core': {
                'engine.py': {'Engine': ['start', 'stop']}
            },
            'tests': {
                'test_main.py': {'module_test_main': ['test_main', 'test_init']}
            }
        }

        populated = builder.populate_with_functions(tree, functions_by_folder)

        # Verify structure
        assert 'src' in populated['__subdirs__']
        assert 'tests' in populated['__subdirs__']

        # Verify src files
        src_tree = populated['__subdirs__']['src']
        assert 'main.py' in src_tree['__files__']
        assert src_tree['__files__']['main.py']['Main'] == ['run', 'init']

        # Verify src/core files
        assert 'core' in src_tree['__subdirs__']
        core_tree = src_tree['__subdirs__']['core']
        assert 'engine.py' in core_tree['__files__']
        assert core_tree['__files__']['engine.py']['Engine'] == ['start', 'stop']

        # Verify tests files
        tests_tree = populated['__subdirs__']['tests']
        assert 'test_main.py' in tests_tree['__files__']
        assert tests_tree['__files__']['test_main.py']['module_test_main'] == ['test_main', 'test_init']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
