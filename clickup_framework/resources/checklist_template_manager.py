"""Checklist template management for ClickUp Framework CLI."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from clickup_framework.exceptions import ClickUpAPIError


class ChecklistTemplateManager:
    """Manages checklist templates for applying to tasks."""

    DEFAULT_TEMPLATES_FILE = Path(__file__).parent.parent / "config" / "checklist_templates.json"
    USER_TEMPLATES_FILE = Path.home() / ".clickup" / "checklist_templates.json"

    def __init__(self, templates_file: Optional[Path] = None):
        """
        Initialize the template manager.

        Args:
            templates_file: Custom path to templates file. If None, uses default locations.
        """
        self.templates_file = templates_file
        self._templates = None

    def _load_templates(self) -> Dict[str, Any]:
        """
        Load templates from file.

        Returns:
            Dictionary of template definitions.
        """
        if self._templates is not None:
            return self._templates

        # Try custom file first
        if self.templates_file and self.templates_file.exists():
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                self._templates = json.load(f)
                return self._templates

        # Try user templates file
        if self.USER_TEMPLATES_FILE.exists():
            with open(self.USER_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                self._templates = json.load(f)
                return self._templates

        # Fall back to default templates
        if self.DEFAULT_TEMPLATES_FILE.exists():
            with open(self.DEFAULT_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                self._templates = json.load(f)
                return self._templates

        # No templates file found, return empty
        self._templates = {"templates": {}}
        return self._templates

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by name.

        Args:
            name: Template name.

        Returns:
            Template definition or None if not found.
        """
        templates = self._load_templates()
        return templates.get("templates", {}).get(name)

    def list_templates(self) -> List[str]:
        """
        List all available template names.

        Returns:
            List of template names.
        """
        templates = self._load_templates()
        return sorted(templates.get("templates", {}).keys())

    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all templates with their definitions.

        Returns:
            Dictionary mapping template names to definitions.
        """
        templates = self._load_templates()
        return templates.get("templates", {})

    def apply_template(self, client, task_id: str, template_name: str) -> Dict[str, Any]:
        """
        Apply a checklist template to a task.

        Args:
            client: ClickUpClient instance.
            task_id: Task ID to apply template to.
            template_name: Name of template to apply.

        Returns:
            Created checklist data.

        Raises:
            ValueError: If template not found.
            ClickUpAPIError: If API call fails.
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        # Create the checklist
        checklist_name = template.get("name", template_name)
        response = client.create_checklist(task_id, checklist_name)
        checklist_id = response["checklist"]["id"]

        # Add items to the checklist
        items = template.get("items", [])
        created_items = []

        for item in items:
            item_name = item.get("name", "")
            if not item_name:
                continue

            # Build item data
            item_data = {}
            if "assignee" in item and item["assignee"]:
                item_data["assignee"] = item["assignee"]

            # Create the item
            item_response = client.create_checklist_item(
                checklist_id,
                item_name,
                **item_data
            )
            created_items.append(item_response)

        return {
            "checklist": response["checklist"],
            "items": created_items,
            "template_name": template_name
        }

    def export_checklist_as_template(
        self,
        checklist_data: Dict[str, Any],
        template_name: str,
        save: bool = False
    ) -> Dict[str, Any]:
        """
        Export a checklist as a template definition.

        Args:
            checklist_data: Checklist data from API.
            template_name: Name for the template.
            save: Whether to save to user templates file.

        Returns:
            Template definition.
        """
        template = {
            "name": checklist_data.get("name", template_name),
            "description": f"Exported from checklist {checklist_data.get('id', '')}",
            "items": []
        }

        # Extract items
        for item in checklist_data.get("items", []):
            template_item = {
                "name": item.get("name", ""),
            }

            # Include assignee if present
            if "assignee" in item and item["assignee"]:
                template_item["assignee"] = item["assignee"]["id"]

            template["items"].append(template_item)

        # Save if requested
        if save:
            self._save_template(template_name, template)

        return template

    def _save_template(self, template_name: str, template: Dict[str, Any]):
        """
        Save a template to user templates file.

        Args:
            template_name: Name of template.
            template: Template definition.
        """
        # Ensure directory exists
        self.USER_TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Load existing templates
        if self.USER_TEMPLATES_FILE.exists():
            with open(self.USER_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"templates": {}}

        # Add new template
        data["templates"][template_name] = template

        # Save
        with open(self.USER_TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def validate_template(self, template: Dict[str, Any]) -> List[str]:
        """
        Validate a template definition.

        Args:
            template: Template definition to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        errors = []

        if "name" not in template:
            errors.append("Template must have a 'name' field")

        if "items" not in template:
            errors.append("Template must have an 'items' field")
        elif not isinstance(template["items"], list):
            errors.append("Template 'items' must be a list")
        else:
            for i, item in enumerate(template["items"]):
                if not isinstance(item, dict):
                    errors.append(f"Item {i} must be a dictionary")
                elif "name" not in item:
                    errors.append(f"Item {i} must have a 'name' field")

        return errors
