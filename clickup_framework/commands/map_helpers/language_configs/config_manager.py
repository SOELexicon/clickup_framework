"""
Language Configuration Manager

Loads and applies language-specific configurations for code mapping and visualization.
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Relationship:
    """Represents a code relationship (inheritance, composition, etc.)"""
    type: str  # inheritance, interface, composition, dependency
    source: str  # Source class/module
    target: str  # Target class/module
    label: str  # Human-readable label
    style: Dict[str, Any]  # Visualization style
    line_number: Optional[int] = None
    extra_info: Optional[Dict[str, Any]] = None


class LanguageConfig:
    """Configuration for a specific programming language."""

    def __init__(self, config_data: Dict[str, Any]):
        self.data = config_data
        self.name = config_data['language']['name']
        self.extensions = config_data['language']['extensions']
        self.paradigm = config_data['language'].get('paradigm', 'procedural')

    def get_relationship_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get all relationship extraction patterns."""
        return self.data.get('relationships', {})

    def extract_relationships(self, source_code: str, file_path: str) -> List[Relationship]:
        """
        Extract relationships from source code using configured patterns.

        Args:
            source_code: Source code content
            file_path: Path to source file

        Returns:
            List of detected relationships
        """
        relationships = []
        patterns = self.get_relationship_patterns()

        # Track current class context for composition relationships
        current_class = None
        class_pattern = re.compile(r'^\s*(?:public|private|internal|protected)?\s*(?:sealed|abstract)?\s*class\s+(\w+)', re.MULTILINE)

        # Build a map of line numbers to classes
        line_to_class = {}
        for match in class_pattern.finditer(source_code):
            class_name = match.group(1)
            start_line = source_code[:match.start()].count('\n')
            # Assume class scope extends until next class or end of file
            line_to_class[start_line] = class_name

        for rel_type, rel_config in patterns.items():
            pattern = rel_config.get('pattern')
            if not pattern:
                continue

            try:
                regex = re.compile(pattern, re.MULTILINE)
                for match in regex.finditer(source_code):
                    # Determine current class context
                    match_line = source_code[:match.start()].count('\n')
                    current_class = None
                    for class_line in sorted(line_to_class.keys(), reverse=True):
                        if match_line >= class_line:
                            current_class = line_to_class[class_line]
                            break

                    # Extract relationship based on config
                    extract_config = rel_config.get('extract', {})
                    rel = self._build_relationship(
                        rel_type=rel_type,
                        match=match,
                        extract_config=extract_config,
                        style_config=rel_config.get('style', {}),
                        label=rel_config.get('label', rel_type),
                        context_class=current_class
                    )
                    if rel:
                        relationships.append(rel)

            except re.error as e:
                print(f"Warning: Invalid regex pattern for {rel_type}: {e}")
                continue

        return relationships

    def _build_relationship(
        self,
        rel_type: str,
        match: re.Match,
        extract_config: Dict[str, Any],
        style_config: Dict[str, Any],
        label: str,
        context_class: Optional[str] = None
    ) -> Optional[Relationship]:
        """Build a Relationship object from regex match."""
        try:
            # Handle different extraction patterns
            if rel_type == "inheritance":
                if 'child' in extract_config and 'parent' in extract_config:
                    child_idx = extract_config['child']
                    parent_idx = extract_config['parent']
                    return Relationship(
                        type=rel_type,
                        source=match.group(child_idx),
                        target=match.group(parent_idx),
                        label=label,
                        style=style_config
                    )

            elif rel_type == "interface_implementation":
                if 'implementer' in extract_config and 'interface' in extract_config:
                    impl_idx = extract_config['implementer']
                    iface_idx = extract_config['interface']
                    return Relationship(
                        type=rel_type,
                        source=match.group(impl_idx),
                        target=f"I{match.group(iface_idx)}",  # Reconstruct interface name
                        label=label,
                        style=style_config
                    )

            elif rel_type == "composition":
                if 'type' in extract_config and 'field' in extract_config:
                    type_idx = extract_config['type']
                    field_idx = extract_config['field']

                    # Use context_class if available, otherwise mark as unknown
                    source_class = context_class if context_class else "<context>"

                    return Relationship(
                        type=rel_type,
                        source=source_class,
                        target=match.group(type_idx),
                        label=label,
                        style=style_config,
                        extra_info={'field_name': match.group(field_idx)}
                    )

        except (IndexError, KeyError) as e:
            print(f"Warning: Failed to extract relationship: {e}")
            return None

        return None

    def get_visualization_config(self, diagram_type: str = None) -> Dict[str, Any]:
        """Get visualization configuration for a diagram type."""
        if diagram_type is None:
            diagram_type = self.data['visualization'].get('default_diagram', 'flow')

        viz_config = self.data['visualization'].get(diagram_type, {})
        return viz_config

    def get_mermaid_template(self, template_name: str = "class_diagram_template") -> str:
        """Get Mermaid diagram template."""
        return self.data.get('mermaid', {}).get(template_name, "")

    def get_hot_path_config(self) -> Dict[str, Any]:
        """Get hot path visualization configuration."""
        return self.data.get('hot_paths', {})

    def get_ctags_options(self) -> List[str]:
        """Get ctags options for this language."""
        return self.data.get('parsing', {}).get('ctags_options', [])


