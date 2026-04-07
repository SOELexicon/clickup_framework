"""
ASCII table formatter for displaying line count analysis results.

This module formats line count data into professional ASCII tables with
optional color support and statistical summaries for terminal output.

Variables:    None
Classes:      ConsoleFormatter
"""

from typing import Dict, Any, Optional
from pathlib import Path
from clickup_framework.utils.colors import colorize, TextColor
from .stats_calculator import StatsCalculator


class ConsoleFormatter:
    """
    Format line count data into professional ASCII tables with statistics.

    Purpose:    Display line count results in formatted ASCII table with colors
    Usage:      Create instance, call format_top_files() or format_summary_stats()
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: console ASCII table formatter
    """

    # Box-drawing characters for ASCII table
    CORNER_TOP_LEFT = '╔'
    CORNER_TOP_RIGHT = '╗'
    CORNER_BOTTOM_LEFT = '╚'
    CORNER_BOTTOM_RIGHT = '╝'
    HORIZONTAL = '═'
    VERTICAL = '║'
    T_DOWN = '╦'
    T_UP = '╩'
    T_RIGHT = '╠'
    T_LEFT = '╣'
    CROSS = '╬'

    def __init__(self, terminal_width: int = 120):
        """
        Initialize ConsoleFormatter.

        Args:
            terminal_width: Width of terminal in characters (default: 120)
        """
        self.terminal_width = max(terminal_width, 80)

    def format_top_files(self, loc_data: Dict[str, Dict[str, Any]],
                        limit: int = 20,
                        use_color: bool = True) -> str:
        """
        Format top N files sorted by line count as ASCII table.

        Creates a professional table with columns: Rank, Filename, Lines,
        % of Total, and Language. Supports color coding and handles varying
        file counts gracefully (shows all if fewer than limit).

        Args:
            loc_data: Dictionary mapping file paths to line count data
            limit: Maximum number of files to show (default: 20)
            use_color: Whether to use ANSI color codes (default: True)

        Returns:
            Formatted ASCII table as a string, ready for terminal output
        """
        if not loc_data:
            return self._empty_table(use_color)

        total_lines = StatsCalculator.total_lines(loc_data)
        if total_lines == 0:
            return self._empty_table(use_color)

        # Sort files by total lines descending and take top N
        sorted_files = sorted(loc_data.items(),
                            key=lambda x: x[1].get('total', 0),
                            reverse=True)
        top_files = sorted_files[:limit]

        # Build table rows
        rows = []
        for rank, (file_path, info) in enumerate(top_files, 1):
            total = info.get('total', 0)
            percentage = (total / total_lines * 100) if total_lines > 0 else 0
            language = info.get('language', 'Unknown')
            filename = Path(file_path).name

            rows.append({
                'rank': str(rank),
                'filename': filename,
                'lines': self._format_number(total),
                'percentage': f'{percentage:.1f}%',
                'language': language,
            })

        return self._render_table(rows, use_color)

    def format_summary_stats(self, loc_data: Dict[str, Dict[str, Any]],
                            use_color: bool = True) -> str:
        """
        Format summary statistics header with aggregated metrics.

        Includes total lines, total files, average file size, language breakdown,
        and percentile analysis for a comprehensive overview.

        Args:
            loc_data: Dictionary mapping file paths to line count data
            use_color: Whether to use ANSI color codes (default: True)

        Returns:
            Formatted statistics summary as a string
        """
        total_lines = StatsCalculator.total_lines(loc_data)
        total_files = StatsCalculator.total_files(loc_data)
        avg_size = StatsCalculator.average_file_size(loc_data)
        lang_breakdown = StatsCalculator.lines_by_language(loc_data)
        percentiles = StatsCalculator.percentile_analysis(loc_data)

        lines = []

        # Header
        header = 'LINE COUNT ANALYSIS SUMMARY'
        if use_color:
            header = colorize(header, TextColor.BRIGHT_CYAN)
        lines.append(header)
        lines.append('')

        # Total metrics
        total_str = f'Total Lines: {self._format_number(total_lines)}'
        files_str = f'Total Files: {total_files}'
        avg_str = f'Average per File: {avg_size:.1f}'
        if use_color:
            total_str = f'Total Lines: {colorize(self._format_number(total_lines), TextColor.BRIGHT_YELLOW)}'
            files_str = f'Total Files: {colorize(str(total_files), TextColor.BRIGHT_YELLOW)}'
            avg_str = f'Average per File: {colorize(f"{avg_size:.1f}", TextColor.BRIGHT_YELLOW)}'

        lines.append(total_str)
        lines.append(files_str)
        lines.append(avg_str)
        lines.append('')

        # Language breakdown
        if lang_breakdown:
            breakdown_label = 'Lines by Language:'
            if use_color:
                breakdown_label = colorize(breakdown_label, TextColor.BRIGHT_CYAN)
            lines.append(breakdown_label)

            for language, count in lang_breakdown.items():
                percentage = (count / total_lines * 100) if total_lines > 0 else 0
                count_str = self._format_number(count)
                pct_str = f'{percentage:>5.1f}%'
                lang_line = f'  {language:15} {count_str:>10} ({pct_str})'
                if use_color:
                    colored_count = colorize(count_str, TextColor.BRIGHT_YELLOW)
                    colored_pct = colorize(pct_str, TextColor.BRIGHT_GREEN)
                    lang_line = f'  {language:15} {colored_count:>10} ({colored_pct})'
                lines.append(lang_line)
            lines.append('')

        # Percentiles
        if any(percentiles.values()):
            perc_label = 'Size Distribution:'
            if use_color:
                perc_label = colorize(perc_label, TextColor.BRIGHT_CYAN)
            lines.append(perc_label)

            for percentile in ['p50', 'p75', 'p90', 'p95', 'p99']:
                value = percentiles.get(percentile, 0)
                value_str = self._format_number(int(value))
                perc_line = f'  {percentile.upper():4} {value_str:>10} lines'
                if use_color:
                    colored_val = colorize(value_str, TextColor.BRIGHT_YELLOW)
                    perc_line = f'  {percentile.upper():4} {colored_val:>10} lines'
                lines.append(perc_line)

        return '\n'.join(lines)

    def _render_table(self, rows: list, use_color: bool) -> str:
        """
        Render rows as ASCII box table with proper alignment.

        Args:
            rows: List of dictionaries with 'rank', 'filename', 'lines',
                  'percentage', 'language' keys
            use_color: Whether to apply color formatting

        Returns:
            Formatted table as string
        """
        if not rows:
            return self._empty_table(use_color)

        # Column widths (rank=6, filename varies, lines=10, %=8, language=12)
        rank_width = 6
        lines_width = 10
        pct_width = 8
        lang_width = 12
        filename_width = max(20, self.terminal_width - rank_width - lines_width -
                            pct_width - lang_width - 12)  # -12 for separators

        # Build header
        header_parts = [
            self._pad_right('Rank', rank_width),
            self._pad_right('Filename', filename_width),
            self._pad_right('Lines', lines_width),
            self._pad_right('%', pct_width),
            self._pad_right('Language', lang_width),
        ]

        header_line = self.VERTICAL + self.VERTICAL.join(header_parts) + self.VERTICAL

        # Apply color to header
        if use_color:
            header_line = colorize(header_line, TextColor.BRIGHT_CYAN)

        # Build separator line
        separators = [
            self.HORIZONTAL * rank_width,
            self.HORIZONTAL * filename_width,
            self.HORIZONTAL * lines_width,
            self.HORIZONTAL * pct_width,
            self.HORIZONTAL * lang_width,
        ]
        sep_line = self.T_RIGHT + self.CROSS.join(separators) + self.T_LEFT

        # Build top border
        top_parts = [
            self.HORIZONTAL * rank_width,
            self.HORIZONTAL * filename_width,
            self.HORIZONTAL * lines_width,
            self.HORIZONTAL * pct_width,
            self.HORIZONTAL * lang_width,
        ]
        top_border = (self.CORNER_TOP_LEFT +
                     self.T_DOWN.join(top_parts) +
                     self.CORNER_TOP_RIGHT)

        # Build bottom border
        bottom_parts = [
            self.HORIZONTAL * rank_width,
            self.HORIZONTAL * filename_width,
            self.HORIZONTAL * lines_width,
            self.HORIZONTAL * pct_width,
            self.HORIZONTAL * lang_width,
        ]
        bottom_border = (self.CORNER_BOTTOM_LEFT +
                        self.T_UP.join(bottom_parts) +
                        self.CORNER_BOTTOM_RIGHT)

        # Build data rows
        table_lines = [top_border, header_line, sep_line]

        for row in rows:
            rank_str = self._pad_right(row['rank'], rank_width)
            filename_str = self._pad_right(row['filename'], filename_width)
            lines_str = self._pad_left(row['lines'], lines_width)
            pct_str = self._pad_left(row['percentage'], pct_width)
            lang_str = self._pad_right(row['language'], lang_width)

            # Apply color to data cells
            if use_color:
                filename_str = colorize(filename_str, TextColor.BRIGHT_GREEN)
                lines_str = colorize(lines_str, TextColor.BRIGHT_YELLOW)
                pct_str = colorize(pct_str, TextColor.BRIGHT_YELLOW)

            row_line = (self.VERTICAL +
                       rank_str + self.VERTICAL +
                       filename_str + self.VERTICAL +
                       lines_str + self.VERTICAL +
                       pct_str + self.VERTICAL +
                       lang_str + self.VERTICAL)

            table_lines.append(row_line)

        table_lines.append(bottom_border)

        return '\n'.join(table_lines)

    def _empty_table(self, use_color: bool) -> str:
        """
        Create empty table message when no data available.

        Args:
            use_color: Whether to apply color formatting

        Returns:
            Message indicating no data available
        """
        msg = 'No files found in the specified directory.'
        if use_color:
            msg = colorize(msg, TextColor.BRIGHT_BLACK)
        return msg

    @staticmethod
    def _format_number(num: int) -> str:
        """
        Format number with thousands separators.

        Args:
            num: Integer to format

        Returns:
            Formatted string with commas (e.g., '1,234,567')
        """
        return f'{num:,}'

    @staticmethod
    def _pad_left(text: str, width: int) -> str:
        """
        Left-pad text to specified width.

        Args:
            text: Text to pad
            width: Total width desired

        Returns:
            Padded text, right-aligned
        """
        return str(text).rjust(width)

    @staticmethod
    def _pad_right(text: str, width: int) -> str:
        """
        Right-pad text to specified width.

        Args:
            text: Text to pad
            width: Total width desired

        Returns:
            Padded text, left-aligned
        """
        return str(text).ljust(width)
