#!/usr/bin/env python3
"""
CtagsParser: Universal Ctags JSON Parser and Code Map Generator
===============================================================

VARIABLES AND FUNCTIONS:
- CtagsParser: Main parser class
- CodeMap: Data structure for code mapping
- format_tree_view(): Format code structure as ASCII tree
- format_symbol_table(): Format symbol table with line ranges
- get_scope_hierarchy(): Extract parent-child relationships
- filter_tags(): Filter tags by language/kind/scope
- export_to_markdown(): Export mapping as markdown

VERSION: 1.0.0
CHANGE HISTORY:
  v1.0.0 - Initial release: JSON parsing, tree visualization, filtering
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class Tag:
    """Represents a single ctags entry"""
    name: str
    path: str
    kind: str
    language: str
    line: Optional[int] = None
    end: Optional[int] = None
    scope: Optional[str] = None
    scope_kind: Optional[str] = None
    pattern: Optional[str] = None
    
    def __hash__(self):
        return hash((self.name, self.path, self.line))
    
    def __eq__(self, other):
        return (self.name == other.name and 
                self.path == other.path and 
                self.line == other.line)


@dataclass
class CodeMap:
    """Code structure mapping for a file"""
    file_path: str
    language: str
    tags: List[Tag] = field(default_factory=list)
    
    # Hierarchical structures
    functions: Dict[str, List[Tag]] = field(default_factory=dict)
    classes: Dict[str, List[Tag]] = field(default_factory=dict)
    variables: List[Tag] = field(default_factory=list)
    
    # Scope hierarchy: parent -> [children]
    hierarchy: Dict[str, List[Tag]] = field(default_factory=lambda: defaultdict(list))


class CtagsParser:
    """
    Parse and analyze Universal Ctags JSON output.
    
    Usage:
        parser = CtagsParser('tags.json')
        code_map = parser.build_code_map('src/module.py')
        print(parser.format_symbols('src/module.py'))
    """
    
    def __init__(self, tags_file: str):
        """Initialize parser with ctags JSON file"""
        self.tags_file = Path(tags_file)
        self.all_tags: List[Tag] = []
        self.tags_by_file: Dict[str, List[Tag]] = defaultdict(list)
        self.tags_by_scope: Dict[str, List[Tag]] = defaultdict(list)
        self._load_tags()
    
    def _load_tags(self):
        """Load and parse JSON lines from ctags output"""
        try:
            with open(self.tags_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        
                        # Skip pseudo-tags and non-tag entries
                        if data.get('_type') != 'tag':
                            continue
                        
                        tag = Tag(
                            name=data.get('name', ''),
                            path=data.get('path', ''),
                            kind=data.get('kind', ''),
                            language=data.get('language', ''),
                            line=data.get('line'),
                            end=data.get('end'),
                            scope=data.get('scope'),
                            scope_kind=data.get('scopeKind'),
                            pattern=data.get('pattern')
                        )
                        
                        self.all_tags.append(tag)
                        self.tags_by_file[tag.path].append(tag)
                        
                        if tag.scope:
                            self.tags_by_scope[f"{tag.path}:{tag.scope}"].append(tag)
                    
                    except json.JSONDecodeError:
                        print(f"Warning: Failed to parse line {line_num}", file=sys.stderr)
                        continue
        
        except FileNotFoundError:
            print(f"Error: Tags file '{self.tags_file}' not found", file=sys.stderr)
            sys.exit(1)
    
    def build_code_map(self, file_path: str) -> CodeMap:
        """Build hierarchical code map for a specific file"""
        tags = self.tags_by_file.get(file_path, [])
        
        if not tags:
            return CodeMap(file_path=file_path, language='Unknown')
        
        code_map = CodeMap(
            file_path=file_path,
            language=tags[0].language
        )
        code_map.tags = sorted(tags, key=lambda t: t.line or 0)
        
        # Organize by kind
        for tag in code_map.tags:
            if tag.kind in ('function', 'method'):
                code_map.functions.setdefault(tag.name, []).append(tag)
            elif tag.kind == 'class':
                code_map.classes.setdefault(tag.name, []).append(tag)
            elif tag.kind in ('variable', 'field', 'property'):
                code_map.variables.append(tag)
            
            # Build hierarchy
            if tag.scope:
                code_map.hierarchy[tag.scope].append(tag)
        
        return code_map
    
    def format_symbols(self, file_path: str, show_lines: bool = True) -> str:
        """Format symbols in a file as hierarchical ASCII tree"""
        code_map = self.build_code_map(file_path)
        
        if not code_map.tags:
            return f"No tags found for '{file_path}'"
        
        lines = [f"\n{file_path} ({code_map.language})\n{'='*60}"]
        
        # Top-level classes
        for class_name, class_tags in sorted(code_map.classes.items()):
            for tag in class_tags:
                range_str = f" [{tag.line}-{tag.end}]" if show_lines and tag.end else ""
                lines.append(f"📦 class {tag.name}{range_str}")
                
                # Methods in class
                class_members = code_map.hierarchy.get(class_name, [])
                for member in sorted(class_members, key=lambda t: t.line or 0):
                    range_str = f" [{member.line}-{member.end}]" if show_lines and member.end else ""
                    lines.append(f"  ├─ {member.kind.ljust(10)} {member.name}{range_str}")
        
        # Top-level functions
        for func_name, func_tags in sorted(code_map.functions.items()):
            for tag in func_tags:
                if tag.scope:  # Skip methods (already listed under classes)
                    continue
                range_str = f" [{tag.line}-{tag.end}]" if show_lines and tag.end else ""
                lines.append(f"⚙️  function {tag.name}{range_str}")
        
        # Module-level variables
        if code_map.variables:
            lines.append("\n📝 Module Variables:")
            for var in sorted(code_map.variables, key=lambda t: t.line or 0):
                range_str = f" [L{var.line}]" if show_lines else ""
                lines.append(f"  • {var.name}: {var.kind}{range_str}")
        
        return '\n'.join(lines)
    
    def filter_tags(self, 
                   language: Optional[str] = None,
                   kind: Optional[str] = None,
                   scope: Optional[str] = None) -> List[Tag]:
        """Filter tags by language, kind, or scope"""
        results = self.all_tags
        
        if language:
            results = [t for t in results if t.language.lower() == language.lower()]
        
        if kind:
            results = [t for t in results if t.kind.lower() == kind.lower()]
        
        if scope:
            results = [t for t in results if (t.scope and scope in t.scope)]
        
        return results
    
    def get_scope_hierarchy(self, file_path: str) -> Dict[str, List[str]]:
        """Get parent->children relationships in a file"""
        tags = self.tags_by_file.get(file_path, [])
        hierarchy = defaultdict(list)
        
        for tag in tags:
            if tag.scope:
                hierarchy[tag.scope].append(tag.name)
            else:
                hierarchy[f"{file_path} (module)"].append(tag.name)
        
        return dict(hierarchy)
    
    def get_line_range(self, file_path: str, line_num: int) -> Optional[Tag]:
        """Find which function/class contains a given line number"""
        tags = sorted(
            [t for t in self.tags_by_file.get(file_path, []) 
             if t.line and t.end],
            key=lambda t: t.line
        )
        
        for tag in tags:
            if tag.line <= line_num <= tag.end:
                return tag
        
        return None
    
    def statistics(self) -> Dict[str, any]:
        """Generate statistics about parsed code"""
        return {
            'total_tags': len(self.all_tags),
            'files': len(self.tags_by_file),
            'languages': len(set(t.language for t in self.all_tags)),
            'by_language': {
                lang: len([t for t in self.all_tags if t.language == lang])
                for lang in set(t.language for t in self.all_tags)
            },
            'by_kind': {
                kind: len([t for t in self.all_tags if t.kind == kind])
                for kind in set(t.kind for t in self.all_tags)
            }
        }
    
    def export_markdown(self, file_path: str, output_file: Optional[str] = None) -> str:
        """Export code map as markdown"""
        code_map = self.build_code_map(file_path)
        
        md = [f"# {file_path}", f"\nLanguage: **{code_map.language}**\n"]
        
        # Classes section
        if code_map.classes:
            md.append("## Classes\n")
            for class_name in sorted(code_map.classes.keys()):
                tag = code_map.classes[class_name][0]
                md.append(f"### `{class_name}` (L{tag.line}-L{tag.end})\n")
                
                members = code_map.hierarchy.get(class_name, [])
                if members:
                    md.append("| Member | Kind | Lines |\n|--------|------|-------|\n")
                    for member in sorted(members, key=lambda t: t.line or 0):
                        md.append(f"| `{member.name}` | {member.kind} | {member.line}-{member.end} |\n")
                md.append()
        
        # Functions section
        top_funcs = [t for t in code_map.functions.values() 
                    for tag in t if not tag.scope]
        if top_funcs:
            md.append("## Functions\n")
            for func_list in sorted(code_map.functions.values()):
                for func in func_list:
                    if not func.scope:
                        md.append(f"- `{func.name}(...)` (L{func.line}-L{func.end})\n")
            md.append()
        
        # Statistics
        md.append(f"## Statistics\n- Total items: {len(code_map.tags)}\n")
        
        result = ''.join(md)
        
        if output_file:
            Path(output_file).write_text(result, encoding='utf-8')
        
        return result


def main():
    """CLI interface for ctags parser"""
    if len(sys.argv) < 2:
        print("Usage: ctags_parser.py <tags.json> [command] [args]")
        print("\nCommands:")
        print("  show <file>           Show symbols in file")
        print("  filter <lang> [kind]  Filter by language and optionally kind")
        print("  stats                 Show parsing statistics")
        print("  markdown <file>       Export file as markdown")
        sys.exit(1)
    
    tags_file = sys.argv[1]
    parser = CtagsParser(tags_file)
    
    if len(sys.argv) < 3:
        print(json.dumps(parser.statistics(), indent=2))
        return
    
    command = sys.argv[2]
    
    if command == 'show' and len(sys.argv) > 3:
        print(parser.format_symbols(sys.argv[3]))
    
    elif command == 'filter':
        lang = sys.argv[3] if len(sys.argv) > 3 else None
        kind = sys.argv[4] if len(sys.argv) > 4 else None
        results = parser.filter_tags(language=lang, kind=kind)
        for tag in sorted(results, key=lambda t: (t.path, t.line or 0)):
            print(f"{tag.path}:{tag.line:5d} {tag.kind:10s} {tag.name}")
    
    elif command == 'stats':
        stats = parser.statistics()
        print(json.dumps(stats, indent=2))
    
    elif command == 'markdown' and len(sys.argv) > 3:
        md = parser.export_markdown(sys.argv[3])
        print(md)


if __name__ == '__main__':
    main()
