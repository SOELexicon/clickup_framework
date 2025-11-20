"""Tests for ClassDiagramGenerator.

This module tests the class diagram generator functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from clickup_framework.commands.map_helpers.mermaid.generators.class_diagram_generator import ClassDiagramGenerator


@pytest.fixture
def sample_stats():
    """Sample statistics dictionary with symbols_by_file data."""
    return {
        'total_symbols': 30,
        'files_analyzed': 2,
        'symbols_by_file': {
            '/project/models.py': [
                {'name': 'BaseModel', 'kind': 'class', 'line': 10},
                {'name': '__init__', 'kind': 'method', 'scope': 'BaseModel'},
                {'name': 'save', 'kind': 'method', 'scope': 'BaseModel'},
                {'name': 'User', 'kind': 'class', 'line': 30},
                {'name': 'username', 'kind': 'member', 'scope': 'User'},
                {'name': '__init__', 'kind': 'method', 'scope': 'User'},
                {'name': '_validate', 'kind': 'method', 'scope': 'User'},
                {'name': 'login', 'kind': 'method', 'scope': 'User'}
            ],
            '/project/utils.py': [
                {'name': 'Helper', 'kind': 'class', 'line': 5},
                {'name': 'process', 'kind': 'method', 'scope': 'Helper'}
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


class TestClassDiagramValidation:
    """Test class diagram validation."""

    def test_validate_inputs_passes_with_valid_data(self, sample_stats, temp_output_file):
        """Test validation passes when symbols_by_file data exists."""
        generator = ClassDiagramGenerator(sample_stats, temp_output_file)

        # Should not raise any exceptions
        generator.validate_inputs()

    def test_validate_inputs_fails_without_symbols_by_file(self, temp_output_file):
        """Test validation fails when symbols_by_file is missing."""
        stats_without_symbols = {
            'total_symbols': 10,
            'files_analyzed': 1
        }
        generator = ClassDiagramGenerator(stats_without_symbols, temp_output_file)

        with pytest.raises(ValueError, match="No symbols_by_file data found in stats"):
            generator.validate_inputs()

    def test_validate_inputs_fails_with_empty_symbols_by_file(self, temp_output_file):
        """Test validation fails when symbols_by_file is empty."""
        stats_empty = {
            'total_symbols': 0,
            'symbols_by_file': {}
        }
        generator = ClassDiagramGenerator(stats_empty, temp_output_file)

        with pytest.raises(ValueError, match="No symbols_by_file data found in stats"):
            generator.validate_inputs()


class TestClassDiagramBodyGeneration:
    """Test class diagram body generation."""

    def test_generate_body_adds_class_diagram_declaration(self, sample_stats, temp_output_file):
        """Test generate_body adds classDiagram declaration."""
        generator = ClassDiagramGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        assert len(generator.lines) > 0
        assert generator.lines[0] == "classDiagram"

    def test_generate_body_extracts_classes(self, sample_stats, temp_output_file):
        """Test generate_body extracts class declarations."""
        generator = ClassDiagramGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        assert 'class BaseModel' in lines_str
        assert 'class User' in lines_str
        assert 'class Helper' in lines_str

    def test_generate_body_adds_file_stereotypes(self, sample_stats, temp_output_file):
        """Test generate_body adds file name as stereotype."""
        generator = ClassDiagramGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should show <<filename>> stereotype
        assert '<<models.py>>' in lines_str
        assert '<<utils.py>>' in lines_str

    def test_generate_body_adds_methods(self, sample_stats, temp_output_file):
        """Test generate_body adds methods to classes."""
        generator = ClassDiagramGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should have methods listed
        assert 'save()' in lines_str
        assert 'login()' in lines_str
        assert 'process()' in lines_str

    def test_generate_body_adds_members(self, sample_stats, temp_output_file):
        """Test generate_body adds member variables to classes."""
        generator = ClassDiagramGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should have members listed with - prefix
        assert '-username' in lines_str

    def test_generate_body_uses_visibility_markers(self, sample_stats, temp_output_file):
        """Test generate_body assigns correct visibility markers."""
        generator = ClassDiagramGenerator(sample_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Private methods (__ or _) should have -
        assert '-__init__()' in lines_str or '__init__()' in lines_str  # Could be either
        assert '-_validate()' in lines_str
        # Public methods should have +
        assert '+save()' in lines_str
        assert '+login()' in lines_str

    def test_generate_body_limits_total_classes(self, temp_output_file):
        """Test generate_body limits to 20 classes."""
        many_classes = {
            'total_symbols': 250,
            'symbols_by_file': {
                f'/file{i}.py': [{'name': f'Class{i}', 'kind': 'class'}]
                for i in range(30)
            }
        }
        generator = ClassDiagramGenerator(many_classes, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Count class declarations
        class_count = lines_str.count('class Class')
        assert class_count <= 20

    def test_generate_body_limits_methods_per_class(self, temp_output_file):
        """Test generate_body limits methods to 15 per class."""
        many_methods = {
            'total_symbols': 100,
            'symbols_by_file': {
                '/big_class.py': [
                    {'name': 'BigClass', 'kind': 'class'}
                ] + [
                    {'name': f'method{i}', 'kind': 'method', 'scope': 'BigClass'}
                    for i in range(20)
                ]
            }
        }
        generator = ClassDiagramGenerator(many_methods, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should have at most 15 methods
        method_count = sum(1 for line in generator.lines if 'method' in line and '()' in line)
        assert method_count <= 15

    def test_generate_body_limits_members_per_class(self, temp_output_file):
        """Test generate_body limits members to 10 per class."""
        many_members = {
            'total_symbols': 100,
            'symbols_by_file': {
                '/member_class.py': [
                    {'name': 'MemberClass', 'kind': 'class'}
                ] + [
                    {'name': f'member{i}', 'kind': 'member', 'scope': 'MemberClass'}
                    for i in range(15)
                ]
            }
        }
        generator = ClassDiagramGenerator(many_members, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should have at most 10 members
        member_count = sum(1 for line in generator.lines if line.strip().startswith('-member'))
        assert member_count <= 10

    def test_generate_body_avoids_duplicate_classes(self, temp_output_file):
        """Test generate_body skips duplicate class names."""
        duplicate_stats = {
            'total_symbols': 20,
            'symbols_by_file': {
                '/file1.py': [{'name': 'Duplicate', 'kind': 'class'}],
                '/file2.py': [{'name': 'Duplicate', 'kind': 'class'}]
            }
        }
        generator = ClassDiagramGenerator(duplicate_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should only appear once
        assert lines_str.count('class Duplicate') == 1

    def test_generate_body_infers_inheritance(self, temp_output_file):
        """Test generate_body infers inheritance from Base prefix."""
        inheritance_stats = {
            'total_symbols': 10,
            'symbols_by_file': {
                '/models.py': [
                    {'name': 'BaseEntity', 'kind': 'class'},
                    {'name': 'Entity', 'kind': 'class'}
                ]
            }
        }
        generator = ClassDiagramGenerator(inheritance_stats, temp_output_file)

        generator.generate_body()

        lines_str = '\n'.join(generator.lines)
        # Should create inheritance relationship
        assert '<|--' in lines_str
        assert 'BaseEntity <|-- Entity' in lines_str


class TestClassDiagramEndToEnd:
    """Test complete end-to-end class diagram generation."""

    def test_full_generation_creates_valid_diagram(self, sample_stats, temp_output_file):
        """Test complete generation workflow produces valid class diagram."""
        generator = ClassDiagramGenerator(sample_stats, temp_output_file)

        result_path = generator.generate()

        assert result_path == temp_output_file
        assert os.path.exists(temp_output_file)

        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify structure
        assert "```mermaid" in content
        assert "classDiagram" in content
        assert "class " in content
        assert "<<" in content  # File stereotypes
        assert "```" in content
        assert "## Statistics" in content


class TestClassDiagramEdgeCases:
    """Test edge cases specific to class diagram generation."""

    def test_generate_with_no_classes(self, temp_output_file):
        """Test generation with no class symbols."""
        no_classes = {
            'total_symbols': 5,
            'symbols_by_file': {
                '/functions.py': [
                    {'name': 'func1', 'kind': 'function'},
                    {'name': 'func2', 'kind': 'function'}
                ]
            }
        }
        generator = ClassDiagramGenerator(no_classes, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should still have classDiagram declaration but no classes
        assert "classDiagram" in content
        assert content.count("class ") <= 1  # Just the declaration, no actual classes

    def test_generate_with_class_without_methods_or_members(self, temp_output_file):
        """Test generation with classes that have no methods or members."""
        empty_class = {
            'total_symbols': 1,
            'symbols_by_file': {
                '/empty.py': [
                    {'name': 'EmptyClass', 'kind': 'class'}
                ]
            }
        }
        generator = ClassDiagramGenerator(empty_class, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "class EmptyClass" in content
        assert "<<empty.py>>" in content

    def test_generate_with_methods_without_scope(self, temp_output_file):
        """Test generation handles methods without scope field."""
        no_scope = {
            'total_symbols': 5,
            'symbols_by_file': {
                '/unscoped.py': [
                    {'name': 'MyClass', 'kind': 'class'},
                    {'name': 'method1', 'kind': 'method'}  # No scope
                ]
            }
        }
        generator = ClassDiagramGenerator(no_scope, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        # Should not crash, methods without scope won't be associated with classes
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "class MyClass" in content
