"""Mindmap diagram generator."""

from pathlib import Path
from .base_generator import BaseGenerator


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
