"""Mermaid diagram generators for code maps."""

import sys
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict
from .mermaid_validator import validate_and_raise, get_diagram_stats
from .mermaid.core.metadata_store import MetadataStore
from .mermaid.core.node_manager import NodeManager
from .mermaid.formatters.label_formatter import LabelFormatter
from .mermaid.styling import ThemeManager, NodeStyler
from .mermaid.generators import BaseGenerator




# ========== Generator Classes (migrated to BaseGenerator pattern) ==========

class FlowchartGenerator(BaseGenerator):
    """Generate flowchart diagrams showing directory structure with symbol details."""

    def validate_inputs(self, **kwargs) -> None:
        """Validate flowchart diagram specific inputs."""
        symbols_by_file = self.stats.get('symbols_by_file', {})
        if not symbols_by_file:
            raise ValueError("No symbols_by_file data found in stats")

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
        sorted_dirs = sorted(dir_structure.keys())[:10]

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
            files = sorted(dir_structure[dir_name], key=lambda x: len(x[1]), reverse=True)[:5]

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

                if classes > 0 and classes <= 5:
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
                if file_count >= 30:
                    break

            if file_count >= 30:
                break


class ClassDiagramGenerator(BaseGenerator):
    """Generate class diagrams showing detailed code structure with inheritance."""

    def validate_inputs(self, **kwargs) -> None:
        """Validate class diagram specific inputs."""
        symbols_by_file = self.stats.get('symbols_by_file', {})
        if not symbols_by_file:
            raise ValueError("No symbols_by_file data found in stats")

    def generate_body(self, **kwargs) -> None:
        """Generate class diagram body."""
        symbols_by_file = self.stats.get('symbols_by_file', {})

        self._add_diagram_declaration("classDiagram")

        all_classes = {}
        class_count = 0

        for file_path, symbols in sorted(symbols_by_file.items()):
            if class_count >= 20:
                break

            classes = [s for s in symbols if s.get('kind') == 'class']
            for cls in classes:
                class_name = cls.get('name', 'Unknown')

                if class_name in all_classes:
                    continue

                all_classes[class_name] = {
                    'file': Path(file_path).name,
                    'line': cls.get('line', 0),
                    'methods': [],
                    'members': []
                }

                methods = [s for s in symbols
                          if s.get('scope') == class_name
                          and s.get('kind') in ['function', 'method']]

                members = [s for s in symbols
                          if s.get('scope') == class_name
                          and s.get('kind') in ['member', 'variable']]

                all_classes[class_name]['methods'] = methods[:15]
                all_classes[class_name]['members'] = members[:10]

                class_count += 1

        for class_name, details in sorted(all_classes.items()):
            self._add_line(f"    class {class_name} {{")
            self._add_line(f"        <<{details['file']}>>")

            for member in details['members']:
                member_name = member.get('name', '')
                self._add_line(f"        -{member_name}")

            for method in details['methods']:
                method_name = method.get('name', '')
                if method_name.startswith('__'):
                    visibility = '-'
                elif method_name.startswith('_'):
                    visibility = '-'
                else:
                    visibility = '+'
                self._add_line(f"        {visibility}{method_name}()")

            self._add_line("    }")

        self._add_line("")
        self._add_line("    %% Inheritance relationships")
        for class_name in all_classes.keys():
            if 'Base' in class_name:
                for other_class in all_classes.keys():
                    if other_class != class_name and 'Base' not in other_class:
                        if any(word in other_class for word in class_name.replace('Base', '').split()):
                            self._add_line(f"    {class_name} <|-- {other_class}")


class PieChartGenerator(BaseGenerator):
    """Generate pie chart diagrams showing language distribution."""

    def validate_inputs(self, **kwargs) -> None:
        """Validate pie chart diagram specific inputs."""
        by_language = self.stats.get('by_language', {})
        if not by_language:
            raise ValueError("No by_language data found in stats")

    def generate_body(self, **kwargs) -> None:
        """Generate pie chart diagram body."""
        by_language = self.stats.get('by_language', {})

        self._add_diagram_declaration("pie title Code Distribution by Language")

        for lang in sorted(by_language.keys()):
            count = sum(by_language[lang].values())
            self._add_line(f'    "{lang}" : {count}')


class MindmapGenerator(BaseGenerator):
    """Generate mindmap diagrams showing code structure hierarchy."""

    def validate_inputs(self, **kwargs) -> None:
        """Validate mindmap diagram specific inputs."""
        symbols_by_file = self.stats.get('symbols_by_file', {})
        by_language = self.stats.get('by_language', {})
        if not symbols_by_file or not by_language:
            raise ValueError("No symbols_by_file or by_language data found in stats")

    def generate_body(self, **kwargs) -> None:
        """Generate mindmap diagram body."""
        symbols_by_file = self.stats.get('symbols_by_file', {})
        by_language = self.stats.get('by_language', {})

        self._add_diagram_declaration("mindmap")
        self._add_line("  root((Codebase))")

        for lang in sorted(by_language.keys())[:5]:
            self._add_line(f"    {lang}")

            lang_files = []
            for file_path, symbols in symbols_by_file.items():
                if symbols and symbols[0].get('language') == lang:
                    lang_files.append((file_path, symbols))

            lang_files.sort(key=lambda x: len(x[1]), reverse=True)
            for file_path, symbols in lang_files[:5]:
                file_name = Path(file_path).name
                symbol_count = len(symbols)
                self._add_line(f"      {file_name} ({symbol_count})")


