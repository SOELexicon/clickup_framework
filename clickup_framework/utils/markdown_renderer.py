"""
Markdown to ANSI Terminal Renderer

Converts markdown formatting to ANSI escape codes for rich terminal display.
"""

import re
from typing import List
from clickup_framework.utils.colors import colorize, TextColor, TextStyle


class MarkdownRenderer:
    """Converts markdown text to ANSI-formatted terminal output."""

    def __init__(self, colorize_output: bool = True):
        """
        Initialize the markdown renderer.

        Args:
            colorize_output: Whether to apply ANSI colors
        """
        self.colorize_output = colorize_output

    def render(self, markdown: str) -> str:
        """
        Convert markdown text to ANSI-formatted output.

        Args:
            markdown: Raw markdown text

        Returns:
            Formatted text with ANSI codes
        """
        if not markdown:
            return ""

        lines = markdown.split('\n')
        rendered_lines = []
        in_code_block = False
        code_block_lines = []
        code_lang = None

        for line in lines:
            # Handle code blocks
            if line.strip().startswith('```'):
                if not in_code_block:
                    # Starting code block
                    in_code_block = True
                    code_lang = line.strip()[3:].strip()
                    code_block_lines = []
                else:
                    # Ending code block
                    in_code_block = False
                    rendered_lines.extend(self._render_code_block(code_block_lines, code_lang))
                    code_block_lines = []
                    code_lang = None
                continue

            if in_code_block:
                code_block_lines.append(line)
                continue

            # Render regular line
            rendered_line = self._render_line(line)
            rendered_lines.append(rendered_line)

        return '\n'.join(rendered_lines)

    def _render_line(self, line: str) -> str:
        """Render a single line of markdown."""
        if not line.strip():
            return line

        # Headers
        if line.startswith('#'):
            return self._render_header(line)

        # Lists
        if re.match(r'^\s*[-*+]\s', line):
            return self._render_list_item(line)

        # Numbered lists
        if re.match(r'^\s*\d+\.\s', line):
            return self._render_numbered_list_item(line)

        # Blockquote
        if line.strip().startswith('>'):
            return self._render_blockquote(line)

        # Horizontal rule
        if re.match(r'^\s*[-*_]{3,}\s*$', line):
            return self._render_horizontal_rule()

        # Regular paragraph - apply inline formatting
        return self._render_inline_formatting(line)

    def _render_header(self, line: str) -> str:
        """Render markdown headers."""
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if not match:
            return line

        level = len(match.group(1))
        text = match.group(2)

        # Apply formatting based on header level
        if self.colorize_output:
            if level == 1:
                formatted = colorize(text, TextColor.BRIGHT_CYAN, TextStyle.BOLD)
                return f"\n{formatted}"
            elif level == 2:
                formatted = colorize(text, TextColor.CYAN, TextStyle.BOLD)
                return f"\n{formatted}"
            elif level == 3:
                formatted = colorize(text, TextColor.BRIGHT_BLUE, TextStyle.BOLD)
                return formatted
            else:
                formatted = colorize(text, TextColor.BLUE, TextStyle.BOLD)
                return formatted
        else:
            return text

    def _render_list_item(self, line: str) -> str:
        """Render bulleted list items."""
        match = re.match(r'^(\s*)([-*+])\s+(.+)$', line)
        if not match:
            return line

        indent = match.group(1)
        content = match.group(3)

        # Apply inline formatting to content
        formatted_content = self._render_inline_formatting(content)

        if self.colorize_output:
            bullet = colorize('•', TextColor.BRIGHT_YELLOW)
            return f"{indent}{bullet} {formatted_content}"
        else:
            return f"{indent}• {formatted_content}"

    def _render_numbered_list_item(self, line: str) -> str:
        """Render numbered list items."""
        match = re.match(r'^(\s*)(\d+)\.\s+(.+)$', line)
        if not match:
            return line

        indent = match.group(1)
        number = match.group(2)
        content = match.group(3)

        # Apply inline formatting to content
        formatted_content = self._render_inline_formatting(content)

        if self.colorize_output:
            num = colorize(f"{number}.", TextColor.BRIGHT_YELLOW)
            return f"{indent}{num} {formatted_content}"
        else:
            return f"{indent}{number}. {formatted_content}"

    def _render_blockquote(self, line: str) -> str:
        """Render blockquotes."""
        match = re.match(r'^(\s*)>\s*(.*)$', line)
        if not match:
            return line

        indent = match.group(1)
        content = match.group(2)

        formatted_content = self._render_inline_formatting(content)

        if self.colorize_output:
            bar = colorize('▌', TextColor.BRIGHT_BLACK)
            formatted_content = colorize(formatted_content, TextColor.BRIGHT_BLACK, TextStyle.ITALIC)
            return f"{indent}{bar} {formatted_content}"
        else:
            return f"{indent}│ {formatted_content}"

    def _render_horizontal_rule(self) -> str:
        """Render horizontal rules."""
        if self.colorize_output:
            return colorize('─' * 60, TextColor.BRIGHT_BLACK)
        else:
            return '─' * 60

    def _render_inline_formatting(self, text: str) -> str:
        """Apply inline markdown formatting (bold, italic, code, links)."""
        if not self.colorize_output:
            return text

        # Code spans (must come before bold/italic to avoid conflicts)
        text = re.sub(
            r'`([^`]+)`',
            lambda m: colorize(m.group(1), TextColor.BRIGHT_GREEN),
            text
        )

        # Bold and italic ***text***
        text = re.sub(
            r'\*\*\*([^*]+)\*\*\*',
            lambda m: colorize(m.group(1), TextColor.BRIGHT_WHITE, TextStyle.BOLD),
            text
        )

        # Bold **text** or __text__
        text = re.sub(
            r'\*\*([^*]+)\*\*',
            lambda m: colorize(m.group(1), TextColor.BRIGHT_WHITE, TextStyle.BOLD),
            text
        )
        text = re.sub(
            r'__([^_]+)__',
            lambda m: colorize(m.group(1), TextColor.BRIGHT_WHITE, TextStyle.BOLD),
            text
        )

        # Italic *text* or _text_
        text = re.sub(
            r'\*([^*]+)\*',
            lambda m: colorize(m.group(1), TextColor.YELLOW, TextStyle.ITALIC),
            text
        )
        text = re.sub(
            r'_([^_]+)_',
            lambda m: colorize(m.group(1), TextColor.YELLOW, TextStyle.ITALIC),
            text
        )

        # Links [text](url)
        text = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            lambda m: f"{colorize(m.group(1), TextColor.BRIGHT_BLUE, TextStyle.UNDERLINE)} {colorize(f'({m.group(2)})', TextColor.BRIGHT_BLACK)}",
            text
        )

        # Strikethrough ~~text~~ (use dim color since ANSI strikethrough isn't widely supported)
        text = re.sub(
            r'~~([^~]+)~~',
            lambda m: colorize(m.group(1), TextColor.BRIGHT_BLACK, TextStyle.DIM),
            text
        )

        return text

    def _render_code_block(self, lines: List[str], lang: str = None) -> List[str]:
        """Render code blocks."""
        if not lines:
            return []

        rendered = []

        # Add language label if provided
        if lang and self.colorize_output:
            label = colorize(f"[{lang}]", TextColor.BRIGHT_BLACK)
            rendered.append(f"  {label}")

        # Render code lines with syntax coloring
        for line in lines:
            if self.colorize_output:
                # Simple syntax highlighting for common patterns
                colored_line = self._apply_simple_syntax_highlighting(line, lang)
                rendered.append(f"  {colorize(colored_line, TextColor.GREEN)}")
            else:
                rendered.append(f"  {line}")

        return rendered

    def _apply_simple_syntax_highlighting(self, line: str, lang: str = None) -> str:
        """Apply basic syntax highlighting to code."""
        # For now, just return the line as-is
        # Could be extended with language-specific highlighting
        return line


def render_markdown(text: str, colorize_output: bool = True) -> str:
    """
    Convenience function to render markdown text.

    Args:
        text: Markdown text to render
        colorize_output: Whether to apply ANSI colors

    Returns:
        Formatted text with ANSI codes
    """
    renderer = MarkdownRenderer(colorize_output)
    return renderer.render(text)
