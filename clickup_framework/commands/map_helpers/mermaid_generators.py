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


def generate_mermaid_flowchart(stats: Dict, output_file: str, theme: str = 'dark') -> None:
    """
    Generate a mermaid flowchart diagram showing directory structure with symbol details.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
        theme: Color theme to use ('dark' or 'light', default: 'dark')
    """
    symbols_by_file = stats.get('symbols_by_file', {})
    by_language = stats.get('by_language', {})

    # Initialize styling system
    theme_manager = ThemeManager(theme)

    # Build mermaid diagram
    lines = [
        "# Code Map - Architecture Diagram",
        "",
        "```mermaid",
        "graph TB"
    ]

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
        # Count total symbols in directory
        total_symbols = sum(len(syms) for _, syms in dir_structure[dir_name])
        safe_dir = dir_name.replace('\\', '/').replace('clickup_framework/', '')
        lines.append(f"    {dir_id}[\"{safe_dir}<br/>{total_symbols} symbols\"]")
        # Use color scheme from theme
        color_scheme = theme_manager.get_color_scheme(idx)
        lines.append(f"    style {dir_id} {color_scheme.to_mermaid_style()},stroke-width:3px")

    lines.append("")

    # Add file nodes with more detail
    file_count = 0
    for dir_name in sorted_dirs:
        files = sorted(dir_structure[dir_name], key=lambda x: len(x[1]), reverse=True)[:5]  # Top 5 files per dir

        for file_path, symbols in files:
            file_id = f"F{file_count}"
            file_name = Path(file_path).name

            # Count different symbol types
            classes = sum(1 for s in symbols if s.get('kind') == 'class')
            functions = sum(1 for s in symbols if s.get('kind') in ['function', 'method'])
            members = sum(1 for s in symbols if s.get('kind') in ['member', 'variable'])

            # Build detailed label
            parts = []
            if classes: parts.append(f"📦 {classes} classes")
            if functions: parts.append(f"⚙️ {functions} funcs")
            if members: parts.append(f"📊 {members} vars")

            detail = "<br/>".join(parts) if parts else f"{len(symbols)} symbols"
            lines.append(f"    {file_id}[\"{file_name}<br/>{detail}\"]")

            # Link file to directory
            if dir_name in dir_nodes:
                lines.append(f"    {dir_nodes[dir_name]} --> {file_id}")

            # Add class nodes for files with classes
            if classes > 0 and classes <= 5:
                class_symbols = [s for s in symbols if s.get('kind') == 'class']
                for cls_idx, cls in enumerate(class_symbols):
                    cls_id = f"C{file_count}_{cls_idx}"
                    cls_name = cls.get('name', 'Unknown')

                    # Count methods in this class
                    methods = [s for s in symbols if s.get('scope') == cls_name and s.get('kind') in ['function', 'method']]
                    lines.append(f"    {cls_id}[\"{cls_name}<br/>{len(methods)} methods\"]")
                    # Use theme for class styling
                    style = theme_manager.apply_to_subgraph('class_subgraph')
                    lines.append(f"    style {cls_id} {style}")
                    lines.append(f"    {file_id} --> {cls_id}")

            file_count += 1

            if file_count >= 30:
                break

        if file_count >= 30:
            break

    lines.append("```")
    lines.append("")

    # Add statistics summary
    lines.extend([
        "## Statistics",
        "",
        f"- **Total Symbols**: {stats.get('total_symbols', 0)}",
        f"- **Files Analyzed**: {stats.get('files_analyzed', 0)}",
        f"- **Languages**: {len(by_language)}",
        ""
    ])

    # Add language breakdown
    lines.append("### By Language")
    lines.append("")
    for lang in sorted(by_language.keys()):
        count = sum(by_language[lang].values())
        lines.append(f"- **{lang}**: {count} symbols")
        for kind, kind_count in sorted(by_language[lang].items()):
            lines.append(f"  - {kind}: {kind_count}")

    # Write to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"Error writing mermaid diagram: {e}", file=sys.stderr)


