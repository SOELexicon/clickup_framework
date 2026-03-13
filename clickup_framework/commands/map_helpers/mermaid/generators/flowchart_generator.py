"""Flowchart diagram generator."""

from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, Optional, List, Tuple
from .base_generator import BaseGenerator
from ..config import get_config
from ..exceptions import DataValidationError
from ..styling import NodeStyle, EdgeStyle


class FlowchartGenerator(BaseGenerator):
    """Generate flowchart diagrams showing directory structure with symbol details."""

    def __init__(self, *args, **kwargs):
        """Initialize flowchart generator with configuration."""
        super().__init__(*args, **kwargs)
        self.config = get_config().flowchart
        self.edge_list: List[Tuple[str, str, str]] = []  # Track edges for styling

    def validate_inputs(self, **kwargs) -> None:
        """Validate flowchart diagram specific inputs."""
        symbols_by_file = self.stats.get('symbols_by_file', {})
        if not symbols_by_file:
            raise DataValidationError.missing_required_field(
                field_name='symbols_by_file',
                generator_type='flowchart',
                stats_keys=list(self.stats.keys())
            )

    def generate_body(self, **kwargs) -> None:
        """Generate flowchart diagram body."""
        symbols_by_file = self.stats.get('symbols_by_file', {})

        self._add_diagram_declaration("graph TB")

        # Group files by directory
        dir_structure = defaultdict(list)
        for file_path, symbols in symbols_by_file.items():
            if symbols:
                dir_name = str(Path(file_path).parent)
                if dir_name == '.':
                    dir_name = 'root'
                dir_structure[dir_name].append((file_path, symbols))

        # Sort directories and limit
        sorted_dirs = sorted(dir_structure.keys())[:self.config.max_directories]

        # Create directory nodes with custom styling
        dir_nodes = {}
        node_list = []  # Track all nodes for styling
        for idx, dir_name in enumerate(sorted_dirs):
            dir_id = f"DIR{idx}"
            dir_nodes[dir_name] = dir_id
            total_symbols = sum(len(syms) for _, syms in dir_structure[dir_name])
            safe_dir = dir_name.replace('\\', '/').replace('clickup_framework/', '')
            self._add_line(f'    {dir_id}["{safe_dir}<br/>{total_symbols} symbols"]')
            node_list.append((dir_id, 'directory', {'symbol_count': total_symbols, 'color_index': idx}))

        self._add_line("")

        # Add file nodes with more detail
        file_count = 0
        for dir_name in sorted_dirs:
            files = sorted(dir_structure[dir_name], key=lambda x: len(x[1]), reverse=True)[:self.config.max_files_per_directory]

            for file_path, symbols in files:
                file_id = f"F{file_count}"
                file_name = Path(file_path).name

                classes = sum(1 for s in symbols if s.get('kind') == 'class')
                functions = sum(1 for s in symbols if s.get('kind') in ['function', 'method'])
                members = sum(1 for s in symbols if s.get('kind') in ['member', 'variable'])

                parts = []
                if classes: parts.append(f"📦 {classes} classes")
                if functions: parts.append(f"⚙️ {functions} funcs")
                if members: parts.append(f"📊 {members} vars")

                detail = "<br/>".join(parts) if parts else f"{len(symbols)} symbols"
                self._add_line(f'    {file_id}["{file_name}<br/>{detail}"]')
                node_list.append((file_id, 'file', {'classes': classes, 'functions': functions, 'members': members}))

                if dir_name in dir_nodes:
                    self._add_line(f"    {dir_nodes[dir_name]} --> {file_id}")
                    self.edge_list.append((dir_nodes[dir_name], file_id, 'dir_to_file'))

                if classes > 0 and classes <= self.config.class_detail_threshold:
                    class_symbols = [s for s in symbols if s.get('kind') == 'class']
                    for cls_idx, cls in enumerate(class_symbols):
                        cls_id = f"C{file_count}_{cls_idx}"
                        cls_name = cls.get('name', 'Unknown')
                        methods = [s for s in symbols if s.get('scope') == cls_name and s.get('kind') in ['function', 'method']]
                        self._add_line(f'    {cls_id}["{cls_name}<br/>{len(methods)} methods"]')
                        node_list.append((cls_id, 'class', {'method_count': len(methods), 'class_name': cls_name}))
                        self._add_line(f"    {file_id} --> {cls_id}")
                        self.edge_list.append((file_id, cls_id, 'file_to_class'))

                file_count += 1
                if file_count >= self.config.max_total_files:
                    break

            if file_count >= self.config.max_total_files:
                break

        # Apply custom styling to all nodes and edges
        self._apply_custom_styles(node_list)

    def style_node(
        self,
        node_id: str,
        node_type: str = 'default',
        properties: Optional[Dict[str, Any]] = None
    ) -> NodeStyle:
        """Custom node styling for flowchart diagrams.

        This demonstrates hierarchical styling for different node types:
        - Directory nodes: Vibrant colors rotated by index
        - File nodes: Cyan for code files
        - Class nodes: Purple for class definitions

        Args:
            node_id: Node identifier (e.g., 'DIR0', 'F5', 'C2_0')
            node_type: Node classification ('directory', 'file', 'class')
            properties: Additional properties for styling decisions

        Returns:
            NodeStyle with custom colors based on node type
        """
        properties = properties or {}

        if node_type == 'directory':
            # Use color rotation for directories
            color_index = properties.get('color_index', 0)
            color_scheme = self.theme_manager.get_color_scheme(color_index)
            return NodeStyle(
                name='directory',
                fill=color_scheme.fill,
                stroke=color_scheme.stroke,
                stroke_width='3px',  # Thicker for emphasis
                text_color=color_scheme.text_color
            )
        elif node_type == 'file':
            # Cyan theme for files
            return NodeStyle(
                name='file',
                fill='#0c1c20',      # Dark cyan background
                stroke='#06b6d4',     # Bright cyan border
                stroke_width='2px',
                text_color='#06b6d4'  # Bright cyan text
            )
        elif node_type == 'class':
            # Purple theme for classes (from theme manager)
            style = self.theme_manager.apply_to_subgraph('class_subgraph')
            # Parse the style string and return as NodeStyle
            return NodeStyle(
                name='class',
                fill='#0f0f0f',
                stroke='#8b5cf6',
                stroke_width='2px',
                text_color='#8b5cf6'
            )

        # Fallback to theme
        return super().style_node(node_id, node_type, properties)

    def style_edge(
        self,
        edge_id: str,
        edge_type: str = 'default',
        properties: Optional[Dict[str, Any]] = None
    ) -> EdgeStyle:
        """Custom edge styling for flowchart diagrams.

        Demonstrates relationship-based edge styling:
        - Directory → File: Solid green lines (structural hierarchy)
        - File → Class: Dashed cyan lines (containment)

        Args:
            edge_id: Edge identifier (e.g., 'DIR0->F5')
            edge_type: Relationship type ('dir_to_file', 'file_to_class')
            properties: Additional properties

        Returns:
            EdgeStyle for the relationship type
        """
        properties = properties or {}

        if edge_type == 'dir_to_file':
            return EdgeStyle(
                name='dir_to_file',
                stroke='#10b981',      # Green for directory hierarchy
                stroke_width='2px',
                stroke_dash='',        # Solid line
                arrow_style='normal'
            )
        elif edge_type == 'file_to_class':
            return EdgeStyle(
                name='file_to_class',
                stroke='#06b6d4',      # Cyan for containment
                stroke_width='1px',
                stroke_dash='5 5',     # Dashed line
                arrow_style='normal'
            )

        # Fallback to theme
        return super().style_edge(edge_id, edge_type, properties)

    def _apply_custom_styles(
        self,
        node_list: List[Tuple[str, str, Dict[str, Any]]]
    ) -> None:
        """Apply custom styling to nodes and edges.

        Args:
            node_list: List of (node_id, node_type, properties) tuples
        """
        self._add_line("")
        self._add_line("    %% Custom styling")

        # Apply node styles
        for node_id, node_type, properties in node_list:
            node_style = self.style_node(node_id, node_type, properties)
            style_str = node_style.to_mermaid_style()
            self._add_line(f"    style {node_id} {style_str}")

        # Apply edge styles
        for idx, (from_node, to_node, edge_type) in enumerate(self.edge_list):
            edge_id = f"{from_node}->{to_node}"
            edge_style = self.style_edge(edge_id, edge_type)
            style_str = edge_style.to_mermaid_style()
            self._add_line(f"    linkStyle {idx} {style_str}")
