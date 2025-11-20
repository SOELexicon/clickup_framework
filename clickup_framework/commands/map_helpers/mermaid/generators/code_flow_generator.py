"""Code flow diagram generator."""

from pathlib import Path
from collections import defaultdict
from .base_generator import BaseGenerator
from ..core.metadata_store import MetadataStore
from ..core.node_manager import NodeManager
from ..formatters.label_formatter import LabelFormatter


# Helper function for directory tree scanning
# NOTE: This function needs to be imported from the appropriate module or created
def scan_directory_structure(base_path: str, max_depth: int = 3):
    """
    Scan directory structure and return tree representation.

    This is a placeholder - the actual implementation should be imported
    from mermaid.builders.tree_builder or implemented here.
    """
    # For now, return a basic structure
    # TODO: Import from TreeBuilder or implement proper scanning
    return {
        '__subdirs__': {},
        '__files__': {}
    }


class CodeFlowGenerator(BaseGenerator):
    """Generate code execution flow diagrams with hierarchical subgraphs."""

    def validate_inputs(self, **kwargs) -> None:
        """Validate code flow diagram specific inputs."""
        function_calls = self.stats.get('function_calls', {})
        all_symbols = self.stats.get('all_symbols', {})
        if not function_calls or not all_symbols:
            raise ValueError("No function_calls or all_symbols data found in stats")

    def _add_header(self) -> None:
        """Add header with custom mermaid initialization config."""
        self.lines.extend([
            "# Code Map - Execution Flow (Call Graph)",
            "",
            "```mermaid",
            "%%{init: {'flowchart': {'curve': 'linear', 'defaultRenderer': 'elk', 'nodeSpacing': 100, 'rankSpacing': 100}, 'theme': 'dark'}}%%"
        ])

    def _add_footer(self) -> None:
        """Override footer to add custom legend and statistics."""
        # Get variables that were created in generate_body
        processed = getattr(self, '_processed', [])
        functions_by_folder = getattr(self, '_functions_by_folder', {})
        function_calls = self.stats.get('function_calls', {})
        entry_points = getattr(self, '_entry_points', [])

        self.lines.extend([
            "```",
            "",
            "## Legend",
            "- **Purple nodes**: Entry points (functions not called by others)",
            "- **Green-bordered nodes**: Called functions",
            "- **DIR subgraphs**: Group by directory (scanned from filesystem)",
            "- **FILE subgraphs**: Group related files (e.g., Component.razor + Component.razor.cs)",
            "- **CLASS subgraphs**: Group by class when multiple classes in same file",
            "- **Line numbers**: Show start-end lines in source file",
            "",
            f"## Statistics",
            f"- **Total Functions Mapped**: {len(processed)}",
            f"- **Folders**: {len(functions_by_folder)}",
            f"- **File Components**: {sum(len(files) for files in functions_by_folder.values())}",
            f"- **Classes/Modules**: {sum(sum(len(classes) for classes in files.values()) for files in functions_by_folder.values())}",
            f"- **Total Call Relationships**: {sum(len(calls) for calls in function_calls.values())}",
            f"- **Entry Points Found**: {len(entry_points)}",
            f"- **Directory Tree Depth**: 3 (configurable)",
        ])

    def generate_body(self, **kwargs) -> None:
        """Generate code flow diagram body with nested subgraphs."""
        function_calls = self.stats.get('function_calls', {})
        all_symbols = self.stats.get('all_symbols', {})

        self._add_diagram_declaration("graph TD")

        # Initialize node manager (theme_manager already available from BaseGenerator)
        metadata_store = MetadataStore()
        label_formatter = LabelFormatter('minimal')
        node_manager = NodeManager(metadata_store, label_formatter)

        # Find entry points
        called_functions = set()
        for calls in function_calls.values():
            called_functions.update(calls)

        entry_points = [func for func in function_calls.keys()
                       if func not in called_functions][:10]
        self._entry_points = entry_points

        # Collect functions
        collected_symbols = {}
        for entry in entry_points:
            if len(node_manager.processed) >= 80:
                break
            collected = node_manager.collect_functions_recursive(
                entry,
                function_calls,
                all_symbols,
                max_depth=8,
                max_nodes=80
            )
            for func_name in collected:
                if func_name in all_symbols:
                    collected_symbols[func_name] = all_symbols[func_name]

        node_ids = node_manager.node_ids
        processed = node_manager.processed
        self._processed = processed

        print(f"[INFO] Collected {len(collected_symbols)} functions to map")

        # Determine base path
        base_path = Path.cwd()
        all_paths = []
        for symbol in collected_symbols.values():
            file_path = symbol.get('path', '')
            if file_path:
                abs_path = Path(file_path).resolve()
                all_paths.append(abs_path)

        if all_paths:
            common_parts = list(all_paths[0].parts)
            for path in all_paths[1:]:
                path_parts = list(path.parts)
                for i, (a, b) in enumerate(zip(common_parts, path_parts)):
                    if a != b:
                        common_parts = common_parts[:i]
                        break
                else:
                    common_parts = common_parts[:len(path_parts)]

            if common_parts:
                base_path = Path(*common_parts)

        base_path_str = str(base_path)
        print(f"[INFO] Scanning directory structure from: {base_path_str}")
        dir_tree = scan_directory_structure(base_path_str, max_depth=3)

        # Group functions by folder
        functions_by_folder = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for func_name, symbol in collected_symbols.items():
            file_path = symbol.get('path', '')
            scope = symbol.get('scope', '')

            if file_path:
                path_obj = Path(file_path)
                folder = str(path_obj.parent).replace('\\\\', '/')
                if folder == '.':
                    folder = 'root'

                base_name = path_obj.stem
                if base_name.endswith('.razor'):
                    base_name = base_name[:-6]

                class_name = scope if scope else f"module_{base_name}"
                functions_by_folder[folder][base_name][class_name].append(func_name)
            else:
                functions_by_folder['root']['unknown']['global'].append(func_name)

        self._functions_by_folder = functions_by_folder

        # Nested helper function to populate tree
        def populate_tree_with_functions(dir_tree, functions_by_folder, base_path_str):
            for folder_path, files_dict in functions_by_folder.items():
                if folder_path == 'root':
                    if '__files__' not in dir_tree:
                        dir_tree['__files__'] = {}
                    dir_tree['__files__'].update(files_dict)
                    continue

                parts = folder_path.replace('\\\\', '/').split('/')
                current = dir_tree
                for part in parts:
                    if part in ('', '.'):
                        continue
                    subdirs = current.get('__subdirs__', {})
                    if part in subdirs:
                        current = subdirs[part]
                    else:
                        break
                else:
                    if '__files__' not in current:
                        current['__files__'] = {}
                    current['__files__'].update(files_dict)
            return dir_tree

        populate_tree_with_functions(dir_tree, functions_by_folder, base_path_str)
        print(f"[INFO] Populated directory tree with collected functions")

        # Subgraph generation state
        subgraph_count = 0
        file_sg_count = 0

        def has_functions_in_tree(tree_node):
            files_dict = tree_node.get('__files__', {})
            if files_dict:
                for file_classes in files_dict.values():
                    if any(file_classes.values()):
                        return True
            subdirs = tree_node.get('__subdirs__', {})
            for subdir_node in subdirs.values():
                if has_functions_in_tree(subdir_node):
                    return True
            return False

        def generate_nested_subgraphs(tree, depth=0, path_parts=[], skip_root=True):
            nonlocal subgraph_count, file_sg_count

            if skip_root and depth == 0:
                files_dict = tree.get('__files__', {})
                if files_dict:
                    generate_file_subgraphs(files_dict, depth)
                subdirs = tree.get('__subdirs__', {})
                generate_nested_subgraphs(subdirs, depth, path_parts, skip_root=False)
                return

            for dir_name in sorted(tree.keys()):
                node = tree[dir_name]
                if not has_functions_in_tree(node):
                    continue

                files_dict = node.get('__files__', {})
                subdirs = node.get('__subdirs__', {})

                folder_sg_id = f"SG{subgraph_count}"
                subgraph_count += 1

                indent = "    " * (depth + 1)
                display_name = f"DIR: {dir_name}"
                self._add_line(f"{indent}subgraph {folder_sg_id}[\"{display_name}\"]")

                if files_dict:
                    generate_file_subgraphs(files_dict, depth + 1)

                if subdirs:
                    generate_nested_subgraphs(subdirs, depth + 1, path_parts + [dir_name], skip_root=False)

                indent = "    " * (depth + 1)
                self._add_line(f"{indent}end")
                self._add_line("")

        def generate_file_subgraphs(files_dict, depth):
            nonlocal file_sg_count

            for base_file_name, classes_dict in sorted(files_dict.items()):
                if not classes_dict:
                    continue

                file_sg_id = f"FSG{file_sg_count}"
                file_sg_count += 1

                file_indent = "    " * (depth + 1)
                self._add_line(f"{file_indent}subgraph {file_sg_id}[\"FILE: {base_file_name}\"]")

                has_multiple_classes = len([c for c in classes_dict.keys() if not c.startswith('module_')]) > 1
                class_sg_count = 0

                for class_name, funcs in sorted(classes_dict.items()):
                    if not funcs:
                        continue

                    if has_multiple_classes and not class_name.startswith('module_'):
                        class_sg_id = f"CSG{file_sg_count}_{class_sg_count}"
                        class_sg_count += 1
                        class_display = class_name.replace('module_', '')
                        class_indent = "    " * (depth + 2)
                        self._add_line(f"{class_indent}subgraph {class_sg_id}[\"CLASS: {class_display}\"]")
                        node_indent = "    " * (depth + 3)
                    else:
                        node_indent = "    " * (depth + 2)

                    for func_name in funcs[:50]:
                        node_id = node_manager.get_node_id(func_name)
                        if not node_id:
                            continue

                        symbol = collected_symbols.get(func_name, {})
                        label = label_formatter.format_function_label(func_name, symbol)
                        self._add_line(f"{node_indent}{node_id}[\"{label}\"]")

                    if has_multiple_classes and not class_name.startswith('module_'):
                        class_indent = "    " * (depth + 2)
                        self._add_line(f"{class_indent}end")

                file_indent = "    " * (depth + 1)
                self._add_line(f"{file_indent}end")

        # Generate subgraphs
        generate_nested_subgraphs(dir_tree)

        # Color mapping
        node_to_color = {}
        for i, (folder, files_dict) in enumerate(sorted(functions_by_folder.items())[:20]):
            color_idx = i % self.theme_manager.get_theme()['color_count']
            color_scheme = self.theme_manager.get_color_scheme(color_idx)
            edge_color = color_scheme.edge_color()

            for base_file_name, classes_dict in files_dict.items():
                for class_name, funcs in classes_dict.items():
                    for func in funcs:
                        full_name = f"{class_name.replace('module_', '')}.{func}" if class_name.startswith('module_') else func
                        for potential_name in [full_name, func]:
                            if potential_name in node_ids:
                                node_to_color[node_ids[potential_name]] = edge_color

        # Add connections
        self._add_line("    %% Connections")
        link_count = 0
        link_styles = []

        for func_name in processed:
            if func_name not in node_ids:
                continue

            from_id = node_ids[func_name]
            calls = function_calls.get(func_name, [])
            for called_func in calls[:5]:
                if called_func in node_ids:
                    to_id = node_ids[called_func]
                    edge_color = node_to_color.get(to_id, self.theme_manager.apply_to_edges())
                    self._add_line(f"    {from_id} --> {to_id}")
                    link_styles.append(f"    linkStyle {link_count} stroke:{edge_color},stroke-width:3px")
                    link_count += 1

        self._add_line("")

        # Apply link styles
        for style in link_styles:
            self._add_line(style)

        self._add_line("")

        # Apply theme styling
        self._add_line(f"    %% Styling - {self.theme_manager.current_theme.capitalize()} Theme")

        for i in range(subgraph_count):
            color_scheme = self.theme_manager.get_color_scheme(i)
            self._add_line(f"    style SG{i} {color_scheme.to_mermaid_style()}")

        for i in range(file_sg_count):
            style = self.theme_manager.apply_to_subgraph('file_subgraph')
            self._add_line(f"    style FSG{i} {style}")

        for i in range(file_sg_count):
            for j in range(10):
                style = self.theme_manager.apply_to_subgraph('class_subgraph')
                self._add_line(f"    style CSG{i}_{j} {style}")

        for func_name, node_id in node_ids.items():
            if func_name in entry_points:
                style = self.theme_manager.apply_to_nodes('entry_point')
                self._add_line(f"    style {node_id} {style}")
            else:
                style = self.theme_manager.apply_to_nodes('default')
                self._add_line(f"    style {node_id} {style}")
