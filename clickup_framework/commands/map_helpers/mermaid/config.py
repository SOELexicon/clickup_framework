"""
Mermaid Diagram Generator Configuration.

This module centralizes all configuration values used across diagram generators,
making them easy to adjust and override via environment variables.
"""
import os
from dataclasses import dataclass
from typing import Optional


def _get_env_int(key: str, default: int) -> int:
    """Get integer value from environment variable with fallback to default."""
    value = os.environ.get(key)
    if value is not None:
        try:
            return int(value)
        except ValueError:
            return default
    return default


@dataclass
class CodeFlowConfig:
    """Configuration for code flow diagram generation."""

    # Node and depth limits
    max_entry_points: int = 10
    max_nodes: int = 80
    max_collection_depth: int = 8
    tree_depth: int = 3

    # Display limits
    max_functions_per_class: int = 50
    max_folders: int = 20
    max_calls_per_function: int = 5

    @classmethod
    def from_env(cls) -> 'CodeFlowConfig':
        """Create configuration from environment variables."""
        return cls(
            max_entry_points=_get_env_int('MERMAID_CODE_FLOW_MAX_ENTRY_POINTS', 10),
            max_nodes=_get_env_int('MERMAID_CODE_FLOW_MAX_NODES', 80),
            max_collection_depth=_get_env_int('MERMAID_CODE_FLOW_MAX_DEPTH', 8),
            tree_depth=_get_env_int('MERMAID_CODE_FLOW_TREE_DEPTH', 3),
            max_functions_per_class=_get_env_int('MERMAID_CODE_FLOW_MAX_FUNCTIONS_PER_CLASS', 50),
            max_folders=_get_env_int('MERMAID_CODE_FLOW_MAX_FOLDERS', 20),
            max_calls_per_function=_get_env_int('MERMAID_CODE_FLOW_MAX_CALLS_PER_FUNCTION', 5),
        )


@dataclass
class SequenceConfig:
    """Configuration for sequence diagram generation."""

    # Entry point discovery
    max_entry_functions_fallback: int = 3

    # Trace limits
    max_trace_depth_declaration: int = 5
    max_trace_depth_actual: int = 4
    max_calls_per_function: int = 3
    max_participants: int = 10

    @classmethod
    def from_env(cls) -> 'SequenceConfig':
        """Create configuration from environment variables."""
        return cls(
            max_entry_functions_fallback=_get_env_int('MERMAID_SEQUENCE_MAX_ENTRY_FALLBACK', 3),
            max_trace_depth_declaration=_get_env_int('MERMAID_SEQUENCE_MAX_TRACE_DEPTH_DECL', 5),
            max_trace_depth_actual=_get_env_int('MERMAID_SEQUENCE_MAX_TRACE_DEPTH', 4),
            max_calls_per_function=_get_env_int('MERMAID_SEQUENCE_MAX_CALLS_PER_FUNCTION', 3),
            max_participants=_get_env_int('MERMAID_SEQUENCE_MAX_PARTICIPANTS', 10),
        )


@dataclass
class ClassDiagramConfig:
    """Configuration for class diagram generation."""

    # Class and member limits
    max_classes: int = 20
    max_methods_per_class: int = 15
    max_members_per_class: int = 10

    @classmethod
    def from_env(cls) -> 'ClassDiagramConfig':
        """Create configuration from environment variables."""
        return cls(
            max_classes=_get_env_int('MERMAID_CLASS_MAX_CLASSES', 20),
            max_methods_per_class=_get_env_int('MERMAID_CLASS_MAX_METHODS', 15),
            max_members_per_class=_get_env_int('MERMAID_CLASS_MAX_MEMBERS', 10),
        )