class LanguageConfigManager:
    """Manages loading and selection of language configurations."""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path(__file__).parent
        self.config_dir = Path(config_dir)
        self.configs: Dict[str, LanguageConfig] = {}
        self._load_configs()

    def _load_configs(self):
        """Load all YAML configs from the config directory."""
        for config_file in self.config_dir.glob("*.yaml"):
            if config_file.name == "base.yaml":
                continue  # Skip base config for now

            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)

                lang_name = config_data['language']['name'].lower()
                self.configs[lang_name] = LanguageConfig(config_data)

                print(f"[CONFIG] Loaded config for {config_data['language']['name']}")

            except Exception as e:
                print(f"Warning: Failed to load config {config_file}: {e}")

    def get_config(self, language: str) -> Optional[LanguageConfig]:
        """Get configuration for a specific language."""
        return self.configs.get(language.lower())

    def get_config_for_extension(self, extension: str) -> Optional[LanguageConfig]:
        """Get configuration based on file extension."""
        if not extension.startswith('.'):
            extension = f'.{extension}'

        for config in self.configs.values():
            if extension in config.extensions:
                return config

        return None

    def get_config_for_file(self, file_path: str) -> Optional[LanguageConfig]:
        """Get configuration based on file path."""
        extension = Path(file_path).suffix
        return self.get_config_for_extension(extension)

    def detect_language(self, file_path: str) -> str:
        """Detect language from file extension."""
        config = self.get_config_for_file(file_path)
        return config.name if config else "Unknown"

    def get_all_languages(self) -> List[str]:
        """Get list of all supported languages."""
        return list(self.configs.keys())


