# Adding New Generators

This guide shows you how to create custom Mermaid diagram generators by extending the `BaseGenerator` class.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Step-by-Step Guide](#step-by-step-guide)
- [Example: Timeline Generator](#example-timeline-generator)
- [Testing Your Generator](#testing-your-generator)
- [Best Practices](#best-practices)
- [Integration](#integration)
- [Advanced Topics](#advanced-topics)

## Overview

All diagram generators inherit from `BaseGenerator` and follow the **Template Method** design pattern. You implement two abstract methods:

1. `validate_inputs(**kwargs)` - Validate required statistics data
2. `generate_body(**kwargs)` - Generate the diagram content

The base class handles:
- File I/O
- Header/footer generation
- Mermaid syntax validation
- Error handling
- Theme management
- Metadata export

## Prerequisites

**Required knowledge:**
- Python classes and inheritance
- Abstract methods
- Mermaid diagram syntax
- The statistics dictionary format from `parse_tags_file()`

**Recommended reading:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [GENERATORS.md](GENERATORS.md) - API reference
- [Mermaid documentation](https://mermaid.js.org/)

## Step-by-Step Guide

### Step 1: Choose Your Diagram Type

First, identify which Mermaid diagram type suits your use case:

- **Timeline**: Show events chronologically
- **Gantt**: Display project schedules
- **Git Graph**: Visualize git history
- **Entity-Relationship**: Database schemas
- **State Diagram**: State machines
- **User Journey**: User workflows

See [Mermaid diagram types](https://mermaid.js.org/intro/syntax-reference.html) for more options.

### Step 2: Create Generator File

Create a new file in `clickup_framework/commands/map_helpers/mermaid/generators/`:

```bash
# Example: timeline_generator.py
clickup_framework/commands/map_helpers/mermaid/generators/timeline_generator.py
```

### Step 3: Implement Generator Class

```python
"""Timeline diagram generator for showing code evolution over time."""

from typing import Dict
from .base_generator import BaseGenerator
from ..exceptions import DataValidationError


class TimelineGenerator(BaseGenerator):
    """Generate timeline diagrams showing code milestones and changes."""

    def validate_inputs(self, **kwargs) -> None:
        """Validate timeline-specific inputs.

        Required stats keys:
            - milestones: List of milestone events with timestamps

        Raises:
            DataValidationError: If required data is missing
        """
        milestones = self.stats.get('milestones', [])
        if not milestones:
            raise DataValidationError.missing_required_field(
                field_name='milestones',
                generator_type='timeline',
                stats_keys=list(self.stats.keys())
            )

        # Additional validation
        if not all('timestamp' in m and 'event' in m for m in milestones):
            raise DataValidationError(
                "Each milestone must have 'timestamp' and 'event' fields",
                generator_type='timeline',
                stats_keys=list(self.stats.keys())
            )

    def generate_body(self, **kwargs) -> None:
        """Generate timeline diagram body.

        Args:
            **kwargs: Additional generation parameters
        """
        milestones = self.stats.get('milestones', [])

        # Add diagram declaration
        self._add_diagram_declaration("timeline")
        self._add_line("    title Code Evolution Timeline")

        # Sort milestones chronologically
        sorted_milestones = sorted(milestones, key=lambda m: m['timestamp'])

        # Group by year
        current_year = None
        for milestone in sorted_milestones:
            year = milestone['timestamp'][:4]  # Extract year from ISO timestamp

            # Add year section if changed
            if year != current_year:
                self._add_line(f"    section {year}")
                current_year = year

            # Add milestone event
            event = milestone['event']
            date = milestone['timestamp'][5:10]  # MM-DD
            self._add_line(f"        {date} : {event}")

            # Store metadata
            node_id = f"milestone_{milestone['timestamp']}"
            self.metadata_store.add_node(node_id, {
                'timestamp': milestone['timestamp'],
                'event': event,
                'type': 'milestone'
            })
```

### Step 4: Export from Module

Add your generator to `clickup_framework/commands/map_helpers/mermaid/generators/__init__.py`:

```python
from .base_generator import BaseGenerator
from .flowchart_generator import FlowchartGenerator
from .class_diagram_generator import ClassDiagramGenerator
from .pie_chart_generator import PieChartGenerator
from .mindmap_generator import MindmapGenerator
from .sequence_generator import SequenceGenerator
from .code_flow_generator import CodeFlowGenerator
from .timeline_generator import TimelineGenerator  # Add this

__all__ = [
    'BaseGenerator',
    'FlowchartGenerator',
    'ClassDiagramGenerator',
    'PieChartGenerator',
    'MindmapGenerator',
    'SequenceGenerator',
    'CodeFlowGenerator',
    'TimelineGenerator',  # Add this
]
```

### Step 5: Create Wrapper Function (Optional)

For backward compatibility, add a wrapper to `mermaid_generators.py`:

```python
from .mermaid.generators import TimelineGenerator

def generate_mermaid_timeline(stats: Dict, output_file: str, theme: str = 'dark') -> None:
    """Generate a timeline diagram showing code evolution.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
        theme: Color theme ('dark' or 'light')
    """
    generator = TimelineGenerator(stats, output_file, theme)
    generator.generate()
```

## Example: Timeline Generator

Here's a complete working example:

### File: `timeline_generator.py`

```python
"""Timeline diagram generator for code evolution visualization."""

from typing import Dict, List
from datetime import datetime
from .base_generator import BaseGenerator
from ..exceptions import DataValidationError


class TimelineGenerator(BaseGenerator):
    """Generate timeline diagrams showing code milestones over time.

    The timeline generator visualizes major code events chronologically,
    grouped by time period (year/month). Useful for showing:
    - Feature release history
    - Bug fix timeline
    - Refactoring milestones
    - Architecture changes
    """

    def validate_inputs(self, **kwargs) -> None:
        """Validate timeline-specific inputs.

        Required stats keys:
            - milestones: List[Dict] with 'timestamp' and 'event' keys

        Raises:
            DataValidationError: If required data is missing or invalid
        """
        milestones = self.stats.get('milestones', [])

        if not milestones:
            raise DataValidationError.missing_required_field(
                field_name='milestones',
                generator_type='timeline',
                stats_keys=list(self.stats.keys())
            )

        # Validate milestone structure
        for i, milestone in enumerate(milestones):
            if 'timestamp' not in milestone:
                raise DataValidationError(
                    f"Milestone {i} missing 'timestamp' field",
                    generator_type='timeline',
                    stats_keys=list(self.stats.keys())
                )
            if 'event' not in milestone:
                raise DataValidationError(
                    f"Milestone {i} missing 'event' field",
                    generator_type='timeline',
                    stats_keys=list(self.stats.keys())
                )

            # Validate timestamp format (ISO 8601)
            try:
                datetime.fromisoformat(milestone['timestamp'])
            except ValueError:
                raise DataValidationError(
                    f"Invalid timestamp format in milestone {i}: {milestone['timestamp']}",
                    generator_type='timeline',
                    stats_keys=list(self.stats.keys())
                )

    def generate_body(self, **kwargs) -> None:
        """Generate timeline diagram body.

        Groups milestones by year and displays chronologically.

        Args:
            **kwargs: Additional parameters (currently unused)
        """
        milestones = self.stats.get('milestones', [])

        # Add diagram declaration
        self._add_diagram_declaration("timeline")
        self._add_line("    title Code Evolution Timeline")

        # Sort chronologically
        sorted_milestones = sorted(milestones, key=lambda m: m['timestamp'])

        # Group by year
        milestones_by_year = self._group_by_year(sorted_milestones)

        # Generate timeline sections
        for year, year_milestones in sorted(milestones_by_year.items()):
            self._add_line(f"    section {year}")

            for milestone in year_milestones:
                # Format: MM-DD : Event description
                date = milestone['timestamp'][5:10]  # Extract MM-DD
                event = self._escape_mermaid_text(milestone['event'])
                self._add_line(f"        {date} : {event}")

                # Store metadata
                self._store_milestone_metadata(milestone)

    def _group_by_year(self, milestones: List[Dict]) -> Dict[str, List[Dict]]:
        """Group milestones by year.

        Args:
            milestones: List of milestone dictionaries

        Returns:
            Dict mapping year strings to milestone lists
        """
        by_year = {}
        for milestone in milestones:
            year = milestone['timestamp'][:4]
            if year not in by_year:
                by_year[year] = []
            by_year[year].append(milestone)
        return by_year

    def _escape_mermaid_text(self, text: str) -> str:
        """Escape special characters for mermaid syntax.

        Args:
            text: Raw text string

        Returns:
            Escaped text safe for mermaid diagrams
        """
        # Replace problematic characters
        replacements = {
            '"': '\\"',
            '[': '\\[',
            ']': '\\]',
            '(': '\\(',
            ')': '\\)',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def _store_milestone_metadata(self, milestone: Dict) -> None:
        """Store milestone metadata for export.

        Args:
            milestone: Milestone dictionary
        """
        node_id = f"milestone_{milestone['timestamp']}"
        metadata = {
            'timestamp': milestone['timestamp'],
            'event': milestone['event'],
            'type': 'milestone'
        }

        # Add optional fields if present
        for field in ['category', 'author', 'description']:
            if field in milestone:
                metadata[field] = milestone[field]

        self.metadata_store.add_node(node_id, metadata)

    def _get_diagram_title(self) -> str:
        """Generate custom title for timeline diagram.

        Returns:
            Diagram title string
        """
        total_milestones = len(self.stats.get('milestones', []))
        return f"Timeline Diagram ({total_milestones} milestones)"
```

### Usage

```python
from clickup_framework.commands.map_helpers.mermaid.generators import TimelineGenerator

stats = {
    'milestones': [
        {
            'timestamp': '2024-01-15T10:00:00',
            'event': 'Initial commit',
            'category': 'setup'
        },
        {
            'timestamp': '2024-03-20T14:30:00',
            'event': 'Feature: User authentication',
            'category': 'feature'
        },
        {
            'timestamp': '2024-06-10T09:15:00',
            'event': 'Refactor: Modularize generators',
            'category': 'refactor'
        }
    ]
}

generator = TimelineGenerator(stats, 'timeline.md', theme='dark')
output = generator.generate()
print(f"Generated: {output}")
```

## Testing Your Generator

### Unit Tests

Create comprehensive unit tests in `tests/commands/map_helpers/test_timeline_generator.py`:

```python
"""Tests for TimelineGenerator."""

import pytest
import tempfile
import os
from pathlib import Path
from clickup_framework.commands.map_helpers.mermaid.exceptions import DataValidationError
from clickup_framework.commands.map_helpers.mermaid.generators.timeline_generator import TimelineGenerator


@pytest.fixture
def sample_stats():
    """Sample statistics with milestones."""
    return {
        'milestones': [
            {'timestamp': '2024-01-15T10:00:00', 'event': 'Initial commit'},
            {'timestamp': '2024-03-20T14:30:00', 'event': 'Feature added'},
            {'timestamp': '2024-06-10T09:15:00', 'event': 'Refactoring'}
        ]
    }


@pytest.fixture
def temp_output_file():
    """Temporary output file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.remove(temp_path)
    metadata_file = str(Path(temp_path).with_suffix('')) + '_metadata.json'
    if os.path.exists(metadata_file):
        os.remove(metadata_file)


class TestTimelineValidation:
    """Test timeline validation."""

    def test_validate_passes_with_valid_data(self, sample_stats, temp_output_file):
        """Test validation passes with valid milestones."""
        generator = TimelineGenerator(sample_stats, temp_output_file)
        generator.validate_inputs()  # Should not raise

    def test_validate_fails_without_milestones(self, temp_output_file):
        """Test validation fails when milestones missing."""
        stats = {'other_data': 'value'}
        generator = TimelineGenerator(stats, temp_output_file)

        with pytest.raises(DataValidationError, match="milestones"):
            generator.validate_inputs()

    def test_validate_fails_with_invalid_timestamp(self, temp_output_file):
        """Test validation fails with malformed timestamp."""
        stats = {
            'milestones': [
                {'timestamp': 'invalid-date', 'event': 'Test'}
            ]
        }
        generator = TimelineGenerator(stats, temp_output_file)

        with pytest.raises(DataValidationError, match="Invalid timestamp"):
            generator.validate_inputs()


class TestTimelineGeneration:
    """Test timeline diagram generation."""

    def test_generate_creates_valid_diagram(self, sample_stats, temp_output_file):
        """Test full generation creates valid output."""
        generator = TimelineGenerator(sample_stats, temp_output_file)

        result = generator.generate()

        assert os.path.exists(result)
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()

        assert '```mermaid' in content
        assert 'timeline' in content
        assert '2024' in content
        assert 'Initial commit' in content
        assert '```' in content

    def test_generate_groups_by_year(self, temp_output_file):
        """Test milestones grouped by year."""
        stats = {
            'milestones': [
                {'timestamp': '2023-06-15T10:00:00', 'event': 'Event 2023'},
                {'timestamp': '2024-03-20T14:30:00', 'event': 'Event 2024'}
            ]
        }
        generator = TimelineGenerator(stats, temp_output_file)

        generator.generate()

        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'section 2023' in content
        assert 'section 2024' in content
```

### Integration Tests

Test with real data from your codebase:

```python
def test_timeline_with_real_git_history():
    """Test timeline generation with actual git data."""
    # Parse git log into milestones
    stats = parse_git_log_to_stats('path/to/repo')

    generator = TimelineGenerator(stats, 'output/git_timeline.md')
    output = generator.generate()

    assert os.path.exists(output)
```

## Best Practices

### 1. Input Validation

Always validate required data thoroughly:

```python
def validate_inputs(self, **kwargs) -> None:
    """Validate all required inputs."""
    # Check required keys exist
    required_keys = ['milestones', 'metadata']
    for key in required_keys:
        if key not in self.stats:
            raise DataValidationError.missing_required_field(
                field_name=key,
                generator_type='timeline',
                stats_keys=list(self.stats.keys())
            )

    # Validate data structure
    if not isinstance(self.stats['milestones'], list):
        raise DataValidationError(
            "'milestones' must be a list",
            generator_type='timeline',
            stats_keys=list(self.stats.keys())
        )

    # Validate individual items
    for item in self.stats['milestones']:
        self._validate_milestone(item)
```

### 2. Error Messages

Provide helpful, actionable error messages:

```python
# Bad
raise ValueError("Invalid data")

# Good
raise DataValidationError(
    f"Timeline requires at least 2 milestones, found {len(milestones)}. "
    f"Available stats keys: {', '.join(self.stats.keys())}",
    generator_type='timeline',
    stats_keys=list(self.stats.keys())
)
```

### 3. Metadata Export

Store meaningful metadata for advanced use cases:

```python
def generate_body(self, **kwargs) -> None:
    """Generate with metadata tracking."""
    for node in nodes:
        # Add node to diagram
        self._add_line(f"    {node['id']}")

        # Store metadata
        self.metadata_store.add_node(node['id'], {
            'label': node['name'],
            'type': node['type'],
            'source_file': node.get('file'),
            'line_number': node.get('line'),
            # Custom fields specific to your generator
            'custom_field': node.get('custom')
        })
```

### 4. Text Escaping

Escape special characters in user data:

```python
def _escape_text(self, text: str) -> str:
    """Escape mermaid special characters."""
    replacements = {
        '"': '\\"',
        '[': '\\[',
        ']': '\\]',
        '(': '\\(',
        ')': '\\)',
        '{': '\\{',
        '}': '\\}',
        '|': '\\|',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text
```

### 5. Limits and Performance

Set reasonable limits to prevent runaway generation:

```python
def generate_body(self, **kwargs) -> None:
    """Generate with limits."""
    MAX_NODES = 100
    MAX_DEPTH = 5

    nodes = self.stats.get('nodes', [])

    if len(nodes) > MAX_NODES:
        print(f"Warning: Limiting to {MAX_NODES} nodes (found {len(nodes)})")
        nodes = nodes[:MAX_NODES]

    # Process with depth limit
    self._process_nodes(nodes, max_depth=MAX_DEPTH)
```

### 6. Theme Support

Use the theme system for consistent styling:

```python
def generate_body(self, **kwargs) -> None:
    """Generate with theme-aware styling."""
    # Get colors from theme
    node_color = self.theme_manager.get_color('function')
    edge_color = self.theme_manager.get_color('default')

    # Apply to diagram
    self._add_line(f"    classDef nodeStyle fill:{node_color}")
```

## Integration

### Add CLI Support

Integrate with the map command in `clickup_framework/cli.py`:

```python
# Add timeline option to mermaid type choices
@click.option('--mer', type=click.Choice([
    'pie', 'class', 'flowchart', 'mindmap', 'sequence', 'code_flow', 'timeline'
]))
def map_command(...):
    if mermaid_type == 'timeline':
        from clickup_framework.commands.map_helpers.mermaid.generators import TimelineGenerator
        generator = TimelineGenerator(stats, output, theme)
        generator.generate()
```

### Register with Factory (Optional)

If you have a generator factory pattern:

```python
# In generator_factory.py
GENERATOR_REGISTRY = {
    'flowchart': FlowchartGenerator,
    'class': ClassDiagramGenerator,
    'pie': PieChartGenerator,
    'timeline': TimelineGenerator,  # Add this
}
```

## Advanced Topics

### Custom Header/Footer

Override header or footer methods:

```python
class TimelineGenerator(BaseGenerator):
    def _get_diagram_title(self) -> str:
        """Custom title with milestone count."""
        count = len(self.stats.get('milestones', []))
        return f"Project Timeline ({count} events)"

    def _add_footer(self) -> None:
        """Add custom footer with timeline summary."""
        super()._add_footer()

        self._add_line("\n## Timeline Summary")
        milestones = self.stats.get('milestones', [])
        first_date = milestones[0]['timestamp'][:10]
        last_date = milestones[-1]['timestamp'][:10]
        self._add_line(f"- **Period**: {first_date} to {last_date}")
        self._add_line(f"- **Total Events**: {len(milestones)}")
```

### Dynamic Configuration

Support runtime configuration:

```python
class TimelineGenerator(BaseGenerator):
    def __init__(self, stats, output_file, theme='dark', metadata_store=None,
                 group_by='year'):
        super().__init__(stats, output_file, theme, metadata_store)
        self.group_by = group_by  # 'year' or 'month'

    def generate_body(self, **kwargs) -> None:
        if self.group_by == 'year':
            self._generate_yearly_timeline()
        elif self.group_by == 'month':
            self._generate_monthly_timeline()
```

### Builder Pattern

Use builders for complex structures:

```python
from ..core.tree_builder import TreeBuilder

class TimelineGenerator(BaseGenerator):
    def generate_body(self, **kwargs) -> None:
        builder = TreeBuilder()
        builder.set_root('timeline_root')

        for milestone in self.stats['milestones']:
            builder.add_child(
                node_id=milestone['id'],
                parent='timeline_root',
                data={'event': milestone['event']}
            )

        timeline_tree = builder.build()
        self._render_tree(timeline_tree)
```

## Checklist

Before submitting your new generator:

- [ ] Inherits from `BaseGenerator`
- [ ] Implements `validate_inputs()`
- [ ] Implements `generate_body()`
- [ ] Escapes special characters in user data
- [ ] Sets reasonable limits (nodes, depth, etc.)
- [ ] Stores metadata when appropriate
- [ ] Has comprehensive unit tests (80%+ coverage)
- [ ] Includes docstrings with examples
- [ ] Exported from `generators/__init__.py`
- [ ] Has wrapper function in `mermaid_generators.py` (optional)
- [ ] Integrated with CLI (optional)
- [ ] Documentation added to this guide
- [ ] Tested with real-world data

## See Also

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture and design patterns
- **[GENERATORS.md](GENERATORS.md)**: Complete API reference
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)**: Migration from legacy API
- **[BaseGenerator source](../../../clickup_framework/commands/map_helpers/mermaid/generators/base_generator.py)**: Template method implementation
- **[Mermaid Documentation](https://mermaid.js.org/)**: Mermaid syntax reference
