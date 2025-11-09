import re
import datetime
import logging
from typing import Any, Dict, List, Optional, Union

# Import base plugin interface
from plugins.plugin_interface import TaskOperationPlugin
from plugins.hooks.hook_system import register_hook
from plugins.config.config_manager import plugin_config_manager
from notification.notification_manager import notification_manager

logger = logging.getLogger(__name__)

class CustomFieldValidationPlugin(TaskOperationPlugin):
    """
    Plugin for validating custom fields in tasks according to specified rules.
    
    This plugin validates custom fields like due dates, story points, and any fields
    that can be validated using regex patterns. It can be configured to either warn
    about validation failures, block task creation/updates, or attempt to auto-fix issues.
    """
    
    def __init__(self, plugin_id: str):
        """Initialize the custom field validation plugin."""
        super().__init__(plugin_id)
        self.config = {}
        self.rules = {}
        self.validation_mode = "warn"
        self.enable_notifications = True
        
    def initialize(self) -> bool:
        """
        Initialize the plugin, loading configuration and registering hooks.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            # Load configuration
            self.config = plugin_config_manager.load_config(self.plugin_id)
            
            # Extract config values
            self.rules = self.config.get("validation_rules", {})
            self.validation_mode = self.config.get("validation_mode", "warn")
            self.enable_notifications = self.config.get("enable_notifications", True)
            
            logger.info(f"Initialized {self.plugin_id} with {len(self.rules)} validation rules")
            logger.debug(f"Validation mode: {self.validation_mode}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {self.plugin_id}: {str(e)}")
            return False
    
    def get_capabilities(self) -> List[str]:
        """
        Get the list of capabilities this plugin provides.
        
        Returns:
            List[str]: List of capability strings.
        """
        return ["task_validation", "field_validation"]
    
    def get_name(self) -> str:
        """
        Get the display name of the plugin.
        
        Returns:
            str: Plugin display name.
        """
        return "Custom Field Validation"
    
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
        
        # Validate validation_rules
        if "validation_rules" not in config:
            errors["validation_rules"] = "Missing required configuration key"
        elif not isinstance(config["validation_rules"], dict):
            errors["validation_rules"] = "Must be a dictionary of field rules"
            
        # Validate validation_mode
        if "validation_mode" in config:
            mode = config["validation_mode"]
            if mode not in ["warn", "block", "auto_fix"]:
                errors["validation_mode"] = "Must be one of: warn, block, auto_fix"
                
        # Validate enable_notifications
        if "enable_notifications" in config and not isinstance(config["enable_notifications"], bool):
            errors["enable_notifications"] = "Must be a boolean value"
            
        return errors
    
    @register_hook("task_hooks.validate_task")
    def validate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a task's custom fields according to configured rules.
        
        Args:
            task (Dict[str, Any]): The task to validate.
            
        Returns:
            Dict[str, Any]: Validation errors, empty if valid.
        """
        if not self.rules:
            return {}
            
        errors = {}
        custom_fields = task.get("custom_fields", {})
        
        # Validate each field with rules
        for field_name, rule in self.rules.items():
            if field_name in custom_fields:
                field_value = custom_fields[field_name]
                field_errors = self._validate_field(field_name, field_value, rule)
                
                if field_errors:
                    errors[field_name] = field_errors
                    
                    # Notify about validation errors if enabled
                    if self.enable_notifications and notification_manager:
                        notification_manager.send_notification(
                            title=f"Field Validation Error: {field_name}",
                            message=f"Task '{task.get('name', 'Unnamed')}' has invalid {field_name}: {field_errors}",
                            level="warning",
                            context={
                                "task_id": task.get("id"),
                                "field": field_name,
                                "errors": field_errors
                            }
                        )
        
        return errors
    
    @register_hook("task_hooks.on_task_created")
    def on_task_created(self, task: Dict[str, Any]) -> None:
        """
        Validate a task when it's created.
        
        Args:
            task (Dict[str, Any]): The newly created task.
        """
        errors = self.validate_task(task)
        
        if errors:
            logger.warning(f"Task {task.get('id')} created with validation errors: {errors}")
            
            if self.validation_mode == "auto_fix":
                # Try to fix issues based on rules
                self._attempt_auto_fix(task, errors)
    
    @register_hook("task_hooks.on_task_updated")
    def on_task_updated(self, task: Dict[str, Any], previous_task: Dict[str, Any]) -> None:
        """
        Validate a task when it's updated.
        
        Args:
            task (Dict[str, Any]): The updated task.
            previous_task (Dict[str, Any]): The task before updates.
        """
        # Only validate if custom fields changed
        old_fields = previous_task.get("custom_fields", {})
        new_fields = task.get("custom_fields", {})
        
        if old_fields != new_fields:
            errors = self.validate_task(task)
            
            if errors:
                logger.warning(f"Task {task.get('id')} updated with validation errors: {errors}")
                
                if self.validation_mode == "auto_fix":
                    # Try to fix issues based on rules
                    self._attempt_auto_fix(task, errors)
                elif self.validation_mode == "block":
                    # TODO: In a real implementation, would integrate with task save workflow
                    # to actually block the save. Here we just log it.
                    logger.error(f"Update to task {task.get('id')} would be blocked due to validation errors")
    
    def _validate_field(self, field_name: str, value: Any, rule: Dict[str, Any]) -> Optional[str]:
        """
        Validate a single field against its rules.
        
        Args:
            field_name (str): Name of the field being validated.
            value (Any): Value of the field to validate.
            rule (Dict[str, Any]): Validation rules for this field.
            
        Returns:
            Optional[str]: Error message if validation fails, None if valid.
        """
        # Due date validation
        if field_name == "due_date" and value:
            return self._validate_due_date(value, rule)
            
        # Story points validation (or any field with allowed values)
        elif "allowed_values" in rule:
            if value not in rule["allowed_values"]:
                return f"Value must be one of: {', '.join(map(str, rule['allowed_values']))}"
                
        # Regex validation
        elif "regex" in rule and isinstance(value, str):
            pattern = rule["regex"]
            if not re.match(pattern, value):
                return f"Value does not match required pattern: {pattern}"
                
        # Range validation
        elif "min" in rule or "max" in rule:
            if "min" in rule and value < rule["min"]:
                return f"Value must be at least {rule['min']}"
            if "max" in rule and value > rule["max"]:
                return f"Value must be at most {rule['max']}"
                
        return None
    
    def _validate_due_date(self, date_value: str, rule: Dict[str, Any]) -> Optional[str]:
        """
        Validate a due date field according to rules.
        
        Args:
            date_value (str): The date string to validate.
            rule (Dict[str, Any]): Validation rules for due dates.
            
        Returns:
            Optional[str]: Error message if validation fails, None if valid.
        """
        try:
            # Parse date string - assume ISO format
            if isinstance(date_value, str):
                due_date = datetime.datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            else:
                # Handle if date is already a datetime object
                due_date = date_value
                
            now = datetime.datetime.now(tz=due_date.tzinfo)
            
            # Validate minimum days ahead
            if "min_days_ahead" in rule:
                min_days = rule["min_days_ahead"]
                min_date = now + datetime.timedelta(days=min_days)
                
                if due_date < min_date:
                    return f"Due date must be at least {min_days} days in the future"
            
            # Validate working days only
            if rule.get("working_days_only", False):
                # Simple check for weekends (0 = Monday, 6 = Sunday in ISO weekday)
                if due_date.weekday() > 4:  # 5 = Saturday, 6 = Sunday
                    return "Due date must be a working day (Mon-Fri)"
                    
            return None
        except (ValueError, TypeError) as e:
            return f"Invalid date format: {str(e)}"
    
    def _attempt_auto_fix(self, task: Dict[str, Any], errors: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to automatically fix validation errors based on rules.
        
        Args:
            task (Dict[str, Any]): The task with errors.
            errors (Dict[str, Any]): The validation errors.
            
        Returns:
            Dict[str, Any]: The potentially modified task.
        """
        custom_fields = task.get("custom_fields", {}).copy()
        fixed_fields = []
        
        for field_name, error in errors.items():
            if field_name not in self.rules:
                continue
                
            rule = self.rules[field_name]
            value = custom_fields.get(field_name)
            
            # Auto-fix for due dates
            if field_name == "due_date" and "min_days_ahead" in rule:
                now = datetime.datetime.now()
                days_ahead = rule["min_days_ahead"]
                
                # Set to minimum allowed date
                new_date = now + datetime.timedelta(days=days_ahead)
                
                # Adjust for working days if needed
                if rule.get("working_days_only", False) and new_date.weekday() > 4:
                    # Move to next Monday if on weekend
                    days_to_add = 7 - new_date.weekday()
                    new_date = new_date + datetime.timedelta(days=days_to_add)
                
                custom_fields[field_name] = new_date.isoformat()
                fixed_fields.append(field_name)
            
            # Auto-fix for allowed values
            elif "allowed_values" in rule and rule["allowed_values"]:
                # Default to first allowed value
                custom_fields[field_name] = rule["allowed_values"][0]
                fixed_fields.append(field_name)
        
        if fixed_fields:
            # Update task with fixed fields
            task["custom_fields"] = custom_fields
            
            logger.info(f"Auto-fixed validation errors for fields: {', '.join(fixed_fields)}")
            
            # Send notification about fixes if enabled
            if self.enable_notifications and notification_manager:
                notification_manager.send_notification(
                    title="Field Values Auto-Fixed",
                    message=f"Task '{task.get('name', 'Unnamed')}' had fields auto-fixed: {', '.join(fixed_fields)}",
                    level="info",
                    context={
                        "task_id": task.get("id"),
                        "fixed_fields": fixed_fields
                    }
                )
        
        return task 