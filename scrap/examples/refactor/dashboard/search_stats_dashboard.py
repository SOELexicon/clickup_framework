"""
Task: tsk_62630e24 - Update Utilities and Support Modules Comments
Document: refactor/dashboard/search_stats_dashboard.py
dohcount: 1

Related Tasks:
    - tsk_0a733101 - Code Comments Enhancement (parent)
    - tsk_7e3a4709 - Update Common Module Comments (sibling)
    - tsk_bf28d342 - Update CLI Module Comments (sibling)
    - tsk_4c899138 - Update Storage Module Comments (sibling)
    - tsk_3f55d115 - Update Plugins Module Comments (sibling)

Used By:
    - CLI Search Stats Command: Displays search statistics to users
    - SearchManagerWithStats: Coordinates with this dashboard for reporting
    - SavedSearchesManager: Provides data for dashboard insights
    - PerformanceReport: Incorporates search statistics data
    - AdminPortal: Embeds search statistics dashboard in web interface
    - Optimization Pipelines: Uses insights to improve search performance

Purpose:
    Provides specialized dashboard functionality for search performance monitoring
    and optimization. Analyzes search patterns, performance metrics, and usage statistics
    to generate actionable insights and visualizations. Enables both CLI and web-based
    reporting of search system health and optimization opportunities.

Requirements:
    - CRITICAL: Must minimize performance impact when generating statistics
    - CRITICAL: Must handle large volumes of search history efficiently
    - CRITICAL: HTML output must be properly escaped and safe for embedding
    - All metrics must be clearly labeled with units where applicable
    - Insights must be actionable and based on statistical significance
    - Must support both CLI text output and rich HTML visualization
    - Must not expose sensitive search content in reports

Search Statistics Dashboard

This module provides a dashboard view for search statistics,
offering visualizations of search performance metrics, usage patterns,
and optimization suggestions.
"""

import os
import time
import json
from typing import Dict, List, Optional, Any, Tuple

from refactor.storage.search_manager_stats_integration import SearchManagerWithStats
from refactor.storage.saved_searches import SavedSearchesManager


