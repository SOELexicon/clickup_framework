"""Pipeline configuration parser for batch diagram generation.

This module handles parsing and validation of YAML configuration files
for batch diagram generation pipelines.

Configuration Format:
    version: 1
    output_dir: docs/diagrams

    generators:
      - name: project-overview
        type: flowchart
        source: clickup_framework/
        output: overview.mmd
        options:
          max_depth: 2
          exclude: [tests/, __pycache__/]

      - name: api-architecture
        type: class
        source: clickup_framework/api/
        output: api-classes.mmd
        options:
          show_methods: true
          show_properties: true
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


class PipelineConfig:
    """Configuration for batch diagram generation pipeline."""

    SUPPORTED_VERSION = 1
    SUPPORTED_DIAGRAM_TYPES = ['flowchart', 'swim', 'class', 'pie', 'mindmap', 'sequence', 'flow']

    def __init__(self, config_file: str):
        """Initialize pipeline configuration.

        Args:
            config_file: Path to YAML configuration file

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If configuration is invalid
        """
        self.config_file = Path(config_file)
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        self.config_data = self._load_config()
        self._validate_config()

        # Extract configuration sections
        self.version = self.config_data.get('version', 1)
        self.output_dir = Path(self.config_data.get('output_dir', 'docs/diagrams'))
        self.generators = self.config_data.get('generators', [])
        self.global_options = self.config_data.get('options', {})

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file.

        Returns:
            Parsed configuration dictionary

        Raises:
            ValueError: If YAML parsing fails
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {self.config_file}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to read {self.config_file}: {e}")

    def _validate_config(self) -> None:
        """Validate configuration structure and values.

        Raises:
            ValueError: If configuration is invalid
        """
        # Check version
        version = self.config_data.get('version')
        if version != self.SUPPORTED_VERSION:
            raise ValueError(
                f"Unsupported configuration version: {version}. "
                f"Expected version {self.SUPPORTED_VERSION}"
            )

        # Check generators exist
        generators = self.config_data.get('generators')
        if not generators:
            raise ValueError("Configuration must contain at least one generator")

        if not isinstance(generators, list):
            raise ValueError("'generators' must be a list")

        # Validate each generator
        for idx, generator in enumerate(generators):
            self._validate_generator(generator, idx)

    def _validate_generator(self, generator: Dict[str, Any], index: int) -> None:
        """Validate individual generator configuration.

        Args:
            generator: Generator configuration dictionary
            index: Generator index in list (for error messages)

        Raises:
            ValueError: If generator configuration is invalid
        """
        if not isinstance(generator, dict):
            raise ValueError(f"Generator #{index} must be a dictionary")

        # Check required fields
        required_fields = ['name', 'type', 'source', 'output']
        for field in required_fields:
            if field not in generator:
                raise ValueError(
                    f"Generator #{index} missing required field: {field}"
                )

        # Validate name
        name = generator['name']
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Generator #{index} 'name' must be non-empty string")

        # Validate diagram type
        diagram_type = generator['type']
        if diagram_type not in self.SUPPORTED_DIAGRAM_TYPES:
            raise ValueError(
                f"Generator '{name}' has unsupported type '{diagram_type}'. "
                f"Supported types: {', '.join(self.SUPPORTED_DIAGRAM_TYPES)}"
            )

        # Validate source path
        source = generator['source']
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"Generator '{name}' 'source' must be non-empty string")

        # Validate output path
        output = generator['output']
        if not isinstance(output, str) or not output.strip():
            raise ValueError(f"Generator '{name}' 'output' must be non-empty string")

        # Validate options if present
        options = generator.get('options', {})
        if not isinstance(options, dict):
            raise ValueError(f"Generator '{name}' 'options' must be a dictionary")

    def get_generators(self) -> List[Dict[str, Any]]:
        """Get list of generator configurations.

        Returns:
            List of generator configuration dictionaries
        """
        return self.generators

    def get_output_dir(self) -> Path:
        """Get output directory path.

        Returns:
            Output directory as Path object
        """
        return self.output_dir

    def get_global_options(self) -> Dict[str, Any]:
        """Get global options that apply to all generators.

        Returns:
            Global options dictionary
        """
        return self.global_options

    def get_generator_options(self, generator: Dict[str, Any]) -> Dict[str, Any]:
        """Get merged options for a specific generator.

        Merges global options with generator-specific options.
        Generator-specific options override global options.

        Args:
            generator: Generator configuration dictionary

        Returns:
            Merged options dictionary
        """
        merged_options = self.global_options.copy()
        generator_options = generator.get('options', {})
        merged_options.update(generator_options)
        return merged_options

    @staticmethod
    def create_example_config(output_file: str = '.diagram-pipeline.yaml') -> None:
        """Create an example configuration file.

        Args:
            output_file: Path to output configuration file
        """
        example_config = """# Diagram Pipeline Configuration
# Version 1 format

version: 1

# Output directory for all generated diagrams
output_dir: docs/diagrams

# Global options (applied to all generators unless overridden)
options:
  theme: dark
  # ignore_gitignore: false

# List of diagram generators to run
generators:
  # Project overview flowchart
  - name: project-overview
    type: flowchart
    source: clickup_framework/
    output: overview.md
    options:
      max_depth: 2
      exclude:
        - tests/
        - __pycache__/
        - "*.pyc"

  # API architecture class diagram
  - name: api-classes
    type: class
    source: clickup_framework/api/
    output: api-classes.md
    options:
      show_methods: true
      show_properties: true

  # Language distribution pie chart
  - name: language-stats
    type: pie
    source: ./
    output: languages.md

  # Code execution flow
  - name: execution-flow
    type: flow
    source: clickup_framework/
    output: execution.md
    options:
      theme: light
      max_depth: 3

  # Sequence diagram
  - name: api-sequence
    type: sequence
    source: clickup_framework/api/
    output: api-sequence.md

  # Project mindmap
  - name: project-mindmap
    type: mindmap
    source: ./
    output: mindmap.md
"""

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(example_config)
            print(f"[SUCCESS] Example configuration created: {output_file}")
        except Exception as e:
            print(f"[ERROR] Failed to create example configuration: {e}", file=sys.stderr)
            sys.exit(1)