class SequenceGenerator(BaseGenerator):
    """Generate sequence diagrams showing typical execution flow."""

    def validate_inputs(self, **kwargs) -> None:
        """Validate sequence diagram specific inputs."""
        function_calls = self.stats.get('function_calls', {})
        all_symbols = self.stats.get('all_symbols', {})
        if not function_calls or not all_symbols:
            raise ValueError("No function_calls or all_symbols data found in stats")

    def generate_body(self, **kwargs) -> None:
        """Generate sequence diagram body."""
        function_calls = self.stats.get('function_calls', {})
        all_symbols = self.stats.get('all_symbols', {})

        self._add_diagram_declaration("sequenceDiagram")

        entry_patterns = ['main', '__init__', 'run', 'execute', 'start', 'process']
        entry_funcs = []

        for func_name in function_calls.keys():
            short_name = func_name.split('.')[-1].lower()
            if any(pattern in short_name for pattern in entry_patterns):
                entry_funcs.append(func_name)

        if not entry_funcs:
            entry_funcs = sorted(function_calls.keys(),
                               key=lambda f: len(function_calls.get(f, [])),
                               reverse=True)[:3]

        if entry_funcs:
            entry = entry_funcs[0]
            participants = set()

            def trace_calls(func, depth=0, max_depth=5):
                if depth > max_depth:
                    return

                symbol = all_symbols.get(func, {})
                scope = symbol.get('scope', 'Module')
                func_short = func.split('.')[-1]

                if scope:
                    participants.add(scope)

                for called in function_calls.get(func, [])[:3]:
                    called_symbol = all_symbols.get(called, {})
                    called_scope = called_symbol.get('scope', 'Module')
                    called_short = called.split('.')[-1]

                    if called_scope:
                        participants.add(called_scope)

                    from_participant = scope if scope else 'Module'
                    to_participant = called_scope if called_scope else 'Module'

                    self._add_line(f"    {from_participant}->>+{to_participant}: {called_short}()")
                    trace_calls(called, depth + 1, max_depth)
                    self._add_line(f"    {to_participant}-->>-{from_participant}: return")

            for participant in sorted(participants)[:10]:
                self.lines.insert(len(self.lines) - len([l for l in self.lines if '->>' in l]), f"    participant {participant}")

            entry_short = entry.split('.')[-1]
            entry_scope = all_symbols.get(entry, {}).get('scope', 'Main')
            if entry_scope:
                self._add_line(f"    Note over {entry_scope}: {entry_short}() starts")
            trace_calls(entry, depth=0, max_depth=4)

    def _add_footer(self) -> None:
        """Override footer to add sequence-specific description."""
        self.lines.extend([
            "```",
            "",
            "## Description",
            "This sequence diagram shows the typical execution flow starting from an entry point.",
            "Arrows show function calls and returns between different components.",
        ])

        # Add entry point info
        function_calls = self.stats.get('function_calls', {})
        entry_patterns = ['main', '__init__', 'run', 'execute', 'start', 'process']
        entry_funcs = []

        for func_name in function_calls.keys():
            short_name = func_name.split('.')[-1].lower()
            if any(pattern in short_name for pattern in entry_patterns):
                entry_funcs.append(func_name)

        if not entry_funcs:
            entry_funcs = sorted(function_calls.keys(),
                               key=lambda f: len(function_calls.get(f, [])),
                               reverse=True)[:3]

        self.lines.extend([
            "",
            f"## Entry Point",
            f"- Starting from: `{entry_funcs[0] if entry_funcs else 'N/A'}`",
        ])

        # Don't call parent _add_footer as we're replacing it entirely


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


# ========== End Generator Classes ==========



# ========== Public API Functions (wrappers for backward compatibility) ==========

def generate_mermaid_flowchart(stats: Dict, output_file: str, theme: str = 'dark') -> None:
    """
    Generate a mermaid flowchart diagram showing directory structure with symbol details.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
        theme: Color theme to use ('dark' or 'light', default: 'dark')
    """
    generator = FlowchartGenerator(stats, output_file, theme)
    generator.generate()


def generate_mermaid_class(stats: Dict, output_file: str) -> None:
    """
    Generate a class diagram showing detailed code structure.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    generator = ClassDiagramGenerator(stats, output_file)
    generator.generate()


def generate_mermaid_pie(stats: Dict, output_file: str) -> None:
    """
    Generate a pie chart showing language distribution.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    generator = PieChartGenerator(stats, output_file)
    generator.generate()


def generate_mermaid_mindmap(stats: Dict, output_file: str) -> None:
    """
    Generate a mindmap showing code structure hierarchy.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    generator = MindmapGenerator(stats, output_file)
    generator.generate()


def generate_mermaid_sequence(stats: Dict, output_file: str) -> None:
    """
    Generate a sequence diagram showing typical execution flow.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    generator = SequenceGenerator(stats, output_file)
    generator.generate()


def generate_mermaid_code_flow(stats: Dict, output_file: str, theme: str = 'dark') -> None:
    """
    Generate a code execution flow diagram with hierarchical subgraphs.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
        theme: Color theme to use ('dark' or 'light', default: 'dark')
    """
    generator = CodeFlowGenerator(stats, output_file, theme)
    generator.generate()