class SearchStatsDashboard:
    """
    Dashboard for visualizing search statistics and analytics.
    
    This class provides methods to generate visualizations and reports
    for search usage patterns, performance metrics, and optimization
    opportunities.
    """
    
    def __init__(self, stats_manager: Optional[SearchManagerWithStats] = None):
        """
        Initialize the search statistics dashboard.
        
        Args:
            stats_manager: Optional SearchManagerWithStats instance.
                           If not provided, one will be created.
        """
        if stats_manager:
            self.stats_manager = stats_manager
        else:
            # Create managers
            search_manager = SavedSearchesManager()
            self.stats_manager = SearchManagerWithStats(search_manager)
    
    def generate_usage_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive usage report with visualizations.
        
        Args:
            output_path: Optional path to save the report
            
        Returns:
            Dictionary containing report data
        """
        # Get report data
        report_data = self.stats_manager.get_stats_report()
        
        # Add dashboard-specific metrics
        report_data['dashboard'] = {
            'generated_at': time.time(),
            'period': 'all_time',
            'top_insights': self._generate_insights(report_data)
        }
        
        # Save to file if output path provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report_data, f, indent=2)
        
        return report_data
    
    def _generate_insights(self, report_data: Dict[str, Any]) -> List[str]:
        """
        Generate key insights from the report data.
        
        Args:
            report_data: The report data to analyze
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Check if we have enough data
        if report_data['summary'].get('total_searches', 0) < 5:
            insights.append("Not enough search data to generate meaningful insights")
            return insights
        
        # Add insights based on the data
        summary = report_data['summary']
        
        # Usage patterns
        if 'usage_patterns' in report_data:
            hours = report_data['usage_patterns'].get('by_hour', {})
            if hours:
                # Find peak hour
                peak_hour = max(hours.items(), key=lambda x: x[1])
                insights.append(f"Peak search activity is at hour {peak_hour[0]} with {peak_hour[1]} searches")
                
                # Check for usage dips
                avg_usage = sum(int(v) for v in hours.values()) / len(hours)
                low_hours = [(h, c) for h, c in hours.items() if int(c) < avg_usage * 0.5]
                if low_hours:
                    low_hours_str = ", ".join([f"hour {h}" for h, c in low_hours[:3]])
                    insights.append(f"Low search activity detected during {low_hours_str}")
        
        # Performance insights
        if 'avg_execution_time' in summary:
            avg_time = summary['avg_execution_time']
            if avg_time > 500:
                insights.append(f"Overall search performance is slow (avg: {avg_time:.2f}ms)")
            elif avg_time < 100:
                insights.append(f"Overall search performance is good (avg: {avg_time:.2f}ms)")
        
        # Favorite usage insights
        if summary.get('total_favorites_used', 0) > 0:
            fav_percent = (summary['total_favorites_used'] / summary['total_searches']) * 100
            if fav_percent > 70:
                insights.append(f"Favorites are heavily used ({fav_percent:.1f}% of all searches)")
            elif fav_percent < 30:
                insights.append(f"Favorites are underutilized ({fav_percent:.1f}% of all searches)")
        
        # Search optimization suggestions
        suggestions = self.stats_manager.get_optimization_suggestions()
        if suggestions:
            insights.append(f"{len(suggestions)} search optimization opportunities identified")
            
            # Add top suggestion
            if len(suggestions) > 0:
                top_suggestion = suggestions[0]
                insights.append(f"Top suggestion: {top_suggestion.get('action')}")
        
        return insights
    
    def print_dashboard(self) -> None:
        """
        Print a text-based dashboard to the console.
        
        This displays a summary of search statistics and insights
        in a formatted, console-friendly way.
        """
        # Generate report
        report = self.generate_usage_report()
        
        # Calculate width
        width = 80
        
        # Print header
        print("=" * width)
        print("SEARCH STATISTICS DASHBOARD".center(width))
        print("=" * width)
        print()
        
        # Print summary metrics
        summary = report['summary']
        print("SUMMARY METRICS".center(width))
        print("-" * width)
        print(f"Total Searches:         {summary.get('total_searches', 0)}")
        print(f"Unique Searches:        {summary.get('unique_searches', 0)}")
        print(f"Favorite Searches Used: {summary.get('total_favorites_used', 0)}")
        
        if 'avg_execution_time' in summary:
            avg_time = summary['avg_execution_time']
            status = "GOOD" if avg_time < 200 else "OK" if avg_time < 500 else "SLOW"
            print(f"Avg Execution Time:    {avg_time:.2f}ms [{status}]")
        
        # Print top searches
        if report.get('top_searches'):
            print("\nMOST USED SEARCHES")
            print("-" * width)
            for i, (name, count) in enumerate(report['top_searches'][:5], 1):
                print(f"{i}. {name:<30} {count} uses")
        
        # Print slowest searches
        if report.get('slowest_searches'):
            print("\nSLOWEST SEARCHES")
            print("-" * width)
            for i, (name, time) in enumerate(report['slowest_searches'][:5], 1):
                print(f"{i}. {name:<30} {time:.2f}ms average")
        
        # Print key insights
        if 'dashboard' in report and 'top_insights' in report['dashboard']:
            print("\nKEY INSIGHTS")
            print("-" * width)
            for insight in report['dashboard']['top_insights']:
                print(f"• {insight}")
        
        # Print usage trends (simplified)
        if 'usage_patterns' in report and 'by_hour' in report['usage_patterns']:
            print("\nUSAGE BY HOUR")
            print("-" * width)
            
            hours = report['usage_patterns']['by_hour']
            max_count = max(int(count) for count in hours.values()) if hours else 0
            
            if max_count > 0:
                # For simplicity, just show a few hours
                for hour in sorted([0, 6, 12, 18], key=lambda h: int(hours.get(str(h), 0)), reverse=True):
                    count = int(hours.get(str(hour), 0))
                    bar_len = int((count / max_count) * 40)
                    print(f"Hour {hour:<2} | {'#' * bar_len} ({count})")
            else:
                print("No hourly usage data available")
        
        # Print optimization suggestions
        suggestions = self.stats_manager.get_optimization_suggestions()
        if suggestions:
            print("\nOPTIMIZATION SUGGESTIONS")
            print("-" * width)
            for i, suggestion in enumerate(suggestions[:3], 1):
                print(f"{i}. [{suggestion.get('type', 'general').upper()}] {suggestion.get('target', 'general')}")
                print(f"   {suggestion.get('action')}")
        
        print("\n" + "=" * width)
    
    def generate_dashboard_html(self, output_path: str) -> str:
        """
        Generate an HTML dashboard for search statistics.
        
        Args:
            output_path: Path to save the HTML file
            
        Returns:
            Path to the generated HTML file
        """
        # Generate report
        report = self.generate_usage_report()
        
        # Convert report data to JSON for JavaScript
        report_json = json.dumps(report)
        
        # Create HTML content
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search Statistics Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .dashboard {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #333;
            margin-bottom: 5px;
        }}
        .header p {{
            color: #666;
            margin-top: 0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            grid-gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background-color: #f9f9f9;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 1px 5px rgba(0, 0, 0, 0.05);
        }}
        .stat-card h3 {{
            margin-top: 0;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
            color: #333;
            margin: 10px 0;
        }}
        .chart-container {{
            margin: 30px 0;
            height: 300px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f5f5f5;
        }}
        tr:hover {{
            background-color: #f9f9f9;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>Search Statistics Dashboard</h1>
            <p>Insights and analytics for search operations</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Searches</h3>
                <div class="stat-value" id="total-searches">-</div>
            </div>
            <div class="stat-card">
                <h3>Unique Searches</h3>
                <div class="stat-value" id="unique-searches">-</div>
            </div>
            <div class="stat-card">
                <h3>Favorites Used</h3>
                <div class="stat-value" id="favorites-used">-</div>
            </div>
            <div class="stat-card">
                <h3>Avg Execution Time</h3>
                <div class="stat-value" id="avg-execution-time">-</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Most Used Searches</h2>
            <table id="top-searches-table">
                <thead>
                    <tr>
                        <th>Search Name</th>
                        <th>Usage Count</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Will be populated by JavaScript -->
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Slowest Searches</h2>
            <table id="slowest-searches-table">
                <thead>
                    <tr>
                        <th>Search Name</th>
                        <th>Avg Time (ms)</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Will be populated by JavaScript -->
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Key Insights</h2>
            <ul id="insights-list">
                <!-- Will be populated by JavaScript -->
            </ul>
        </div>
        
        <div class="section">
            <h2>Optimization Suggestions</h2>
            <div id="suggestions-container">
                <!-- Will be populated by JavaScript -->
            </div>
        </div>
    </div>
    
    <script>
        // Dashboard data
        const dashboardData = {report_json};
        
        // Populate summary metrics
        document.getElementById('total-searches').textContent = 
            dashboardData.summary.total_searches || 0;
        document.getElementById('unique-searches').textContent = 
            dashboardData.summary.unique_searches || 0;
        document.getElementById('favorites-used').textContent = 
            dashboardData.summary.total_favorites_used || 0;
        document.getElementById('avg-execution-time').textContent = 
            dashboardData.summary.avg_execution_time ? 
            dashboardData.summary.avg_execution_time.toFixed(2) + 'ms' : '-';
        
        // Populate top searches table
        const topSearchesTable = document.getElementById('top-searches-table').getElementsByTagName('tbody')[0];
        if (dashboardData.top_searches && dashboardData.top_searches.length > 0) {{
            dashboardData.top_searches.forEach(search => {{
                const row = topSearchesTable.insertRow();
                const nameCell = row.insertCell(0);
                const countCell = row.insertCell(1);
                nameCell.textContent = search[0];
                countCell.textContent = search[1];
            }});
        }} else {{
            const row = topSearchesTable.insertRow();
            const cell = row.insertCell(0);
            cell.colSpan = 2;
            cell.textContent = 'No data available';
            cell.style.textAlign = 'center';
            cell.style.fontStyle = 'italic';
        }}
        
        // Populate slowest searches table
        const slowestSearchesTable = document.getElementById('slowest-searches-table').getElementsByTagName('tbody')[0];
        if (dashboardData.slowest_searches && dashboardData.slowest_searches.length > 0) {{
            dashboardData.slowest_searches.forEach(search => {{
                const row = slowestSearchesTable.insertRow();
                const nameCell = row.insertCell(0);
                const timeCell = row.insertCell(1);
                nameCell.textContent = search[0];
                timeCell.textContent = search[1].toFixed(2) + 'ms';
            }});
        }} else {{
            const row = slowestSearchesTable.insertRow();
            const cell = row.insertCell(0);
            cell.colSpan = 2;
            cell.textContent = 'No data available';
            cell.style.textAlign = 'center';
            cell.style.fontStyle = 'italic';
        }}
        
        // Populate insights
        const insightsList = document.getElementById('insights-list');
        if (dashboardData.dashboard && dashboardData.dashboard.top_insights) {{
            dashboardData.dashboard.top_insights.forEach(insight => {{
                const li = document.createElement('li');
                li.textContent = insight;
                insightsList.appendChild(li);
            }});
        }}
        
        // Fetch and populate suggestions
        fetch('/api/search-stats/suggestions')
            .then(response => response.json())
            .catch(error => {{
                // Fallback to static data if API is not available
                return dashboardData.suggestions || [];
            }})
            .then(suggestions => {{
                const suggestionsContainer = document.getElementById('suggestions-container');
                if (suggestions && suggestions.length > 0) {{
                    const ul = document.createElement('ul');
                    suggestions.forEach(suggestion => {{
                        const li = document.createElement('li');
                        const strong = document.createElement('strong');
                        strong.textContent = suggestion.target + ': ';
                        li.appendChild(strong);
                        li.appendChild(document.createTextNode(suggestion.action));
                        ul.appendChild(li);
                    }});
                    suggestionsContainer.appendChild(ul);
                }} else {{
                    suggestionsContainer.textContent = 'No optimization suggestions available';
                    suggestionsContainer.style.fontStyle = 'italic';
                }}
            }});
    </script>
</body>
</html>
"""
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write(html)
        
        return output_path


def generate_dashboard(output_path: Optional[str] = None, 
                      format_type: str = 'text') -> None:
    """
    Generate a search statistics dashboard.
    
    Args:
        output_path: Optional path to save the dashboard (HTML or JSON)
        format_type: Dashboard format ('text', 'html', or 'json')
    """
    dashboard = SearchStatsDashboard()
    
    if format_type == 'text':
        dashboard.print_dashboard()
    elif format_type == 'html':
        if not output_path:
            output_path = 'search_stats_dashboard.html'
        dashboard.generate_dashboard_html(output_path)
        print(f"HTML dashboard generated at: {output_path}")
    elif format_type == 'json':
        if not output_path:
            output_path = 'search_stats_report.json'
        dashboard.generate_usage_report(output_path)
        print(f"JSON report generated at: {output_path}")
    else:
        print(f"Unknown format type: {format_type}")
        print("Supported formats: text, html, json")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate search statistics dashboard")
    parser.add_argument(
        '--output', 
        help='Output file path for HTML or JSON output'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'html', 'json'],
        default='text',
        help='Dashboard format (default: text)'
    )
    
    args = parser.parse_args()
    generate_dashboard(args.output, args.format) 