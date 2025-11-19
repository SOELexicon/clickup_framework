"""Mermaid diagram generators for code maps."""

import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict


def generate_mermaid_flowchart(stats: Dict, output_file: str) -> None:
    """
    Generate a mermaid flowchart diagram showing directory structure with symbol details.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
    """
    symbols_by_file = stats.get('symbols_by_file', {})
    by_language = stats.get('by_language', {})

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
        lines.append(f"    style {dir_id} fill:#1e3a8a,stroke:#60a5fa,stroke-width:3px")

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
                    lines.append(f"    style {cls_id} fill:#065f46,stroke:#34d399")
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


def generate_mermaid_code_flow(stats: Dict, output_file: str) -> None:
    """
    Generate a mermaid flowchart showing actual code execution flow with subgraphs by class/module.

    Args:
        stats: Statistics dictionary from parse_tags_file
        output_file: Output markdown file path
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

    # Find entry points (functions not called by others)
    called_functions = set()
    for calls in function_calls.values():
        called_functions.update(calls)

    entry_points = [func for func in function_calls.keys()
                   if func not in called_functions][:15]  # Even more entry points

    # Group functions by folder/directory
    functions_by_folder = defaultdict(lambda: defaultdict(list))  # folder -> class -> [functions]
    processed = set()
    node_count = 0
    node_ids = {}  # Map func_name to node_id

    def collect_functions(func_name, depth=0, max_depth=8):
        nonlocal node_count

        if depth > max_depth or func_name in processed or node_count >= 50:
            return

        processed.add(func_name)
        symbol = all_symbols.get(func_name, {})
        scope = symbol.get('scope', '')

        # Get folder path from file path
        file_path = symbol.get('path', '')
        if file_path:
            folder = str(Path(file_path).parent)
            # Normalize path separators and handle current directory
            folder = folder.replace('\\', '/').replace('.', 'root')
        else:
            folder = 'root'

        # Group by folder, then by class or module
        if scope:
            functions_by_folder[folder][scope].append(func_name)
        else:
            # Use file as grouping if no class
            file_name = Path(symbol.get('path', 'global')).stem
            functions_by_folder[folder][f"module_{file_name}"].append(func_name)

        node_count += 1

        # Recursively collect called functions
        calls = function_calls.get(func_name, [])
        for called_func in calls[:3]:  # Limit calls per function for clarity
            if called_func not in processed:
                collect_functions(called_func, depth + 1, max_depth)

    # Collect all functions starting from entry points
    for entry in entry_points:
        if node_count >= 50:
            break
        collect_functions(entry, depth=0, max_depth=8)

    # Transform folder->class into folder->file_component->class for grouping related files
    def group_by_file_components(functions_by_folder, all_symbols):
        """Group related files (e.g., Component.razor + Component.razor.cs) together."""
        file_components = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        # Result: file_components[folder][base_file_name][class_name] = [functions]

        for folder, classes_dict in functions_by_folder.items():
            for class_name, funcs in classes_dict.items():
                for func_name in funcs:
                    symbol = all_symbols.get(func_name, {})
                    file_path = symbol.get('path', '')

                    if file_path:
                        path_obj = Path(file_path)
                        base_name = path_obj.stem

                        # Handle compound extensions: Component.razor.cs -> Component
                        if base_name.endswith('.razor'):
                            base_name = base_name[:-6]

                        # Group by base file name
                        file_components[folder][base_name][class_name].append(func_name)
                    else:
                        # Fallback for functions without file path
                        file_components[folder]['unknown'][class_name].append(func_name)

        return file_components

    file_components = group_by_file_components(functions_by_folder, all_symbols)

    # Generate subgraphs for each folder with nested file components
    subgraph_count = 0
    file_sg_count = 0

    for folder, files_dict in sorted(file_components.items())[:20]:  # Limit folders
        if not files_dict:
            continue

        folder_sg_id = f"SG{subgraph_count}"
        subgraph_count += 1

        # Clean folder name for display
        display_folder = folder.replace('root', '📁 .').replace('/', ' / ')
        if not display_folder.startswith('📁'):
            display_folder = f"📁 {display_folder}"

        # Start folder subgraph
        lines.append(f"    subgraph {folder_sg_id}[\"{display_folder}\"]")

        # Iterate through file components in this folder
        for base_file_name, classes_dict in sorted(files_dict.items()):
            if not classes_dict:
                continue

            # Create nested file component subgraph
            file_sg_id = f"FSG{file_sg_count}"
            file_sg_count += 1

            lines.append(f"        subgraph {file_sg_id}[\"📄 {base_file_name}\"]")

            # Add all functions from all classes in this file component
            for class_name, funcs in sorted(classes_dict.items()):
                if not funcs:
                    continue

                for func_name in funcs[:15]:  # Limit functions
                    symbol = all_symbols.get(func_name, {})
                    node_id = f"N{len(node_ids)}"
                    node_ids[func_name] = node_id

                    display_func = func_name.split('.')[-1]
                    file_name = Path(symbol.get('path', '')).name
                    line_start = symbol.get('line', 0)
                    line_end = symbol.get('end', line_start)

                    # Show class/module in node if available
                    class_display = class_name.replace('module_', '')

                    # Create node with class, file, and line numbers (file also shown in subgraph title for context)
                    lines.append(f"            {node_id}[\"{display_func}()<br/>🔧 {class_display}<br/>📄 {file_name}<br/>📍 L{line_start}-{line_end}\"]")

            lines.append("        end")  # Close file component subgraph

        lines.append("    end")  # Close folder subgraph
        lines.append("")

    # Define colors for subgraphs and edges (using very dark shades for subtle backgrounds)
    colors = [
        ("fill:#0d1f1a,stroke:#10b981,color:#10b981,stroke-width:2px", "#10b981", "emerald"),  # Very dark emerald
        ("fill:#1a1625,stroke:#8b5cf6,color:#8b5cf6,stroke-width:2px", "#8b5cf6", "purple"),   # Very dark purple
        ("fill:#0c1c20,stroke:#06b6d4,color:#06b6d4,stroke-width:2px", "#06b6d4", "cyan"),     # Very dark cyan
        ("fill:#211a0d,stroke:#f59e0b,color:#f59e0b,stroke-width:2px", "#f59e0b", "amber"),    # Very dark amber
        ("fill:#1f0d18,stroke:#ec4899,color:#ec4899,stroke-width:2px", "#ec4899", "pink"),     # Very dark pink
    ]

    # Build node-to-color mapping based on which folder they belong to
    node_to_color = {}
    for i, (folder, files_dict) in enumerate(sorted(file_components.items())[:20]):
        _, edge_color, _ = colors[i % len(colors)]
        for base_file_name, classes_dict in files_dict.items():
            for class_name, funcs in classes_dict.items():
                for func in funcs:
                    full_name = f"{class_name.replace('module_', '')}.{func}" if class_name.startswith('module_') else func
                    # Try both full name and short name
                    for potential_name in [full_name, func]:
                        if potential_name in node_ids:
                            node_to_color[node_ids[potential_name]] = edge_color

    # Add connections with color-coded edges matching destination
    lines.append("    %% Connections")
    link_count = 0
    link_styles = []

    for func_name, calls in function_calls.items():
        if func_name not in node_ids:
            continue

        from_id = node_ids[func_name]
        for called_func in calls[:3]:  # Limit to 3 calls per function for clarity
            if called_func in node_ids:
                to_id = node_ids[called_func]
                edge_color = node_to_color.get(to_id, '#10b981')  # Default to green

                lines.append(f"    {from_id} --> {to_id}")
                link_styles.append(f"    linkStyle {link_count} stroke:{edge_color},stroke-width:3px")
                link_count += 1

    lines.append("")

    # Apply link styles
    for style in link_styles:
        lines.append(style)

    lines.append("")

    # Apply green/black/purple theme styling
    lines.append("    %% Styling - Green/Black/Purple Theme")

    # Style subgraphs with different faded colors
    for i in range(subgraph_count):
        color_style, _, _ = colors[i % len(colors)]
        lines.append(f"    style SG{i} {color_style}")

    # Style nodes with subtle backgrounds
    for func_name, node_id in node_ids.items():
        if func_name in entry_points:
            # Entry points - subtle purple with glow border
            lines.append(f"    style {node_id} fill:#1a1625,stroke:#8b5cf6,stroke-width:3px,color:#a855f7")
        else:
            # Regular nodes - very dark with green border
            lines.append(f"    style {node_id} fill:#0a0a0a,stroke:#10b981,stroke-width:2px,color:#10b981")

    lines.append("```")
    lines.append("")
    lines.extend([
        "## Legend",
        "- 🟣 **Purple nodes**: Entry points (functions not called by others)",
        "- 🟢 **Green-bordered nodes**: Called functions",
        "- **Folder Subgraphs**: Group by directory",
        "- **File Subgraphs**: Group related files (e.g., Component.razor + Component.razor.cs)",
        "- **Line numbers**: Show start-end lines in source file",
        "",
        f"## Statistics",
        f"- **Total Functions Mapped**: {len(processed)}",
        f"- **Folders**: {len(file_components)}",
        f"- **File Components**: {sum(len(files) for files in file_components.values())}",
        f"- **Classes/Modules**: {sum(sum(len(classes) for classes in files.values()) for files in file_components.values())}",
        f"- **Total Call Relationships**: {sum(len(calls) for calls in function_calls.values())}",
        f"- **Entry Points Found**: {len(entry_points)}",
    ])

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
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
