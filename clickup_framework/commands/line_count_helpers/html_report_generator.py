"""
Professional HTML report generator for line count analysis with embedded styling.

Generates a single self-contained HTML file with dark theme, responsive layout,
interactive tabs, sortable tables, and SVG-based charts. All CSS, JavaScript,
and data are embedded within the HTML document for portability.

Variables:    DARK_THEME_COLORS
Classes:      HTMLReportGenerator
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import math
from .stats_calculator import StatsCalculator


DARK_THEME_COLORS = {
    'background': '#1a1a1a',
    'surface': '#242424',
    'text': '#e0e0e0',
    'text_muted': '#a0a0a0',
    'primary': '#4CAF50',
    'secondary': '#2196F3',
    'highlight': '#FF9800',
    'border': '#3a3a3a',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'error': '#F44336',
}


class ChartConfig:
    """SVG chart dimension and styling constants."""
    # Pie chart
    PIE_CENTER_X = 200
    PIE_CENTER_Y = 200
    PIE_RADIUS = 150

    # Bar chart
    BAR_HEIGHT = 30
    BAR_SPACING = 5
    BAR_LEFT_MARGIN = 150
    BAR_MAX_WIDTH = 600

    # Histogram
    HIST_BAR_WIDTH = 60
    HIST_BAR_SPACING = 20
    HIST_MAX_HEIGHT = 250
    HIST_LEFT_MARGIN = 80
    HIST_BASE_Y = 300
    HIST_LABEL_Y = 320


class HTMLReportGenerator:
    """
    Generate professional HTML reports for line count analysis.

    Purpose:    Create self-contained HTML reports with charts, tables, and stats
    Usage:      Call generate_report() with loc_data dict and optional output path
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: dark-themed HTML report generator with SVG charts
    """

    # Chart color palette for SVG visualizations
    CHART_COLORS = ['#4CAF50', '#2196F3', '#FF9800', '#F44336', '#9C27B0',
                    '#00BCD4', '#FFEB3B', '#795548', '#E91E63', '#607D8B']

    def __init__(self, theme_colors: Optional[Dict[str, str]] = None):
        """
        Initialize HTMLReportGenerator.

        Args:
            theme_colors: Optional color theme dict (defaults to DARK_THEME_COLORS)
        """
        self.colors = theme_colors or DARK_THEME_COLORS

    def generate_report(
        self,
        loc_data: Dict[str, Dict[str, Any]],
        output_path: Optional[Path] = None,
        project_name: str = ""
    ) -> Path:
        """
        Generate a professional HTML report from line count data.

        Creates a self-contained HTML file with embedded CSS and JavaScript,
        featuring tabs, interactive tables, sortable columns, and SVG charts.
        All resources (CSS, JS, charts) are embedded; no external dependencies.

        Args:
            loc_data: Dictionary mapping file paths to line count data
                      {
                          'path/to/file.py': {
                              'total': 100,
                              'blank': 20,
                              'comment': 15,
                              'code': 65,
                              'language': 'Python'
                          },
                          ...
                      }
            output_path: Directory to write HTML file (default: current directory)
            project_name: Optional project name for report title

        Returns:
            Path to the generated HTML file
        """
        if output_path is None:
            output_path = Path.cwd()
        else:
            output_path = Path(output_path)

        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f'line-count-report-{timestamp}.html'
        report_path = output_path / filename

        # Calculate statistics
        total_files = StatsCalculator.total_files(loc_data)
        total_lines = StatsCalculator.total_lines(loc_data)
        avg_file_size = StatsCalculator.average_file_size(loc_data)
        lines_by_lang = StatsCalculator.lines_by_language(loc_data)
        percentiles = StatsCalculator.percentile_analysis(loc_data)

        # Prepare data for JavaScript
        files_data = self._prepare_files_data(loc_data, total_lines)
        lang_stats = self._prepare_language_stats(loc_data, lines_by_lang, total_lines)

        # Build HTML document
        html_content = self._build_html(
            project_name=project_name,
            loc_data=loc_data,
            files_data=files_data,
            lang_stats=lang_stats,
            total_files=total_files,
            total_lines=total_lines,
            avg_file_size=avg_file_size,
            lines_by_lang=lines_by_lang,
            percentiles=percentiles,
            generated_at=datetime.now()
        )

        # Write to file
        report_path.write_text(html_content, encoding='utf-8')
        return report_path

    def _prepare_files_data(
        self,
        loc_data: Dict[str, Dict[str, Any]],
        total_lines: int
    ) -> list:
        """
        Prepare file data for JavaScript table.

        Args:
            loc_data: Original line count data
            total_lines: Total lines across all files (for percentage calculations)

        Returns:
            List of dicts ready for JavaScript processing
        """
        files = []

        for file_path, info in loc_data.items():
            total = info.get('total', 0)
            percentage = (total / total_lines * 100) if total_lines > 0 else 0
            ext = Path(file_path).suffix or 'no-ext'
            files.append({
                'path': str(file_path),
                'filename': Path(file_path).name,
                'extension': ext.lstrip('.'),
                'total': total,
                'blank': info.get('blank', 0),
                'comment': info.get('comment', 0),
                'code': info.get('code', 0),
                'language': info.get('language', 'Unknown'),
                'percentage': round(percentage, 2),
            })

        # Sort by total lines descending
        return sorted(files, key=lambda x: x['total'], reverse=True)

    def _prepare_language_stats(
        self,
        loc_data: Dict[str, Dict[str, Any]],
        lines_by_lang: Dict[str, int],
        total_lines: int
    ) -> list:
        """
        Prepare language statistics for table and charts.

        Args:
            loc_data: Original line count data
            lines_by_lang: Lines aggregated by language
            total_lines: Total lines across all files (for percentage calculations)

        Returns:
            List of dicts with language statistics
        """
        lang_stats = []

        # Aggregate language statistics in single nested dict
        lang_data = {}
        for info in loc_data.values():
            lang = info.get('language', 'Unknown')
            if lang not in lang_data:
                lang_data[lang] = {
                    'files': 0,
                    'blank': 0,
                    'comment': 0,
                    'code': 0
                }
            lang_data[lang]['files'] += 1
            lang_data[lang]['blank'] += info.get('blank', 0)
            lang_data[lang]['comment'] += info.get('comment', 0)
            lang_data[lang]['code'] += info.get('code', 0)

        # Build stats list
        for language, total in lines_by_lang.items():
            stats = lang_data.get(language, {'files': 0, 'blank': 0, 'comment': 0, 'code': 0})
            file_count = stats['files']
            avg_per_file = (total / file_count) if file_count > 0 else 0
            percentage = (total / total_lines * 100) if total_lines > 0 else 0

            lang_stats.append({
                'language': language,
                'files': file_count,
                'total': total,
                'average': round(avg_per_file, 1),
                'percentage': round(percentage, 2),
                'blank': stats['blank'],
                'comment': stats['comment'],
                'code': stats['code'],
            })

        return lang_stats

    def _build_html(
        self,
        project_name: str,
        loc_data: Dict[str, Dict[str, Any]],
        files_data: list,
        lang_stats: list,
        total_files: int,
        total_lines: int,
        avg_file_size: float,
        lines_by_lang: Dict[str, int],
        percentiles: Dict[str, float],
        generated_at: datetime
    ) -> str:
        """
        Build the complete HTML document.

        Args:
            project_name: Project name for title
            loc_data: Original line count data
            files_data: Prepared files data
            lang_stats: Prepared language statistics
            total_files: Total file count
            total_lines: Total line count
            avg_file_size: Average file size
            lines_by_lang: Lines by language dict
            percentiles: Percentile analysis dict
            generated_at: Timestamp of generation

        Returns:
            Complete HTML as string
        """
        # Escape strings for JavaScript
        project_title = self._escape_html(project_name or "Line Count Report")
        timestamp_str = generated_at.strftime('%Y-%m-%d %H:%M:%S')

        # Prepare chart data
        lang_names = list(lines_by_lang.keys())[:10]  # Top 10
        lang_values = [lines_by_lang[lang] for lang in lang_names]

        # Top 10 files for bar chart
        top_files = files_data[:10]
        top_filenames = [f['filename'] for f in top_files]
        top_file_lines = [f['total'] for f in top_files]

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_title}</title>
    <style>
{self._build_css()}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="header-content">
                <h1>{project_title}</h1>
                <p class="subtitle">Generated on {timestamp_str}</p>
            </div>
        </header>

        <nav class="nav-tabs">
            <button class="tab-button active" data-tab="overview">Overview</button>
            <button class="tab-button" data-tab="files">Files</button>
            <button class="tab-button" data-tab="languages">Languages</button>
            <button class="tab-button" data-tab="statistics">Statistics</button>
        </nav>

        <main class="main-content">
            <!-- Overview Tab -->
            <div id="overview" class="tab-content active">
                <div class="summary-cards">
                    <div class="card">
                        <div class="card-value">{total_files}</div>
                        <div class="card-label">Total Files</div>
                    </div>
                    <div class="card">
                        <div class="card-value">{total_lines:,}</div>
                        <div class="card-label">Total Lines</div>
                    </div>
                    <div class="card">
                        <div class="card-value">{len(lang_names)}</div>
                        <div class="card-label">Languages</div>
                    </div>
                    <div class="card">
                        <div class="card-value">{int(avg_file_size)}</div>
                        <div class="card-label">Avg File Size</div>
                    </div>
                </div>

                <div class="charts-grid">
                    <div class="chart-container">
                        <h2>Lines by Language</h2>
                        <svg viewBox="0 0 400 400" class="pie-chart">
{self._generate_pie_chart(lang_names, lang_values)}
                        </svg>
                        <div class="chart-legend">
{self._generate_legend(lang_names, lang_values, total_lines)}
                        </div>
                    </div>

                    <div class="chart-container">
                        <h2>Top 10 Files by Lines</h2>
                        <svg viewBox="0 0 800 350" class="bar-chart">
{self._generate_bar_chart(top_filenames, top_file_lines, max(top_file_lines) if top_file_lines else 1)}
                        </svg>
                    </div>
                </div>
            </div>

            <!-- Files Tab -->
            <div id="files" class="tab-content">
                <div class="section">
                    <h2>File Listing</h2>
                    <div class="search-box">
                        <input type="text" id="fileSearch" placeholder="Search files...">
                    </div>
                    <div class="extension-filter">
                        <label>Filter by Extension:</label>
                        <div id="extFilterButtons" class="filter-buttons">
{self._generate_extension_filters(files_data)}
                        </div>
                    </div>
                    <table class="data-table" id="filesTable">
                        <thead>
                            <tr>
                                <th onclick="sortTable('filesTable', 0)">Path / Filename ▼</th>
                                <th onclick="sortTable('filesTable', 1)">Lines</th>
                                <th onclick="sortTable('filesTable', 2)">% Total</th>
                                <th onclick="sortTable('filesTable', 3)">Language</th>
                                <th onclick="sortTable('filesTable', 4)">Blank</th>
                                <th onclick="sortTable('filesTable', 5)">Comment</th>
                                <th onclick="sortTable('filesTable', 6)">Code</th>
                            </tr>
                        </thead>
                        <tbody>
{self._generate_files_table_rows(files_data)}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Languages Tab -->
            <div id="languages" class="tab-content">
                <div class="section">
                    <h2>Language Statistics</h2>
                    <table class="data-table" id="langTable">
                        <thead>
                            <tr>
                                <th onclick="sortTable('langTable', 0)">Language</th>
                                <th onclick="sortTable('langTable', 1)">Files</th>
                                <th onclick="sortTable('langTable', 2)">Total Lines</th>
                                <th onclick="sortTable('langTable', 3)">Avg/File</th>
                                <th onclick="sortTable('langTable', 4)">% of Total</th>
                                <th onclick="sortTable('langTable', 5)">Blank</th>
                                <th onclick="sortTable('langTable', 6)">Comment</th>
                                <th onclick="sortTable('langTable', 7)">Code</th>
                            </tr>
                        </thead>
                        <tbody>
{self._generate_languages_table_rows(lang_stats)}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Statistics Tab -->
            <div id="statistics" class="tab-content">
                <div class="section">
                    <h2>Distribution & Percentiles</h2>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <h3>File Size Percentiles</h3>
                            <ul class="percentile-list">
{self._generate_percentile_list(percentiles)}
                            </ul>
                        </div>
                        <div class="stat-item">
                            <h3>Code Metrics</h3>
                            <ul class="metrics-list">
{self._generate_code_metrics(loc_data, total_lines)}
                            </ul>
                        </div>
                    </div>

                    <h3>Distribution Histogram</h3>
                    <svg viewBox="0 0 800 300" class="histogram">
{self._generate_histogram(files_data)}
                    </svg>
                </div>
            </div>
        </main>

        <footer class="footer">
            <p>Generated by ClickUp Framework • Line Count Report v1.0</p>
            <p class="timestamp">{timestamp_str}</p>
        </footer>
    </div>

    <script>
{self._build_javascript()}
    </script>
</body>
</html>
"""

    def _build_css(self) -> str:
        """Build embedded CSS stylesheet."""
        return f"""        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --bg: {self.colors['background']};
            --surface: {self.colors['surface']};
            --text: {self.colors['text']};
            --text-muted: {self.colors['text_muted']};
            --primary: {self.colors['primary']};
            --secondary: {self.colors['secondary']};
            --highlight: {self.colors['highlight']};
            --border: {self.colors['border']};
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
                         Ubuntu, Cantarell, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0;
        }}

        .header {{
            background: linear-gradient(135deg, {self.colors['surface']} 0%, {self.colors['background']} 100%);
            border-bottom: 2px solid var(--border);
            padding: 2rem;
            margin-bottom: 2rem;
        }}

        .header-content h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            color: var(--primary);
        }}

        .header-content .subtitle {{
            color: var(--text-muted);
            font-size: 0.95rem;
        }}

        .nav-tabs {{
            display: flex;
            gap: 0.5rem;
            border-bottom: 1px solid var(--border);
            padding: 0 2rem;
            background: {self.colors['surface']};
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .tab-button {{
            background: none;
            border: none;
            color: var(--text-muted);
            padding: 1rem 1.5rem;
            cursor: pointer;
            font-size: 1rem;
            border-bottom: 2px solid transparent;
            transition: all 0.3s ease;
        }}

        .tab-button:hover {{
            color: var(--text);
            border-bottom-color: var(--primary);
        }}

        .tab-button.active {{
            color: var(--primary);
            border-bottom-color: var(--primary);
        }}

        .main-content {{
            padding: 2rem;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .card {{
            background: {self.colors['surface']};
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
        }}

        .card-value {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }}

        .card-label {{
            color: var(--text-muted);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }}

        .chart-container {{
            background: {self.colors['surface']};
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
        }}

        .chart-container h2 {{
            margin-bottom: 1rem;
            color: var(--primary);
        }}

        .pie-chart, .bar-chart, .histogram {{
            width: 100%;
            height: auto;
        }}

        .chart-legend {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
        }}

        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
        }}

        .section {{
            background: {self.colors['surface']};
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}

        .section h2 {{
            margin-bottom: 1rem;
            color: var(--primary);
        }}

        .section h3 {{
            margin: 1.5rem 0 1rem 0;
            color: var(--secondary);
        }}

        .search-box {{
            margin-bottom: 1.5rem;
        }}

        .search-box input {{
            width: 100%;
            max-width: 400px;
            padding: 0.75rem;
            background: {self.colors['background']};
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--text);
            font-size: 1rem;
        }}

        .search-box input::placeholder {{
            color: var(--text-muted);
        }}

        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}

        .data-table thead {{
            background: {self.colors['background']};
        }}

        .data-table th {{
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            color: var(--primary);
            border-bottom: 2px solid var(--border);
            cursor: pointer;
            user-select: none;
        }}

        .data-table th:hover {{
            background: {self.colors['surface']};
        }}

        .data-table tbody tr {{
            border-bottom: 1px solid var(--border);
            transition: background 0.2s ease;
        }}

        .data-table tbody tr:hover {{
            background: {self.colors['background']};
        }}

        .data-table td {{
            padding: 0.75rem 1rem;
        }}

        .data-table .numeric {{
            text-align: right;
            font-family: 'Monaco', 'Menlo', monospace;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }}

        .stat-item h3 {{
            margin-bottom: 1rem;
            color: var(--secondary);
        }}

        .percentile-list, .metrics-list {{
            list-style: none;
        }}

        .percentile-list li, .metrics-list li {{
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .percentile-list li:last-child, .metrics-list li:last-child {{
            border-bottom: none;
        }}

        .percentile-list .label, .metrics-list .label {{
            color: var(--text-muted);
        }}

        .percentile-list .value, .metrics-list .value {{
            font-weight: 600;
            color: var(--highlight);
            font-family: 'Monaco', 'Menlo', monospace;
        }}

        .footer {{
            background: {self.colors['surface']};
            border-top: 1px solid var(--border);
            padding: 2rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-top: 3rem;
        }}

        .footer .timestamp {{
            margin-top: 0.5rem;
            font-size: 0.85rem;
        }}

        .extension-filter {{
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: {self.colors['background']};
            border: 1px solid var(--border);
            border-radius: 4px;
        }}

        .extension-filter label {{
            display: block;
            margin-bottom: 0.75rem;
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.9rem;
        }}

        .filter-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        .ext-filter-btn {{
            padding: 0.5rem 1rem;
            background: {self.colors['surface']};
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--text);
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s ease;
        }}

        .ext-filter-btn:hover {{
            background: {self.colors['primary']};
            color: #000;
            border-color: var(--primary);
        }}

        .ext-filter-btn.active {{
            background: var(--primary);
            color: #000;
            font-weight: 600;
        }}

        .data-table tbody tr.hidden {{
            display: none;
        }}

        /* Mobile responsiveness */
        @media (max-width: 768px) {{
            .header-content h1 {{
                font-size: 1.75rem;
            }}

            .nav-tabs {{
                overflow-x: auto;
                padding: 0 1rem;
            }}

            .summary-cards {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .charts-grid {{
                grid-template-columns: 1fr;
            }}

            .data-table {{
                font-size: 0.8rem;
            }}

            .data-table th, .data-table td {{
                padding: 0.5rem;
            }}
        }}

        @media (max-width: 480px) {{
            .header {{
                padding: 1rem;
            }}

            .header-content h1 {{
                font-size: 1.5rem;
            }}

            .main-content {{
                padding: 1rem;
            }}

            .summary-cards {{
                grid-template-columns: 1fr;
            }}

            .nav-tabs {{
                padding: 0;
            }}

            .tab-button {{
                padding: 0.75rem 1rem;
                font-size: 0.85rem;
            }}
        }}

        /* Keyboard navigation support */
        .tab-button:focus {{
            outline: 2px solid var(--primary);
            outline-offset: 2px;
        }}

        .data-table tbody tr:focus-within {{
            outline: 2px solid var(--secondary);
            outline-offset: -1px;
        }}

        /* Accessibility: high contrast for tables */
        .data-table th {{
            background-color: var(--border);
            color: var(--text);
        }}
"""

    def _build_javascript(self) -> str:
        """Build embedded JavaScript for interactivity."""
        return """        // Tab switching
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                const tabName = this.getAttribute('data-tab');
                switchTab(tabName);
            });

            // Keyboard navigation: arrow keys
            button.addEventListener('keydown', function(e) {
                const buttons = Array.from(tabButtons);
                const index = buttons.indexOf(this);
                if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    buttons[(index + 1) % buttons.length].focus();
                    buttons[(index + 1) % buttons.length].click();
                } else if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    buttons[(index - 1 + buttons.length) % buttons.length].focus();
                    buttons[(index - 1 + buttons.length) % buttons.length].click();
                }
            });
        });

        function switchTab(tabName) {
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));

            // Remove active class from buttons
            tabButtons.forEach(button => button.classList.remove('active'));

            // Show selected tab
            const selectedTab = document.getElementById(tabName);
            if (selectedTab) {
                selectedTab.classList.add('active');
            }

            // Mark button as active
            const selectedButton = document.querySelector(`[data-tab="${tabName}"]`);
            if (selectedButton) {
                selectedButton.classList.add('active');
            }
        }

        // Table sorting
        function sortTable(tableId, columnIndex) {
            const table = document.getElementById(tableId);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            // Determine sort direction
            const isAscending = table.getAttribute('data-sort-column') === String(columnIndex) &&
                               table.getAttribute('data-sort-direction') === 'asc';
            const direction = isAscending ? 'desc' : 'asc';

            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.children[columnIndex].textContent.trim();
                const bValue = b.children[columnIndex].textContent.trim();

                // Try numeric comparison
                const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
                const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));

                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return direction === 'asc' ? aNum - bNum : bNum - aNum;
                }

                // String comparison
                return direction === 'asc' ?
                    aValue.localeCompare(bValue) :
                    bValue.localeCompare(aValue);
            });

            // Update table
            rows.forEach(row => tbody.appendChild(row));

            // Update header icons
            table.querySelectorAll('th').forEach((th, idx) => {
                if (idx === columnIndex) {
                    th.textContent = th.textContent.replace(/[▲▼]/g, '');
                    th.textContent += (direction === 'asc' ? ' ▲' : ' ▼');
                } else {
                    th.textContent = th.textContent.replace(/[▲▼]/g, '');
                    th.textContent += ' ▼';
                }
            });

            // Remember sort state
            table.setAttribute('data-sort-column', columnIndex);
            table.setAttribute('data-sort-direction', direction);
        }

        // Table search/filter
        const fileSearch = document.getElementById('fileSearch');
        if (fileSearch) {
            fileSearch.addEventListener('keyup', function() {
                const searchTerm = this.value.toLowerCase();
                const filesTable = document.getElementById('filesTable');
                const rows = filesTable.querySelectorAll('tbody tr');

                rows.forEach(row => {
                    const filename = row.children[0].textContent.toLowerCase();
                    const language = row.children[3].textContent.toLowerCase();
                    const matches = filename.includes(searchTerm) || language.includes(searchTerm);
                    row.style.display = matches ? '' : 'none';
                });
            });
        }

        // Accessibility: tab key navigation in tables
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                const activeElement = document.activeElement;
                if (activeElement && activeElement.tagName === 'TD') {
                    // Allow default tab behavior
                }
            }
        });

        // Extension filter
        function filterByExtension(extension, event) {
            event.preventDefault();
            const filesTable = document.getElementById('filesTable');
            const rows = filesTable.querySelectorAll('tbody tr');

            // Update button states
            document.querySelectorAll('.ext-filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');

            // Filter rows
            rows.forEach(row => {
                const rowExt = row.getAttribute('data-extension');
                if (extension === 'all' || rowExt === extension) {
                    row.classList.remove('hidden');
                    row.style.display = '';
                } else {
                    row.classList.add('hidden');
                    row.style.display = 'none';
                }
            });
        }
"""

    def _generate_pie_chart(self, labels: list, values: list) -> str:
        """Generate SVG pie chart."""
        if not values or sum(values) == 0:
            cx, cy = ChartConfig.PIE_CENTER_X, ChartConfig.PIE_CENTER_Y
            return f'<text x="{cx}" y="{cy}" text-anchor="middle" fill="#a0a0a0">No data</text>'

        total = sum(values)
        colors = self.CHART_COLORS

        svg_parts = []
        start_angle = -90  # Start from top

        for i, (label, value) in enumerate(zip(labels, values)):
            percentage = value / total
            angle = percentage * 360
            end_angle = start_angle + angle

            # Convert to radians
            pi = math.pi
            start_rad = start_angle * pi / 180
            end_rad = end_angle * pi / 180

            # Calculate points
            cx, cy, r = ChartConfig.PIE_CENTER_X, ChartConfig.PIE_CENTER_Y, ChartConfig.PIE_RADIUS
            x1 = cx + r * math.cos(start_rad)
            y1 = cy + r * math.sin(start_rad)
            x2 = cx + r * math.cos(end_rad)
            y2 = cy + r * math.sin(end_rad)

            large_arc = 1 if angle > 180 else 0

            # Pie slice
            path = (
                f'M {cx} {cy} L {x1:.1f} {y1:.1f} '
                f'A {r} {r} 0 {large_arc} 1 {x2:.1f} {y2:.1f} Z'
            )

            color = colors[i % len(colors)]
            svg_parts.append(
                f'<path d="{path}" fill="{color}" stroke="{self.colors["background"]}" '
                'stroke-width="2" />'
            )

            start_angle = end_angle

        return '\n'.join(svg_parts)

    def _generate_bar_chart(self, labels: list, values: list, max_value: float) -> str:
        """Generate SVG horizontal bar chart."""
        if not values or max_value == 0:
            return '<text x="400" y="175" text-anchor="middle" fill="#a0a0a0">No data</text>'

        svg_parts = []
        cfg = ChartConfig

        # Y-axis label
        y_center = len(labels) * (cfg.BAR_HEIGHT + cfg.BAR_SPACING) / 2 + 20
        svg_parts.append(
            f'<text x="10" y="{y_center}" '
            'text-anchor="end" fill="#a0a0a0" font-size="12">Files</text>'
        )

        # X-axis label
        svg_parts.append(
            '<text x="400" y="330" text-anchor="middle" fill="#a0a0a0" '
            'font-size="12">Lines</text>'
        )

        for i, (label, value) in enumerate(zip(labels, values)):
            y = i * (cfg.BAR_HEIGHT + cfg.BAR_SPACING) + 20
            bar_width = (value / max_value) * cfg.BAR_MAX_WIDTH if max_value > 0 else 0

            # Bar
            svg_parts.append(
                f'<rect x="{cfg.BAR_LEFT_MARGIN}" y="{y}" width="{bar_width}" '
                f'height="{cfg.BAR_HEIGHT}" fill="#4CAF50" opacity="0.8" />'
            )

            # Label
            svg_parts.append(
                f'<text x="{cfg.BAR_LEFT_MARGIN - 5}" y="{y + cfg.BAR_HEIGHT / 2 + 4}" '
                f'text-anchor="end" fill="#a0a0a0" font-size="11">{label}</text>'
            )

            # Value
            svg_parts.append(
                f'<text x="{cfg.BAR_LEFT_MARGIN + bar_width + 5}" y="{y + cfg.BAR_HEIGHT / 2 + 4}" '
                f'fill="#e0e0e0" font-size="11">{value}</text>'
            )

        return '\n'.join(svg_parts)

    def _generate_histogram(self, files_data: list) -> str:
        """Generate SVG histogram of file size distribution."""
        if not files_data:
            return '<text x="400" y="150" text-anchor="middle" fill="#a0a0a0">No data</text>'

        # Create bins: 0-10, 10-50, 50-100, 100-500, 500+
        bins = [0, 10, 50, 100, 500, float('inf')]
        bin_labels = ['0-10', '10-50', '50-100', '100-500', '500+']
        bin_counts = [0] * (len(bins) - 1)

        for file_data in files_data:
            total = file_data['total']
            for i in range(len(bins) - 1):
                if bins[i] <= total < bins[i + 1]:
                    bin_counts[i] += 1
                    break

        max_count = max(bin_counts) if bin_counts else 1
        if max_count == 0:
            max_count = 1

        svg_parts = []
        cfg = ChartConfig

        for i, (label, count) in enumerate(zip(bin_labels, bin_counts)):
            x = cfg.HIST_LEFT_MARGIN + i * (cfg.HIST_BAR_WIDTH + cfg.HIST_BAR_SPACING)
            bar_height = (count / max_count) * cfg.HIST_MAX_HEIGHT if max_count > 0 else 0
            y = cfg.HIST_BASE_Y - bar_height

            # Bar
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{cfg.HIST_BAR_WIDTH}" '
                f'height="{bar_height}" fill="#2196F3" opacity="0.8" />'
            )

            # Label
            svg_parts.append(
                f'<text x="{x + cfg.HIST_BAR_WIDTH / 2}" y="{cfg.HIST_LABEL_Y}" text-anchor="middle" '
                f'fill="#a0a0a0" font-size="12">{label}</text>'
            )

            # Count
            svg_parts.append(
                f'<text x="{x + cfg.HIST_BAR_WIDTH / 2}" y="{y - 5}" text-anchor="middle" '
                f'fill="#e0e0e0" font-size="12">{count}</text>'
            )

        return '\n'.join(svg_parts)

    def _generate_legend(self, labels: list, values: list, total: int) -> str:
        """Generate HTML legend for pie chart."""
        colors = self.CHART_COLORS

        legend_items = []
        for i, (label, value) in enumerate(zip(labels, values)):
            percentage = (value / total * 100) if total > 0 else 0
            color = colors[i % len(colors)]
            legend_items.append(
                '<div class="legend-item">'
                f'<div class="legend-color" style="background: {color};"></div>'
                f'<span>{label}: {value:,} ({percentage:.1f}%)</span>'
                '</div>'
            )

        return '\n'.join(legend_items)

    def _generate_files_table_rows(self, files_data: list) -> str:
        """Generate HTML table rows for files table."""
        rows = []
        for file_data in files_data:
            ext = file_data.get('extension', 'no-ext')
            path_display = f'{self._escape_html(file_data["path"])}'
            rows.append(
                f'<tr data-extension="{ext}">'
                f'<td>{path_display}</td>'
                f'<td class="numeric">{file_data["total"]:,}</td>'
                f'<td class="numeric">{file_data["percentage"]:.2f}%</td>'
                f'<td>{self._escape_html(file_data["language"])}</td>'
                f'<td class="numeric">{file_data["blank"]:,}</td>'
                f'<td class="numeric">{file_data["comment"]:,}</td>'
                f'<td class="numeric">{file_data["code"]:,}</td>'
                '</tr>'
            )
        return '\n'.join(rows)

    def _generate_extension_filters(self, files_data: list) -> str:
        """Generate extension filter buttons."""
        # Extract unique extensions with counts
        ext_counts = {}
        for file_data in files_data:
            ext = file_data.get('extension', 'no-ext')
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

        # Sort by frequency (descending)
        sorted_exts = sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)

        buttons = ['<button class="ext-filter-btn active" onclick="filterByExtension(\'all\', event)" data-ext="all">All</button>']
        for ext, count in sorted_exts:
            buttons.append(
                f'<button class="ext-filter-btn" onclick="filterByExtension(\'{ext}\', event)" data-ext="{ext}">'
                f'{ext} ({count})</button>'
            )

        return '\n'.join(buttons)

    def _generate_languages_table_rows(self, lang_stats: list) -> str:
        """Generate HTML table rows for languages table."""
        rows = []
        for lang in lang_stats:
            rows.append(
                '<tr>'
                f'<td>{self._escape_html(lang["language"])}</td>'
                f'<td class="numeric">{lang["files"]}</td>'
                f'<td class="numeric">{lang["total"]:,}</td>'
                f'<td class="numeric">{lang["average"]:.1f}</td>'
                f'<td class="numeric">{lang["percentage"]:.2f}%</td>'
                f'<td class="numeric">{lang["blank"]:,}</td>'
                f'<td class="numeric">{lang["comment"]:,}</td>'
                f'<td class="numeric">{lang["code"]:,}</td>'
                '</tr>'
            )
        return '\n'.join(rows)

    def _generate_percentile_list(self, percentiles: Dict[str, float]) -> str:
        """Generate HTML list for percentiles."""
        items = []
        for key in ['p50', 'p75', 'p90', 'p95', 'p99']:
            value = percentiles.get(key, 0)
            label_text = key.upper()
            items.append(
                '<li>'
                f'<span class="label">{label_text}:</span>'
                f'<span class="value">{int(value)}</span>'
                '</li>'
            )
        return '\n'.join(items)

    def _generate_code_metrics(
        self,
        loc_data: Dict[str, Dict[str, Any]],
        total_lines: int
    ) -> str:
        """Generate HTML list for code metrics."""
        total_blank = sum(info.get('blank', 0) for info in loc_data.values())
        total_comment = sum(info.get('comment', 0) for info in loc_data.values())
        total_code = sum(info.get('code', 0) for info in loc_data.values())

        blank_pct = (total_blank / total_lines * 100) if total_lines > 0 else 0
        comment_pct = (total_comment / total_lines * 100) if total_lines > 0 else 0
        code_pct = (total_code / total_lines * 100) if total_lines > 0 else 0

        return f"""<li>
                                <span class="label">Code Lines:</span>
                                <span class="value">{total_code:,} ({code_pct:.1f}%)</span>
                            </li>
                            <li>
                                <span class="label">Comment Lines:</span>
                                <span class="value">{total_comment:,} ({comment_pct:.1f}%)</span>
                            </li>
                            <li>
                                <span class="label">Blank Lines:</span>
                                <span class="value">{total_blank:,} ({blank_pct:.1f}%)</span>
                            </li>"""

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))