@dataclass
class FlowchartConfig:
    """Configuration for flowchart diagram generation."""

    # Structure limits
    max_directories: int = 10
    max_files_per_directory: int = 5
    max_total_files: int = 30

    # Detail thresholds
    class_detail_threshold: int = 5  # Show individual classes if <= this many

    @classmethod
    def from_env(cls) -> 'FlowchartConfig':
        """Create configuration from environment variables."""
        return cls(
            max_directories=_get_env_int('MERMAID_FLOWCHART_MAX_DIRECTORIES', 10),
            max_files_per_directory=_get_env_int('MERMAID_FLOWCHART_MAX_FILES_PER_DIR', 5),
            max_total_files=_get_env_int('MERMAID_FLOWCHART_MAX_TOTAL_FILES', 30),
            class_detail_threshold=_get_env_int('MERMAID_FLOWCHART_CLASS_DETAIL_THRESHOLD', 5),
        )


@dataclass
class MindmapConfig:
    """Configuration for mindmap diagram generation."""

    # Hierarchy limits
    max_languages: int = 5
    max_files_per_language: int = 5

    @classmethod
    def from_env(cls) -> 'MindmapConfig':
        """Create configuration from environment variables."""
        return cls(
            max_languages=_get_env_int('MERMAID_MINDMAP_MAX_LANGUAGES', 5),
            max_files_per_language=_get_env_int('MERMAID_MINDMAP_MAX_FILES_PER_LANG', 5),
        )


@dataclass
class ValidationConfig:
    """Configuration for Mermaid diagram validation."""

    # Validation thresholds
    max_nodes: int = 200
    max_edges: int = 1000
    max_subgraphs: int = 50
    max_text_size: int = 50000

    @classmethod
    def from_env(cls) -> 'ValidationConfig':
        """Create configuration from environment variables."""
        return cls(
            max_nodes=_get_env_int('MERMAID_VALIDATION_MAX_NODES', 200),
            max_edges=_get_env_int('MERMAID_VALIDATION_MAX_EDGES', 1000),
            max_subgraphs=_get_env_int('MERMAID_VALIDATION_MAX_SUBGRAPHS', 50),
            max_text_size=_get_env_int('MERMAID_VALIDATION_MAX_TEXT_SIZE', 50000),
        )


def _get_env_bool(key: str, default: bool) -> bool:
    """Get boolean value from environment variable with fallback to default."""
    value = os.environ.get(key)
    if value is not None:
        return value.lower() in ('true', '1', 'yes', 'on')
    return default


@dataclass
class ProfilingConfig:
    """Configuration for performance profiling."""

    # Profiling settings
    enabled: bool = False  # Disabled by default for production
    print_reports: bool = False  # Print reports to stdout
    save_reports: bool = False  # Save reports to files
    output_dir: str = 'profiling_reports'  # Directory for saved reports

    @classmethod
    def from_env(cls) -> 'ProfilingConfig':
        """Create configuration from environment variables."""
        return cls(
            enabled=_get_env_bool('MERMAID_PROFILING_ENABLED', False),
            print_reports=_get_env_bool('MERMAID_PROFILING_PRINT_REPORTS', False),
            save_reports=_get_env_bool('MERMAID_PROFILING_SAVE_REPORTS', False),
            output_dir=os.environ.get('MERMAID_PROFILING_OUTPUT_DIR', 'profiling_reports'),
        )