def generate_mermaid_class(stats: Dict, output_file: str) -> None:
    """
    Generate a mermaid class diagram showing detailed code structure with inheritance.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    symbols_by_file = stats.get('symbols_by_file', {})
    by_language = stats.get('by_language', {})

    lines = [
        "# Code Map - Class Diagram",
        "",
        "```mermaid",
        "classDiagram"
    ]

    # Track classes and their details
    all_classes = {}
    class_count = 0

    for file_path, symbols in sorted(symbols_by_file.items()):
        if class_count >= 20:
            break

        # Find classes in this file
        classes = [s for s in symbols if s.get('kind') == 'class']
        for cls in classes:
            class_name = cls.get('name', 'Unknown')

            # Skip if we already have this class
            if class_name in all_classes:
                continue

            all_classes[class_name] = {
                'file': Path(file_path).name,
                'line': cls.get('line', 0),
                'methods': [],
                'members': []
            }

            # Find methods in this class
            methods = [s for s in symbols
                      if s.get('scope') == class_name
                      and s.get('kind') in ['function', 'method']]

            # Find members/attributes
            members = [s for s in symbols
                      if s.get('scope') == class_name
                      and s.get('kind') in ['member', 'variable']]

            all_classes[class_name]['methods'] = methods[:15]
            all_classes[class_name]['members'] = members[:10]

            class_count += 1

    # Generate class definitions with details
    for class_name, details in sorted(all_classes.items()):
        lines.append(f"    class {class_name} {{")

        # Add file annotation
        lines.append(f"        <<{details['file']}>>")

        # Add members
        for member in details['members']:
            member_name = member.get('name', '')
            lines.append(f"        -{member_name}")

        # Add methods with visibility
        for method in details['methods']:
            method_name = method.get('name', '')
            # Determine visibility based on naming convention
            if method_name.startswith('_'):
                visibility = '-'  # private
            elif method_name.startswith('__'):
                visibility = '-'  # private
            else:
                visibility = '+'  # public
            lines.append(f"        {visibility}{method_name}()")

        lines.append("    }")

    # Try to detect inheritance relationships
    lines.append("")
    lines.append("    %% Inheritance relationships")
    for class_name in all_classes.keys():
        # Common base class patterns
        if 'Base' in class_name:
            # Find classes that might inherit from this
            for other_class in all_classes.keys():
                if other_class != class_name and 'Base' not in other_class:
                    if any(word in other_class for word in class_name.replace('Base', '').split()):
                        lines.append(f"    {class_name} <|-- {other_class}")

    lines.append("```")
    lines.append("")
    lines.extend([
        "## Statistics",
        "",
        f"- **Total Symbols**: {stats.get('total_symbols', 0)}",
        f"- **Files Analyzed**: {stats.get('files_analyzed', 0)}",
        f"- **Languages**: {len(by_language)}",
    ])

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"Error writing mermaid diagram: {e}", file=sys.stderr)


def generate_mermaid_pie(stats: Dict, output_file: str) -> None:
    """
    Generate a mermaid pie chart showing language distribution.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    by_language = stats.get('by_language', {})

    lines = [
        "# Code Map - Language Distribution",
        "",
        "```mermaid",
        "pie title Code Distribution by Language"
    ]

    for lang in sorted(by_language.keys()):
        count = sum(by_language[lang].values())
        lines.append(f"    \"{lang}\" : {count}")

    lines.append("```")
    lines.append("")
    lines.extend([
        "## Statistics",
        "",
        f"- **Total Symbols**: {stats.get('total_symbols', 0)}",
        f"- **Files Analyzed**: {stats.get('files_analyzed', 0)}",
        f"- **Languages**: {len(by_language)}",
    ])

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"Error writing mermaid diagram: {e}", file=sys.stderr)


