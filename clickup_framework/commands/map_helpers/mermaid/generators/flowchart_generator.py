"""Flowchart diagram generator."""

from pathlib import Path
from collections import defaultdict
from .base_generator import BaseGenerator
from ..config import get_config
from ..exceptions import DataValidationError


class FlowchartGenerator(BaseGenerator):
    """Generate flowchart diagrams showing directory structure with symbol details."""

    def __init__(self, *args, **kwargs):
        """Initialize flowchart generator with configuration."""
        super().__init__(*args, **kwargs)
        self.config = get_config().flowchart

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

        # Create directory nodes
        dir_nodes = {}
        for idx, dir_name in enumerate(sorted_dirs):
            dir_id = f"DIR{idx}"
            dir_nodes[dir_name] = dir_id
            total_symbols = sum(len(syms) for _, syms in dir_structure[dir_name])
            safe_dir = dir_name.replace('\\', '/').replace('clickup_framework/', '')
            self._add_line(f'    {dir_id}["{safe_dir}<br/>{total_symbols} symbols"]')
            color_scheme = self.theme_manager.get_color_scheme(idx)
            self._add_line(f"    style {dir_id} {color_scheme.to_mermaid_style()},stroke-width:3px")

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

                if dir_name in dir_nodes:
                    self._add_line(f"    {dir_nodes[dir_name]} --> {file_id}")

                if classes > 0 and classes <= self.config.class_detail_threshold:
                    class_symbols = [s for s in symbols if s.get('kind') == 'class']
                    for cls_idx, cls in enumerate(class_symbols):
                        cls_id = f"C{file_count}_{cls_idx}"
                        cls_name = cls.get('name', 'Unknown')
                        methods = [s for s in symbols if s.get('scope') == cls_name and s.get('kind') in ['function', 'method']]
                        self._add_line(f'    {cls_id}["{cls_name}<br/>{len(methods)} methods"]')
                        style = self.theme_manager.apply_to_subgraph('class_subgraph')
                        self._add_line(f"    style {cls_id} {style}")
                        self._add_line(f"    {file_id} --> {cls_id}")

                file_count += 1
                if file_count >= self.config.max_total_files:
                    break

            if file_count >= self.config.max_total_files:
                break