class MermaidConfig:
    """
    Central configuration manager for all Mermaid diagram generators.

    Usage:
        # Use default configuration
        config = MermaidConfig()
        max_nodes = config.code_flow.max_nodes

        # Override via environment variables
        # export MERMAID_CODE_FLOW_MAX_NODES=100
        config = MermaidConfig.from_env()

        # Direct instantiation with custom values
        custom_code_flow = CodeFlowConfig(max_nodes=150)
        config = MermaidConfig(code_flow=custom_code_flow)
    """

    def __init__(
        self,
        code_flow: Optional[CodeFlowConfig] = None,
        sequence: Optional[SequenceConfig] = None,
        class_diagram: Optional[ClassDiagramConfig] = None,
        flowchart: Optional[FlowchartConfig] = None,
        mindmap: Optional[MindmapConfig] = None,
        validation: Optional[ValidationConfig] = None,
        profiling: Optional[ProfilingConfig] = None,
    ):
        """Initialize configuration with provided or default configs."""
        self.code_flow = code_flow or CodeFlowConfig()
        self.sequence = sequence or SequenceConfig()
        self.class_diagram = class_diagram or ClassDiagramConfig()
        self.flowchart = flowchart or FlowchartConfig()
        self.mindmap = mindmap or MindmapConfig()
        self.validation = validation or ValidationConfig()
        self.profiling = profiling or ProfilingConfig()

    @classmethod
    def from_env(cls) -> 'MermaidConfig':
        """
        Create configuration from environment variables.

        Environment Variables:
            Code Flow:
                MERMAID_CODE_FLOW_MAX_ENTRY_POINTS (default: 10)
                MERMAID_CODE_FLOW_MAX_NODES (default: 80)
                MERMAID_CODE_FLOW_MAX_DEPTH (default: 8)
                MERMAID_CODE_FLOW_TREE_DEPTH (default: 3)
                MERMAID_CODE_FLOW_MAX_FUNCTIONS_PER_CLASS (default: 50)
                MERMAID_CODE_FLOW_MAX_FOLDERS (default: 20)
                MERMAID_CODE_FLOW_MAX_CALLS_PER_FUNCTION (default: 5)

            Sequence:
                MERMAID_SEQUENCE_MAX_ENTRY_FALLBACK (default: 3)
                MERMAID_SEQUENCE_MAX_TRACE_DEPTH_DECL (default: 5)
                MERMAID_SEQUENCE_MAX_TRACE_DEPTH (default: 4)
                MERMAID_SEQUENCE_MAX_CALLS_PER_FUNCTION (default: 3)
                MERMAID_SEQUENCE_MAX_PARTICIPANTS (default: 10)

            Class Diagram:
                MERMAID_CLASS_MAX_CLASSES (default: 20)
                MERMAID_CLASS_MAX_METHODS (default: 15)
                MERMAID_CLASS_MAX_MEMBERS (default: 10)

            Flowchart:
                MERMAID_FLOWCHART_MAX_DIRECTORIES (default: 10)
                MERMAID_FLOWCHART_MAX_FILES_PER_DIR (default: 5)
                MERMAID_FLOWCHART_MAX_TOTAL_FILES (default: 30)
                MERMAID_FLOWCHART_CLASS_DETAIL_THRESHOLD (default: 5)

            Mindmap:
                MERMAID_MINDMAP_MAX_LANGUAGES (default: 5)
                MERMAID_MINDMAP_MAX_FILES_PER_LANG (default: 5)

            Validation:
                MERMAID_VALIDATION_MAX_NODES (default: 200)
                MERMAID_VALIDATION_MAX_EDGES (default: 1000)
                MERMAID_VALIDATION_MAX_SUBGRAPHS (default: 50)
                MERMAID_VALIDATION_MAX_TEXT_SIZE (default: 50000)

            Profiling:
                MERMAID_PROFILING_ENABLED (default: False)
                MERMAID_PROFILING_PRINT_REPORTS (default: False)
                MERMAID_PROFILING_SAVE_REPORTS (default: False)
                MERMAID_PROFILING_OUTPUT_DIR (default: 'profiling_reports')
        """
        return cls(
            code_flow=CodeFlowConfig.from_env(),
            sequence=SequenceConfig.from_env(),
            class_diagram=ClassDiagramConfig.from_env(),
            flowchart=FlowchartConfig.from_env(),
            mindmap=MindmapConfig.from_env(),
            validation=ValidationConfig.from_env(),
            profiling=ProfilingConfig.from_env(),
        )


# Singleton instance for easy access
_default_config: Optional[MermaidConfig] = None


def get_config() -> MermaidConfig:
    """
    Get the default configuration instance.

    This creates a singleton configuration that respects environment variables.
    The configuration is cached after first access.

    Returns:
        MermaidConfig: The default configuration instance
    """
    global _default_config
    if _default_config is None:
        _default_config = MermaidConfig.from_env()
    return _default_config


def set_config(config: MermaidConfig) -> None:
    """Set the default configuration instance.

    Args:
        config: The configuration to set as default
    """
    global _default_config
    _default_config = config


def reset_config() -> None:
    """Reset the default configuration (useful for testing)."""
    global _default_config
    _default_config = None