def generate_mermaid_mindmap(stats: Dict, output_file: str) -> None:
    """
    Generate a mermaid mindmap showing code structure hierarchy.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    symbols_by_file = stats.get('symbols_by_file', {})
    by_language = stats.get('by_language', {})

    lines = [
        "# Code Map - Mind Map",
        "",
        "```mermaid",
        "mindmap",
        "  root((Codebase))"
    ]

    # Group by language
    for lang in sorted(by_language.keys())[:5]:  # Limit languages
        lines.append(f"    {lang}")

        # Find files for this language
        lang_files = []
        for file_path, symbols in symbols_by_file.items():
            if symbols and symbols[0].get('language') == lang:
                lang_files.append((file_path, symbols))

        # Show top files by symbol count
        lang_files.sort(key=lambda x: len(x[1]), reverse=True)
        for file_path, symbols in lang_files[:5]:  # Top 5 files per language
            file_name = Path(file_path).name
            symbol_count = len(symbols)
            lines.append(f"      {file_name} ({symbol_count})")

    lines.append("```")
    lines.append("")
    lines.extend([
        "## Statistics",
        "",
        f"- **Total Symbols**: {stats.get('total_symbols', 0)}",
        f"- **Files Analyzed**: {stats.get('files_analyzed', 0)}",
        f"- **Languages**: {len(by_language)}",
    ])

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"Error writing mermaid diagram: {e}", file=sys.stderr)


def scan_directory_structure(base_path: str, max_depth: int = 5, exclude_dirs: set = None) -> dict:
    """
    Scan filesystem directory structure to build a directory tree.

    Args:
        base_path: Root directory to scan
        max_depth: Maximum depth to scan
        exclude_dirs: Set of directory names to exclude

    Returns:
        Nested dictionary representing directory tree structure
    """
    if exclude_dirs is None:
        exclude_dirs = {
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'dist', 'build', '.pytest_cache', '.mypy_cache', 'htmlcov',
            '.tox', 'eggs', '.eggs', 'lib', 'lib64', 'parts', 'sdist',
            'var', 'wheels', '*.egg-info', '.installed.cfg', '*.egg'
        }

    tree = {}
    base_path_obj = Path(base_path)

    def scan_dir(current_path: Path, depth: int = 0):
        """Recursively scan directory and build tree."""
        if depth >= max_depth:
            return None

        # Get relative path from base
        try:
            rel_path = current_path.relative_to(base_path_obj)
            parts = list(rel_path.parts) if str(rel_path) != '.' else []
        except ValueError:
            return None

        result = {
            '__files__': {},
            '__subdirs__': {},
            '__has_code__': False
        }

        try:
            entries = list(current_path.iterdir())
        except PermissionError:
            return None

        # Check for code files in this directory
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cs', '.cpp', '.c', '.h', '.go', '.rb', '.php'}
        has_code_files = any(entry.is_file() and entry.suffix in code_extensions for entry in entries)
        result['__has_code__'] = has_code_files

        # Scan subdirectories
        for entry in entries:
            if entry.is_dir() and entry.name not in exclude_dirs:
                subdir_result = scan_dir(entry, depth + 1)
                if subdir_result and (subdir_result['__has_code__'] or subdir_result['__subdirs__']):
                    result['__subdirs__'][entry.name] = subdir_result
                    result['__has_code__'] = True  # Mark parent as having code if child has code

        return result

    root_result = scan_dir(base_path_obj, 0)
    return root_result if root_result else {'__files__': {}, '__subdirs__': {}, '__has_code__': False}


def generate_mermaid_code_flow(stats: Dict, output_file: str, theme: str = 'dark') -> None:
    """
    Generate a mermaid flowchart showing actual code execution flow with subgraphs by class/module.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
        theme: Color theme to use ('dark' or 'light', default: 'dark')
    """
    function_calls = stats.get('function_calls', {})
    all_symbols = stats.get('all_symbols', {})

    lines = [
        "# Code Map - Execution Flow (Call Graph)",
        "",
        "```mermaid",
        "%%{init: {'flowchart': {'curve': 'linear', 'defaultRenderer': 'elk', 'nodeSpacing': 100, 'rankSpacing': 100}, 'theme': 'dark'}}%%",
        "graph TD"
    ]

    # Initialize styling system
    theme_manager = ThemeManager(theme)
    node_styler = NodeStyler()

    # Initialize metadata store and node manager
    metadata_store = MetadataStore()
    label_formatter = LabelFormatter('minimal')  # Use minimal labels to reduce text size
    node_manager = NodeManager(metadata_store, label_formatter)

    # Find entry points (functions not called by others)
    called_functions = set()
    for calls in function_calls.values():
        called_functions.update(calls)

    entry_points = [func for func in function_calls.keys()
                   if func not in called_functions][:10]  # Reduced to 10 entry points

    # Collect functions using NodeManager (reduced limits for text size)
    collected_symbols = {}
    for entry in entry_points:
        if len(node_manager.processed) >= 80:  # Reduced from 150 to 80
            break
        collected = node_manager.collect_functions_recursive(
            entry,
            function_calls,
            all_symbols,
            max_depth=8,  # Reduced from 12 to 8
            max_nodes=80  # Reduced from 150 to 80
        )
        # Store collected symbols for tree organization
        for func_name in collected:
            if func_name in all_symbols:
                collected_symbols[func_name] = all_symbols[func_name]

    # Get references for backwards compatibility
    node_ids = node_manager.node_ids
    processed = node_manager.processed

    print(f"[INFO] Collected {len(collected_symbols)} functions to map")

    # Scan directory structure first
    # Determine base path - use current working directory as the project root
    base_path = Path.cwd()

    # Verify that the symbols we collected are under this base path
    # If not, find the common ancestor
    all_paths = []
    for symbol in collected_symbols.values():
        file_path = symbol.get('path', '')
        if file_path:
            abs_path = Path(file_path).resolve()
            all_paths.append(abs_path)

    if all_paths:
        # Find common ancestor of all paths
        common_parts = list(all_paths[0].parts)
        for path in all_paths[1:]:
            path_parts = list(path.parts)
            # Find where they diverge
            for i, (a, b) in enumerate(zip(common_parts, path_parts)):
                if a != b:
                    common_parts = common_parts[:i]
                    break
            else:
                # One path is prefix of another
                common_parts = common_parts[:len(path_parts)]

        if common_parts:
            base_path = Path(*common_parts)
        else:
            base_path = Path.cwd()
    else:
        base_path = Path.cwd()

    base_path_str = str(base_path)

    print(f"[INFO] Scanning directory structure from: {base_path_str}")
    dir_tree = scan_directory_structure(base_path_str, max_depth=3)

    # Now organize collected functions into the directory tree
    # Group functions by folder -> file -> class
    functions_by_folder = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for func_name, symbol in collected_symbols.items():
        file_path = symbol.get('path', '')
        scope = symbol.get('scope', '')

        if file_path:
            path_obj = Path(file_path)
            folder = str(path_obj.parent).replace('\\', '/')
            if folder == '.':
                folder = 'root'

            # Get base file name (handle compound extensions)
            base_name = path_obj.stem
            if base_name.endswith('.razor'):
                base_name = base_name[:-6]

            # Determine class/module grouping
            if scope:
                class_name = scope
            else:
                class_name = f"module_{base_name}"

            functions_by_folder[folder][base_name][class_name].append(func_name)
        else:
            functions_by_folder['root']['unknown']['global'].append(func_name)

    # Populate the scanned directory tree with collected functions
    # We need to match functions to directories in the tree
    def populate_tree_with_functions(dir_tree, functions_by_folder, base_path_str):
        """
        Populate the scanned directory tree with collected functions.

        Args:
            dir_tree: Scanned directory structure
            functions_by_folder: Collected functions grouped by folder->file->class
            base_path_str: Base path string for normalization
        """
        base_path_obj = Path(base_path_str) if base_path_str != '.' else Path.cwd()

        # For each folder with functions, find its location in the tree
        for folder_path, files_dict in functions_by_folder.items():
            # Normalize folder path
            if folder_path == 'root':
                # Functions in root go at tree root
                if '__files__' not in dir_tree:
                    dir_tree['__files__'] = {}
                dir_tree['__files__'].update(files_dict)
                continue

            # Split folder path into parts
            parts = folder_path.replace('\\', '/').split('/')

            # Navigate to the correct location in tree
            current = dir_tree
            for part in parts:
                if part == '.' or part == '':
                    continue

                # Look in subdirs
                subdirs = current.get('__subdirs__', {})
                if part in subdirs:
                    current = subdirs[part]
                else:
                    # Directory not in scanned tree, skip these functions
                    break
            else:
                # Successfully navigated to directory, add files
                if '__files__' not in current:
                    current['__files__'] = {}
                current['__files__'].update(files_dict)

        return dir_tree

    populate_tree_with_functions(dir_tree, functions_by_folder, base_path_str)
    print(f"[INFO] Populated directory tree with collected functions")

    # Generate nested subgraphs recursively
    subgraph_count = 0
    file_sg_count = 0

    def has_functions_in_tree(tree_node):
        """Check if a tree node or its children have any functions."""
        files_dict = tree_node.get('__files__', {})
        if files_dict:
            # Check if any file has any class with functions
            for file_classes in files_dict.values():
                if any(file_classes.values()):
                    return True

        # Check subdirectories
        subdirs = tree_node.get('__subdirs__', {})
        for subdir_node in subdirs.values():
            if has_functions_in_tree(subdir_node):
                return True

        return False

    def generate_nested_subgraphs(tree, depth=0, path_parts=[], skip_root=True):
        """Recursively generate nested subgraphs for directory hierarchy."""
        nonlocal subgraph_count, file_sg_count, lines

        # Handle root level specially
        if skip_root and depth == 0:
            # Process root's files and subdirs directly without creating root subgraph
            files_dict = tree.get('__files__', {})
            if files_dict:
                # Generate file subgraphs at root level
                generate_file_subgraphs(files_dict, depth)

            subdirs = tree.get('__subdirs__', {})
            generate_nested_subgraphs(subdirs, depth, path_parts, skip_root=False)
            return

        # Normal processing for non-root levels
        for dir_name in sorted(tree.keys()):
            node = tree[dir_name]

            # Skip if no functions in this branch
            if not has_functions_in_tree(node):
                continue

            files_dict = node.get('__files__', {})
            subdirs = node.get('__subdirs__', {})

            # Create subgraph for this directory
            folder_sg_id = f"SG{subgraph_count}"
            subgraph_count += 1

            indent = "    " * (depth + 1)
            display_name = f"DIR: {dir_name}"

            lines.append(f"{indent}subgraph {folder_sg_id}[\"{display_name}\"]")

            # Generate file subgraphs in this directory
            if files_dict:
                generate_file_subgraphs(files_dict, depth + 1)

            # Recursively process subdirectories
            if subdirs:
                generate_nested_subgraphs(subdirs, depth + 1, path_parts + [dir_name], skip_root=False)

            # Close directory subgraph
            indent = "    " * (depth + 1)
            lines.append(f"{indent}end")
            lines.append("")

    def generate_file_subgraphs(files_dict, depth):
        """Generate file and class subgraphs with function nodes."""
        nonlocal file_sg_count, node_ids

        # Iterate through file components in this folder
        for base_file_name, classes_dict in sorted(files_dict.items()):
            if not classes_dict:
                continue

            # Create nested file component subgraph
            file_sg_id = f"FSG{file_sg_count}"
            file_sg_count += 1

            file_indent = "    " * (depth + 1)
            lines.append(f"{file_indent}subgraph {file_sg_id}[\"FILE: {base_file_name}\"]")

            # Check if there are multiple classes - if so, create class subgraphs
            has_multiple_classes = len([c for c in classes_dict.keys() if not c.startswith('module_')]) > 1
            class_sg_count = 0

            # Add all functions from all classes in this file component
            for class_name, funcs in sorted(classes_dict.items()):
                if not funcs:
                    continue

                # If multiple classes exist and this is a real class (not module_), create class subgraph
                if has_multiple_classes and not class_name.startswith('module_'):
                    class_sg_id = f"CSG{file_sg_count}_{class_sg_count}"
                    class_sg_count += 1
                    class_display = class_name.replace('module_', '')
                    class_indent = "    " * (depth + 2)
                    lines.append(f"{class_indent}subgraph {class_sg_id}[\"CLASS: {class_display}\"]")
                    node_indent = "    " * (depth + 3)
                else:
                    node_indent = "    " * (depth + 2)

                for func_name in funcs[:50]:  # Include more functions per file
                    # Get node ID from NodeManager (already created during collection)
                    node_id = node_manager.get_node_id(func_name)
                    if not node_id:
                        continue  # Skip if node wasn't created

                    # Get label from formatter
                    symbol = collected_symbols.get(func_name, {})
                    label = label_formatter.format_function_label(func_name, symbol)

                    # Add node to diagram with minimal label
                    lines.append(f"{node_indent}{node_id}[\"{label}\"]")

                    # Metadata is already stored in metadata_store via NodeManager

                # Close class subgraph if we created one
                if has_multiple_classes and not class_name.startswith('module_'):
                    class_indent = "    " * (depth + 2)
                    lines.append(f"{class_indent}end")

            file_indent = "    " * (depth + 1)
            lines.append(f"{file_indent}end")  # Close file component subgraph

    # Start recursive generation from the tree root
    generate_nested_subgraphs(dir_tree)

    # Build node-to-color mapping based on which folder they belong to
    # Using theme manager to get color rotation
    node_to_color = {}
    color_rotation = {}  # Maps node_id to color index
    for i, (folder, files_dict) in enumerate(sorted(functions_by_folder.items())[:20]):
        color_idx = i % theme_manager.get_theme()['color_count']
        color_scheme = theme_manager.get_color_scheme(color_idx)
        edge_color = color_scheme.edge_color()

        for base_file_name, classes_dict in files_dict.items():
            for class_name, funcs in classes_dict.items():
                for func in funcs:
                    full_name = f"{class_name.replace('module_', '')}.{func}" if class_name.startswith('module_') else func
                    # Try both full name and short name
                    for potential_name in [full_name, func]:
                        if potential_name in node_ids:
                            node_to_color[node_ids[potential_name]] = edge_color
                            color_rotation[node_ids[potential_name]] = color_idx

    # Add connections with color-coded edges matching destination
    lines.append("    %% Connections")
    link_count = 0
    link_styles = []

    for func_name in processed:  # Only iterate collected functions
        if func_name not in node_ids:
            continue

        from_id = node_ids[func_name]
        calls = function_calls.get(func_name, [])
        for called_func in calls[:5]:  # Match NodeManager limit of 5 callees
            if called_func in node_ids:
                to_id = node_ids[called_func]
                edge_color = node_to_color.get(to_id, theme_manager.apply_to_edges())  # Default from theme

                lines.append(f"    {from_id} --> {to_id}")
                link_styles.append(f"    linkStyle {link_count} stroke:{edge_color},stroke-width:3px")
                link_count += 1

    lines.append("")

    # Apply link styles
    for style in link_styles:
        lines.append(style)

    lines.append("")

    # Apply theme styling
    lines.append(f"    %% Styling - {theme_manager.current_theme.capitalize()} Theme")

    # Style subgraphs with different colors from theme
    for i in range(subgraph_count):
        color_scheme = theme_manager.get_color_scheme(i)
        lines.append(f"    style SG{i} {color_scheme.to_mermaid_style()}")

    # Style file subgraphs using theme manager
    for i in range(file_sg_count):
        style = theme_manager.apply_to_subgraph('file_subgraph')
        lines.append(f"    style FSG{i} {style}")

    # Style class subgraphs using theme manager
    for i in range(file_sg_count):
        for j in range(10):  # Assume max 10 classes per file
            style = theme_manager.apply_to_subgraph('class_subgraph')
            lines.append(f"    style CSG{i}_{j} {style}")

    # Style nodes using theme manager
    for func_name, node_id in node_ids.items():
        if func_name in entry_points:
            # Entry points
            style = theme_manager.apply_to_nodes('entry_point')
            lines.append(f"    style {node_id} {style}")
        else:
            # Regular nodes
            style = theme_manager.apply_to_nodes('default')
            lines.append(f"    style {node_id} {style}")

    lines.append("```")
    lines.append("")
    lines.extend([
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

    # Validate diagram before writing
    try:
        validate_and_raise(lines)
        stats = get_diagram_stats(lines)
        print(f"[INFO] Diagram stats: {stats['node_count']} nodes, {stats['edge_count']} edges, {stats['subgraph_count']} subgraphs, {stats['text_size']} chars")
    except Exception as e:
        print(f"[ERROR] Mermaid validation failed: {e}", file=sys.stderr)
        raise

    # Store diagram stats in metadata
    metadata_store.set_stats(**stats)

    try:
        # Write diagram file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        # Write metadata JSON file alongside the diagram
        metadata_file = output_file.replace('.md', '_metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write(metadata_store.export_json(indent=2))

        print(f"[INFO] Metadata exported to: {metadata_file}")
    except Exception as e:
        print(f"Error writing mermaid diagram: {e}", file=sys.stderr)


def generate_mermaid_sequence(stats: Dict, output_file: str) -> None:
    """
    Generate a mermaid sequence diagram showing typical execution flow.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    function_calls = stats.get('function_calls', {})
    all_symbols = stats.get('all_symbols', {})
    symbols_by_file = stats.get('symbols_by_file', {})

    lines = [
        "# Code Map - Sequence Diagram",
        "",
        "```mermaid",
        "sequenceDiagram"
    ]

    # Find main entry points (common patterns)
    entry_patterns = ['main', '__init__', 'run', 'execute', 'start', 'process']
    entry_funcs = []

    for func_name in function_calls.keys():
        short_name = func_name.split('.')[-1].lower()
        if any(pattern in short_name for pattern in entry_patterns):
            entry_funcs.append(func_name)

    if not entry_funcs:
        # Fallback: find functions with most calls
        entry_funcs = sorted(function_calls.keys(),
                           key=lambda f: len(function_calls.get(f, [])),
                           reverse=True)[:3]

    # Generate sequence for first entry point
    if entry_funcs:
        entry = entry_funcs[0]
        symbol = all_symbols.get(entry, {})
        scope = symbol.get('scope', '')

        # Identify participants (classes/modules)
        participants = set()
        if scope:
            participants.add(scope)

        # Trace through calls
        def trace_calls(func, depth=0, max_depth=5):
            if depth > max_depth:
                return

            symbol = all_symbols.get(func, {})
            scope = symbol.get('scope', 'Module')
            func_short = func.split('.')[-1]

            if scope:
                participants.add(scope)

            # Add calls
            for called in function_calls.get(func, [])[:3]:  # Limit to 3 calls per function
                called_symbol = all_symbols.get(called, {})
                called_scope = called_symbol.get('scope', 'Module')
                called_short = called.split('.')[-1]

                if called_scope:
                    participants.add(called_scope)

                from_participant = scope if scope else 'Module'
                to_participant = called_scope if called_scope else 'Module'

                lines.append(f"    {from_participant}->>+{to_participant}: {called_short}()")
                trace_calls(called, depth + 1, max_depth)
                lines.append(f"    {to_participant}-->>-{from_participant}: return")

        # Add participants
        for participant in sorted(participants)[:10]:  # Limit participants
            lines.insert(3, f"    participant {participant}")

        # Trace from entry point
        entry_short = entry.split('.')[-1]
        entry_scope = all_symbols.get(entry, {}).get('scope', 'Main')
        if entry_scope:
            lines.append(f"    Note over {entry_scope}: {entry_short}() starts")
        trace_calls(entry, depth=0, max_depth=4)

    lines.append("```")
    lines.append("")
    lines.extend([
        "## Description",
        "This sequence diagram shows the typical execution flow starting from an entry point.",
        "Arrows show function calls and returns between different components.",
        "",
        f"## Entry Point",
        f"- Starting from: `{entry_funcs[0] if entry_funcs else 'N/A'}`",
    ])

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"Error writing mermaid diagram: {e}", file=sys.stderr)
