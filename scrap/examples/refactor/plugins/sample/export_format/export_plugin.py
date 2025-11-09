import os
import csv
import json
import logging
from typing import Any, Dict, List, Optional, Union, TextIO

# Import base plugin interface
from plugins.plugin_interface import CommandPlugin
from plugins.config.config_manager import plugin_config_manager

logger = logging.getLogger(__name__)

class ExportFormatPlugin(CommandPlugin):
    """
    Plugin for exporting tasks in various formats.
    
    Supported formats include CSV, Markdown, and HTML. The plugin registers
    an 'export' command that can be used from the CLI to export tasks.
    """
    
    def __init__(self, plugin_id: str):
        """Initialize the export format plugin."""
        super().__init__(plugin_id)
        self.config = {}
        self.default_format = "csv"
        self.include_fields = []
        self.export_directory = "./exports"
        self.exporters = {
            "csv": self._export_csv,
            "markdown": self._export_markdown,
            "html": self._export_html,
            "xlsx": self._export_xlsx,
            "pdf": self._export_pdf
        }
        
    def initialize(self) -> bool:
        """
        Initialize the plugin, loading configuration.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            # Load configuration
            self.config = plugin_config_manager.load_config(self.plugin_id)
            
            # Extract config values
            self.default_format = self.config.get("default_format", "csv")
            self.include_fields = self.config.get("include_fields", [])
            self.export_directory = self.config.get("export_directory", "./exports")
            
            # Ensure export directory exists
            os.makedirs(self.export_directory, exist_ok=True)
            
            logger.info(f"Initialized {self.plugin_id} with default format: {self.default_format}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {self.plugin_id}: {str(e)}")
            return False
    
    def get_commands(self) -> List[str]:
        """
        Get the list of commands this plugin provides.
        
        Returns:
            List[str]: List of command names.
        """
        return ["export"]
    
    def get_command_help(self, command: str) -> str:
        """
        Get the help text for a specific command.
        
        Args:
            command (str): Command name.
            
        Returns:
            str: Help text for the command.
        """
        if command == "export":
            return """
            export - Export tasks to various formats
            
            Usage: export [options] [task_ids...]
            
            Options:
              --format, -f FORMAT       Export format (csv, markdown, html, xlsx, pdf)
              --output, -o FILE         Output file path
              --fields FIELDS           Comma-separated list of fields to include
              --query QUERY             Filter query to select tasks
              --recursive, -r           Include subtasks recursively
              --all, -a                 Export all tasks
            
            Examples:
              export --format markdown --output tasks.md tsk_123 tsk_456
              export --all --format csv --output all_tasks.csv
              export --query "status == 'in progress'" --format html
            """
        return ""
    
    def execute_command(self, command: str, args: List[str], tasks_data: Dict[str, Any]) -> bool:
        """
        Execute a command provided by this plugin.
        
        Args:
            command (str): Command name.
            args (List[str]): Command arguments.
            tasks_data (Dict[str, Any]): Task data from the template file.
            
        Returns:
            bool: True if command executed successfully, False otherwise.
        """
        if command == "export":
            return self._handle_export_command(args, tasks_data)
        
        return False
    
    def get_capabilities(self) -> List[str]:
        """
        Get the list of capabilities this plugin provides.
        
        Returns:
            List[str]: List of capability strings.
        """
        return ["export", "file_generation"]
    
    def get_name(self) -> str:
        """
        Get the display name of the plugin.
        
        Returns:
            str: Plugin display name.
        """
        return "Export Format"
    
    def get_version(self) -> str:
        """
        Get the version of the plugin.
        
        Returns:
            str: Plugin version.
        """
        return "1.0.0"
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the provided configuration.
        
        Args:
            config (Dict[str, Any]): The configuration to validate.
            
        Returns:
            Dict[str, Any]: Validation errors, empty if valid.
        """
        errors = {}
        
        # Validate default_format
        if "default_format" in config:
            if config["default_format"] not in self.exporters:
                errors["default_format"] = f"Must be one of: {', '.join(self.exporters.keys())}"
        
        # Validate include_fields
        if "include_fields" in config and not isinstance(config["include_fields"], list):
            errors["include_fields"] = "Must be a list of field names"
        
        # Validate export_directory
        if "export_directory" in config and not isinstance(config["export_directory"], str):
            errors["export_directory"] = "Must be a string path"
        
        return errors
    
    def _handle_export_command(self, args: List[str], tasks_data: Dict[str, Any]) -> bool:
        """
        Handle the export command.
        
        Args:
            args (List[str]): Command arguments.
            tasks_data (Dict[str, Any]): Task data from the template file.
            
        Returns:
            bool: True if command executed successfully, False otherwise.
        """
        import argparse
        
        # Parse arguments
        parser = argparse.ArgumentParser(prog="export", description="Export tasks to various formats")
        parser.add_argument("--format", "-f", choices=list(self.exporters.keys()), default=self.default_format,
                           help="Export format")
        parser.add_argument("--output", "-o", help="Output file path")
        parser.add_argument("--fields", help="Comma-separated list of fields to include")
        parser.add_argument("--query", help="Filter query to select tasks")
        parser.add_argument("--recursive", "-r", action="store_true", help="Include subtasks recursively")
        parser.add_argument("--all", "-a", action="store_true", help="Export all tasks")
        parser.add_argument("task_ids", nargs="*", help="Task IDs to export")
        
        try:
            parsed_args = parser.parse_args(args)
            
            # Determine output file
            output_file = parsed_args.output
            if not output_file:
                format_ext = parsed_args.format
                if format_ext == "xlsx":
                    format_ext = "xlsx"
                elif format_ext == "pdf":
                    format_ext = "pdf"
                output_file = os.path.join(self.export_directory, f"export.{format_ext}")
            
            # Determine fields to include
            fields = self.include_fields
            if parsed_args.fields:
                fields = parsed_args.fields.split(",")
            
            # Get tasks to export
            tasks = self._get_tasks_to_export(parsed_args, tasks_data)
            
            if not tasks:
                logger.warning("No tasks found to export")
                return True
            
            # Export tasks
            exporter = self.exporters[parsed_args.format]
            result = exporter(tasks, output_file, fields)
            
            if result:
                logger.info(f"Exported {len(tasks)} tasks to {output_file}")
                return True
            else:
                logger.error(f"Failed to export tasks to {output_file}")
                return False
            
        except Exception as e:
            logger.error(f"Error executing export command: {str(e)}")
            return False
    
    def _get_tasks_to_export(self, args: argparse.Namespace, tasks_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get the tasks to export based on command arguments.
        
        Args:
            args (argparse.Namespace): Parsed command arguments.
            tasks_data (Dict[str, Any]): Task data from the template file.
            
        Returns:
            List[Dict[str, Any]]: List of tasks to export.
        """
        tasks = []
        
        # Get all tasks from the template
        all_tasks = self._extract_all_tasks(tasks_data)
        
        # Filter tasks based on arguments
        if args.all:
            tasks = all_tasks
        elif args.query:
            # This would typically use a filter_manager to evaluate the query
            # For now, we just log that this would be done
            logger.info(f"Would filter tasks based on query: {args.query}")
            tasks = all_tasks  # In reality, this would be filtered
        elif args.task_ids:
            # Get tasks by ID
            task_ids = set(args.task_ids)
            tasks = [task for task in all_tasks if task.get("id") in task_ids]
            
            # Handle recursive flag for subtasks
            if args.recursive:
                for task_id in task_ids:
                    tasks.extend(self._get_subtasks_recursive(task_id, all_tasks))
        
        return tasks
    
    def _extract_all_tasks(self, tasks_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all tasks from the template data.
        
        Args:
            tasks_data (Dict[str, Any]): Task data from the template file.
            
        Returns:
            List[Dict[str, Any]]: List of all tasks.
        """
        all_tasks = []
        
        # Process spaces
        for space in tasks_data.get("Spaces", []):
            # Process lists directly in the space
            for task_list in space.get("Lists", []):
                all_tasks.extend(self._extract_tasks_from_list(task_list))
            
            # Process folders in the space
            for folder in space.get("Folders", []):
                for task_list in folder.get("Lists", []):
                    all_tasks.extend(self._extract_tasks_from_list(task_list))
        
        return all_tasks
    
    def _extract_tasks_from_list(self, task_list: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract tasks from a task list, including subtasks.
        
        Args:
            task_list (Dict[str, Any]): Task list data.
            
        Returns:
            List[Dict[str, Any]]: List of tasks.
        """
        tasks = []
        
        for task in task_list.get("Tasks", []):
            tasks.append(task)
            tasks.extend(self._extract_subtasks(task))
        
        return tasks
    
    def _extract_subtasks(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract subtasks from a task recursively.
        
        Args:
            task (Dict[str, Any]): Task data.
            
        Returns:
            List[Dict[str, Any]]: List of subtasks.
        """
        subtasks = []
        
        for subtask in task.get("subtasks", []):
            subtasks.append(subtask)
            subtasks.extend(self._extract_subtasks(subtask))
        
        return subtasks
    
    def _get_subtasks_recursive(self, task_id: str, all_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get subtasks for a task recursively.
        
        Args:
            task_id (str): Task ID.
            all_tasks (List[Dict[str, Any]]): List of all tasks.
            
        Returns:
            List[Dict[str, Any]]: List of subtasks.
        """
        subtasks = []
        
        for task in all_tasks:
            if task.get("parent_id") == task_id:
                subtasks.append(task)
                subtasks.extend(self._get_subtasks_recursive(task.get("id"), all_tasks))
        
        return subtasks
    
    def _export_csv(self, tasks: List[Dict[str, Any]], output_file: str, fields: List[str]) -> bool:
        """
        Export tasks to CSV format.
        
        Args:
            tasks (List[Dict[str, Any]]): Tasks to export.
            output_file (str): Output file path.
            fields (List[str]): Fields to include.
            
        Returns:
            bool: True if export was successful, False otherwise.
        """
        try:
            # Get CSV options from config
            csv_options = self.config.get("csv_options", {})
            delimiter = csv_options.get("delimiter", ",")
            quote_char = csv_options.get("quote_char", '"')
            include_header = csv_options.get("include_header", True)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=delimiter, quotechar=quote_char, quoting=csv.QUOTE_MINIMAL)
                
                # Write header
                if include_header:
                    writer.writerow(fields)
                
                # Write task rows
                for task in tasks:
                    row = []
                    for field in fields:
                        value = task.get(field, "")
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value)
                        row.append(value)
                    writer.writerow(row)
                    
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return False
    
    def _export_markdown(self, tasks: List[Dict[str, Any]], output_file: str, fields: List[str]) -> bool:
        """
        Export tasks to Markdown format.
        
        Args:
            tasks (List[Dict[str, Any]]): Tasks to export.
            output_file (str): Output file path.
            fields (List[str]): Fields to include.
            
        Returns:
            bool: True if export was successful, False otherwise.
        """
        try:
            # Get Markdown options from config
            md_options = self.config.get("markdown_options", {})
            include_metadata = md_options.get("include_metadata", True)
            table_format = md_options.get("table_format", True)
            
            with open(output_file, 'w', encoding='utf-8') as md_file:
                md_file.write("# Task Export\n\n")
                
                if include_metadata:
                    md_file.write(f"Generated: {self._get_current_datetime()}\n")
                    md_file.write(f"Total Tasks: {len(tasks)}\n\n")
                
                if table_format:
                    # Write table header
                    md_file.write("| " + " | ".join(fields) + " |\n")
                    md_file.write("| " + " | ".join(["---"] * len(fields)) + " |\n")
                    
                    # Write task rows
                    for task in tasks:
                        row = []
                        for field in fields:
                            value = task.get(field, "")
                            if isinstance(value, (list, dict)):
                                value = json.dumps(value)
                            row.append(str(value).replace("|", "\\|"))
                        md_file.write("| " + " | ".join(row) + " |\n")
                else:
                    # Write tasks as sections
                    for task in tasks:
                        md_file.write(f"## {task.get('name', 'Unnamed Task')}\n\n")
                        
                        for field in fields:
                            if field == "name":
                                continue
                                
                            value = task.get(field, "")
                            if isinstance(value, (list, dict)):
                                value = json.dumps(value, indent=2)
                            md_file.write(f"**{field}**: {value}\n\n")
                            
                        md_file.write("---\n\n")
                    
            return True
        except Exception as e:
            logger.error(f"Error exporting to Markdown: {str(e)}")
            return False
    
    def _export_html(self, tasks: List[Dict[str, Any]], output_file: str, fields: List[str]) -> bool:
        """
        Export tasks to HTML format.
        
        Args:
            tasks (List[Dict[str, Any]]): Tasks to export.
            output_file (str): Output file path.
            fields (List[str]): Fields to include.
            
        Returns:
            bool: True if export was successful, False otherwise.
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as html_file:
                # Write HTML header
                html_file.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Task Export</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .metadata { margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>Task Export</h1>
    <div class="metadata">
        <p>Generated: """ + self._get_current_datetime() + """</p>
        <p>Total Tasks: """ + str(len(tasks)) + """</p>
    </div>
    <table>
        <thead>
            <tr>
""")

                # Write table header
                for field in fields:
                    html_file.write(f"                <th>{field}</th>\n")
                
                html_file.write("""            </tr>
        </thead>
        <tbody>
""")

                # Write task rows
                for task in tasks:
                    html_file.write("            <tr>\n")
                    for field in fields:
                        value = task.get(field, "")
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value)
                        html_file.write(f"                <td>{self._html_escape(value)}</td>\n")
                    html_file.write("            </tr>\n")
                
                # Write HTML footer
                html_file.write("""        </tbody>
    </table>
</body>
</html>
""")
                    
            return True
        except Exception as e:
            logger.error(f"Error exporting to HTML: {str(e)}")
            return False
    
    def _export_xlsx(self, tasks: List[Dict[str, Any]], output_file: str, fields: List[str]) -> bool:
        """
        Export tasks to Excel format.
        
        Args:
            tasks (List[Dict[str, Any]]): Tasks to export.
            output_file (str): Output file path.
            fields (List[str]): Fields to include.
            
        Returns:
            bool: True if export was successful, False otherwise.
        """
        try:
            # Check if pandas and openpyxl are available
            import importlib.util
            if not (importlib.util.find_spec("pandas") and importlib.util.find_spec("openpyxl")):
                logger.error("XLSX export requires pandas and openpyxl packages")
                return False
                
            import pandas as pd
            
            # Convert tasks to DataFrame
            data = []
            for task in tasks:
                row = {}
                for field in fields:
                    value = task.get(field, "")
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value)
                    row[field] = value
                data.append(row)
                
            df = pd.DataFrame(data)
            
            # Export to Excel
            df.to_excel(output_file, index=False)
            
            return True
        except Exception as e:
            logger.error(f"Error exporting to XLSX: {str(e)}")
            return False
    
    def _export_pdf(self, tasks: List[Dict[str, Any]], output_file: str, fields: List[str]) -> bool:
        """
        Export tasks to PDF format.
        
        Args:
            tasks (List[Dict[str, Any]]): Tasks to export.
            output_file (str): Output file path.
            fields (List[str]): Fields to include.
            
        Returns:
            bool: True if export was successful, False otherwise.
        """
        try:
            # Check if required packages are available
            import importlib.util
            if not (importlib.util.find_spec("reportlab")):
                logger.error("PDF export requires reportlab package")
                return False
                
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            # Create PDF document
            doc = SimpleDocTemplate(output_file, pagesize=letter)
            elements = []
            
            # Add title
            styles = getSampleStyleSheet()
            elements.append(Paragraph("Task Export", styles['Title']))
            elements.append(Spacer(1, 12))
            
            # Add metadata
            elements.append(Paragraph(f"Generated: {self._get_current_datetime()}", styles['Normal']))
            elements.append(Paragraph(f"Total Tasks: {len(tasks)}", styles['Normal']))
            elements.append(Spacer(1, 12))
            
            # Create table data
            data = [fields]  # Header row
            
            for task in tasks:
                row = []
                for field in fields:
                    value = task.get(field, "")
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value)
                    row.append(str(value))
                data.append(row)
            
            # Create table
            table = Table(data)
            
            # Add style
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
            
            table.setStyle(style)
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            
            return True
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            return False
    
    def _get_current_datetime(self) -> str:
        """
        Get current datetime string.
        
        Returns:
            str: Current datetime string.
        """
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _html_escape(self, text: Any) -> str:
        """
        Escape HTML special characters.
        
        Args:
            text (Any): Text to escape.
            
        Returns:
            str: Escaped text.
        """
        import html
        return html.escape(str(text)) 