class RelationshipGraph:
    """Builds a graph of code relationships."""

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}  # class/module name -> metadata
        self.edges: List[Relationship] = []

    def add_node(self, name: str, node_type: str = "class", metadata: Optional[Dict] = None):
        """Add a node to the graph."""
        if name not in self.nodes:
            self.nodes[name] = {
                'type': node_type,
                'metadata': metadata or {}
            }

    def add_relationship(self, relationship: Relationship):
        """Add a relationship edge."""
        self.add_node(relationship.source)
        self.add_node(relationship.target)
        self.edges.append(relationship)

    def to_mermaid_class_diagram(self, language_config: Optional['LanguageConfig'] = None) -> str:
        """Generate Mermaid class diagram from relationships.

        Args:
            language_config: Optional language config to apply visualization rules
        """
        # Check if subgraph containment mode is enabled
        use_subgraphs = False
        viz_config = {}

        if language_config:
            viz_config = language_config.get_visualization_config('class_diagram')
            use_subgraphs = viz_config.get('containment_mode') == 'subgraph'

        if use_subgraphs:
            return self._generate_subgraph_diagram(viz_config)
        else:
            return self._generate_flat_diagram()

    def _generate_flat_diagram(self) -> str:
        """Generate traditional flat class diagram."""
        lines = ["classDiagram"]

        # Add nodes
        for node_name in sorted(self.nodes.keys()):
            if node_name != "<context>":
                lines.append(f"    class {node_name}")

        # Add relationships
        for rel in self.edges:
            if rel.source == "<context>":
                continue  # Skip context-dependent relationships for now

            mermaid_arrow = self._get_mermaid_arrow(rel.type)
            lines.append(f"    {rel.source} {mermaid_arrow} {rel.target} : {rel.label}")

        return '\n'.join(lines)

    def _generate_subgraph_diagram(self, viz_config: Dict[str, Any]) -> str:
        """Generate class diagram with subgraph containment.

        Groups class members (fields, properties, methods) inside their containing class.
        """
        lines = ["classDiagram"]

        # Organize relationships by class
        class_members = defaultdict(lambda: {'fields': [], 'properties': [], 'methods': []})
        class_relationships = []  # Inheritance, interfaces

        for rel in self.edges:
            if rel.source == "<context>":
                continue

            if rel.type == 'composition':
                # This is a member of the source class
                field_name = rel.extra_info.get('field_name', rel.target) if rel.extra_info else rel.target
                class_members[rel.source]['fields'].append({
                    'name': field_name,
                    'type': rel.target
                })
            elif rel.type in ('inheritance', 'interface_implementation', 'dependency'):
                # Class-level relationship
                class_relationships.append(rel)

        # Get member styling from config
        member_style = viz_config.get('member_style', {})
        field_prefix = member_style.get('fields', {}).get('prefix', '+')
        prop_prefix = member_style.get('properties', {}).get('prefix', '~')
        method_prefix = member_style.get('methods', {}).get('prefix', '()')

        # Generate class definitions with members
        all_classes = set(self.nodes.keys()) - {"<context>"}
        for class_name in sorted(all_classes):
            members = class_members.get(class_name, {'fields': [], 'properties': [], 'methods': []})

            if members['fields'] or members['properties'] or members['methods']:
                # Class with members - use full syntax
                lines.append(f"    class {class_name} {{")

                # Add fields
                for field in members['fields']:
                    lines.append(f"        {field_prefix}{field['name']} : {field['type']}")

                # Add properties (if we can distinguish them)
                for prop in members['properties']:
                    lines.append(f"        {prop_prefix}{prop['name']} : {prop['type']}")

                # Add methods (if we can distinguish them)
                for method in members['methods']:
                    lines.append(f"        {method_prefix}{method['name']}")

                lines.append(f"    }}")
            else:
                # Empty class - simple declaration
                lines.append(f"    class {class_name}")

        # Add class-level relationships
        for rel in class_relationships:
            mermaid_arrow = self._get_mermaid_arrow(rel.type)
            lines.append(f"    {rel.source} {mermaid_arrow} {rel.target} : {rel.label}")

        return '\n'.join(lines)

    def _get_mermaid_arrow(self, rel_type: str) -> str:
        """Get Mermaid arrow notation for relationship type."""
        arrow_map = {
            'inheritance': '--|>',
            'interface_implementation': '..|>',
            'composition': '*--',
            'dependency': '-->',
        }
        return arrow_map.get(rel_type, '-->')

    def to_webgl_data(self, hot_path_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Convert graph to WebGL visualization data."""
        nodes = []
        edges = []

        for node_name, node_data in self.nodes.items():
            if node_name == "<context>":
                continue

            nodes.append({
                'id': node_name,
                'type': node_data['type'],
                'label': node_name
            })

        for rel in self.edges:
            if rel.source == "<context>":
                continue

            edges.append({
                'from': rel.source,
                'to': rel.target,
                'type': rel.type,
                'label': rel.label,
                'style': rel.style
            })

        result = {
            'nodes': nodes,
            'edges': edges
        }

        # Merge with hot path data if available
        if hot_path_data:
            result['hot_paths'] = hot_path_data

        return result


# Example usage
if __name__ == "__main__":
    # Load configs
    manager = LanguageConfigManager()

    print("\nSupported languages:")
    for lang in manager.get_all_languages():
        print(f"  - {lang}")

    # Test C# config
    csharp_config = manager.get_config("c#")
    if csharp_config:
        print(f"\nC# Config loaded:")
        print(f"  Extensions: {csharp_config.extensions}")
        print(f"  Paradigm: {csharp_config.paradigm}")
        print(f"  Relationship patterns: {list(csharp_config.get_relationship_patterns().keys())}")

        # Test relationship extraction
        sample_code = """
public class MyService : ClickUpClient, IDisposable
{
    private readonly HttpClient _client;

    public async Task<string> GetData()
    {
        return await _client.GetStringAsync("/api/data");
    }
}
        """

        relationships = csharp_config.extract_relationships(sample_code, "MyService.cs")
        print(f"\n  Found {len(relationships)} relationships:")
        for rel in relationships:
            print(f"    - {rel.source} {rel.type} {rel.target}")

        # Build relationship graph
        graph = RelationshipGraph()
        for rel in relationships:
            graph.add_relationship(rel)

        # Test flat diagram
        print("\n  Flat class diagram:")
        flat_diagram = graph.to_mermaid_class_diagram()
        for line in flat_diagram.split('\n')[:10]:  # First 10 lines
            print(f"    {line}")

        # Test subgraph diagram with C# config
        print("\n  Subgraph class diagram (C# containment mode):")
        subgraph_diagram = graph.to_mermaid_class_diagram(csharp_config)
        for line in subgraph_diagram.split('\n'):
            print(f"    {line}")
