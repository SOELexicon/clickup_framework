"""
Time Tracking Plugin

A plugin for tracking time spent on tasks with detailed reporting capabilities.
"""

import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from ....common.exceptions import PluginError
from ...hooks.task_hooks import TaskHooks
from ...plugin_interface import UtilityPlugin
from ...plugin_manager import Plugin

logger = logging.getLogger(__name__)


class TimeEntry:
    """Represents a time tracking entry for a task."""
    
    def __init__(self, task_id: str, start_time: datetime.datetime):
        """
        Initialize a new time entry.
        
        Args:
            task_id: ID of the task being tracked
            start_time: When the time tracking started
        """
        self.task_id = task_id
        self.start_time = start_time
        self.end_time: Optional[datetime.datetime] = None
        self.duration: Optional[int] = None  # Duration in seconds
        self.notes: str = ""
        self.tags: List[str] = []
        self.is_billable: bool = False
    
    def stop(self, end_time: Optional[datetime.datetime] = None) -> int:
        """
        Stop the time entry.
        
        Args:
            end_time: When the time tracking ended (defaults to now)
            
        Returns:
            int: Duration in seconds
        """
        self.end_time = end_time or datetime.datetime.now()
        self.duration = int((self.end_time - self.start_time).total_seconds())
        return self.duration
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the time entry to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the time entry
        """
        return {
            "task_id": self.task_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "notes": self.notes,
            "tags": self.tags,
            "is_billable": self.is_billable
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeEntry':
        """
        Create a time entry from a dictionary.
        
        Args:
            data: Dictionary representation of a time entry
            
        Returns:
            TimeEntry: New time entry instance
        """
        start_time = datetime.datetime.fromisoformat(data["start_time"])
        entry = cls(data["task_id"], start_time)
        
        if data.get("end_time"):
            entry.end_time = datetime.datetime.fromisoformat(data["end_time"])
        
        entry.duration = data.get("duration")
        entry.notes = data.get("notes", "")
        entry.tags = data.get("tags", [])
        entry.is_billable = data.get("is_billable", False)
        
        return entry


class TimeTrackingPlugin(UtilityPlugin):
    """
    Time tracking plugin for ClickUp JSON Manager.
    
    Features:
    - Track time spent on tasks
    - Generate time reports
    - Export time data in various formats
    - Automatic tracking based on task status
    """
    
    def __init__(self, plugin_id: str, manager: 'PluginManager'):
        """Initialize the time tracking plugin."""
        super().__init__(plugin_id, manager)
        self.active_entries: Dict[str, TimeEntry] = {}  # task_id -> TimeEntry
        self.data_file: Optional[str] = None
        self.entries: List[TimeEntry] = []
    
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful
        """
        try:
            # Register hooks for task operations
            hook_registry = self.manager.get_service("hook_registry")
            if hook_registry:
                # Register for task status changes
                hook_registry.get_hook(TaskHooks.POST_STATUS_CHANGE).register(
                    self.plugin_id,
                    self._on_task_status_change,
                    plugin_id=self.plugin_id
                )
                
                # Register for task selection
                hook_registry.get_hook(TaskHooks.TASK_SELECTED).register(
                    self.plugin_id,
                    self._on_task_selected,
                    plugin_id=self.plugin_id
                )
                
                # Register for task deselection
                hook_registry.get_hook(TaskHooks.TASK_DESELECTED).register(
                    self.plugin_id,
                    self._on_task_deselected,
                    plugin_id=self.plugin_id
                )
            
            # Load saved time entries
            self._load_entries()
            
            logger.info(f"Time tracking plugin initialized with {len(self.entries)} saved entries")
            return super().initialize()
        except Exception as e:
            logger.error(f"Error initializing time tracking plugin: {str(e)}")
            return False
    
    def cleanup(self) -> bool:
        """
        Clean up resources used by the plugin.
        
        Returns:
            bool: True if cleanup was successful
        """
        try:
            # Stop any active time entries
            active_task_ids = list(self.active_entries.keys())
            for task_id in active_task_ids:
                self.stop_tracking(task_id)
            
            # Save time entries
            self._save_entries()
            
            # Unregister hooks
            hook_registry = self.manager.get_service("hook_registry")
            if hook_registry:
                hook_registry.unregister_hooks(self.plugin_id)
            
            return super().cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up time tracking plugin: {str(e)}")
            return False
    
    def get_config_schema(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the configuration schema for this plugin.
        
        Returns:
            Dict[str, Dict[str, Any]]: Configuration schema
        """
        return {
            "auto_track": {
                "type": "boolean",
                "description": "Automatically track time based on task status",
                "default": False
            },
            "track_status_changes": {
                "type": "boolean",
                "description": "Track time when task status changes",
                "default": True
            },
            "idle_detection": {
                "type": "boolean",
                "description": "Detect idle time and prompt for exclusion",
                "default": True
            },
            "idle_threshold_minutes": {
                "type": "integer",
                "description": "Number of minutes before idle detection triggers",
                "default": 5,
                "min": 1,
                "max": 60
            },
            "export_formats": {
                "type": "array",
                "description": "Formats to export time tracking data",
                "default": ["csv", "json"],
                "items": {
                    "type": "string",
                    "enum": ["csv", "json", "pdf", "xlsx"]
                }
            },
            "round_to_nearest": {
                "type": "integer",
                "description": "Round time entries to nearest X minutes",
                "default": 1,
                "min": 1,
                "max": 60
            },
            "data_file": {
                "type": "string",
                "description": "Path to file for storing time tracking data",
                "default": "time_tracking_data.json"
            }
        }
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate the configuration for this plugin.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Validate idle_threshold_minutes if provided
        idle_threshold = config.get("idle_threshold_minutes")
        if idle_threshold is not None:
            if not isinstance(idle_threshold, int):
                return False, "idle_threshold_minutes must be an integer"
            if idle_threshold < 1 or idle_threshold > 60:
                return False, "idle_threshold_minutes must be between 1 and 60"
        
        # Validate export_formats if provided
        export_formats = config.get("export_formats")
        if export_formats is not None:
            if not isinstance(export_formats, list):
                return False, "export_formats must be a list"
            valid_formats = ["csv", "json", "pdf", "xlsx"]
            for fmt in export_formats:
                if fmt not in valid_formats:
                    return False, f"Invalid export format: {fmt}"
        
        # Validate round_to_nearest if provided
        round_to = config.get("round_to_nearest")
        if round_to is not None:
            if not isinstance(round_to, int):
                return False, "round_to_nearest must be an integer"
            if round_to < 1 or round_to > 60:
                return False, "round_to_nearest must be between 1 and 60"
        
        return True, None
    
    def start_tracking(self, task_id: str, note: str = "") -> TimeEntry:
        """
        Start tracking time for a task.
        
        Args:
            task_id: ID of the task to track
            note: Optional note for the time entry
            
        Returns:
            TimeEntry: The started time entry
            
        Raises:
            PluginError: If time tracking is already active for the task
        """
        if task_id in self.active_entries:
            raise PluginError(f"Time tracking already active for task {task_id}")
        
        entry = TimeEntry(task_id, datetime.datetime.now())
        entry.notes = note
        
        self.active_entries[task_id] = entry
        logger.info(f"Started time tracking for task {task_id}")
        
        return entry
    
    def stop_tracking(self, task_id: str) -> Optional[TimeEntry]:
        """
        Stop tracking time for a task.
        
        Args:
            task_id: ID of the task to stop tracking
            
        Returns:
            Optional[TimeEntry]: The completed time entry, or None if no entry was active
        """
        entry = self.active_entries.pop(task_id, None)
        if not entry:
            logger.warning(f"No active time entry for task {task_id}")
            return None
        
        # Stop the entry and calculate duration
        entry.stop()
        
        # Apply rounding if configured
        config = self.get_config()
        round_to = config.get("round_to_nearest", 1)
        if round_to > 1 and entry.duration is not None:
            # Convert seconds to minutes, round, then back to seconds
            minutes = entry.duration / 60
            rounded_minutes = round(minutes / round_to) * round_to
            entry.duration = int(rounded_minutes * 60)
        
        # Save the entry
        self.entries.append(entry)
        self._save_entries()
        
        logger.info(f"Stopped time tracking for task {task_id}, duration: {entry.duration}s")
        return entry
    
    def get_time_entries(self, task_id: Optional[str] = None, 
                         start_date: Optional[datetime.date] = None,
                         end_date: Optional[datetime.date] = None) -> List[TimeEntry]:
        """
        Get time entries matching the filters.
        
        Args:
            task_id: Optional task ID to filter by
            start_date: Optional start date to filter by
            end_date: Optional end date to filter by
            
        Returns:
            List[TimeEntry]: Matching time entries
        """
        result = []
        
        for entry in self.entries:
            # Filter by task ID if provided
            if task_id and entry.task_id != task_id:
                continue
            
            # Filter by start date if provided
            if start_date and entry.start_time.date() < start_date:
                continue
            
            # Filter by end date if provided
            if end_date and entry.start_time.date() > end_date:
                continue
            
            result.append(entry)
        
        return result
    
    def get_total_time(self, task_id: Optional[str] = None,
                      start_date: Optional[datetime.date] = None,
                      end_date: Optional[datetime.date] = None) -> int:
        """
        Get total time spent on tasks matching the filters.
        
        Args:
            task_id: Optional task ID to filter by
            start_date: Optional start date to filter by
            end_date: Optional end date to filter by
            
        Returns:
            int: Total time in seconds
        """
        entries = self.get_time_entries(task_id, start_date, end_date)
        return sum(entry.duration or 0 for entry in entries)
    
    def export_entries(self, format_type: str, 
                      task_id: Optional[str] = None,
                      start_date: Optional[datetime.date] = None,
                      end_date: Optional[datetime.date] = None) -> str:
        """
        Export time entries in the specified format.
        
        Args:
            format_type: Format to export in (csv, json, etc.)
            task_id: Optional task ID to filter by
            start_date: Optional start date to filter by
            end_date: Optional end date to filter by
            
        Returns:
            str: Exported data as string
            
        Raises:
            PluginError: If the format is not supported
        """
        entries = self.get_time_entries(task_id, start_date, end_date)
        
        if format_type == "json":
            data = [entry.to_dict() for entry in entries]
            return json.dumps(data, indent=2)
        elif format_type == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["Task ID", "Start Time", "End Time", 
                           "Duration (s)", "Duration (h:m:s)", 
                           "Notes", "Tags", "Billable"])
            
            # Write entries
            for entry in entries:
                duration_hms = str(datetime.timedelta(seconds=entry.duration or 0))
                writer.writerow([
                    entry.task_id,
                    entry.start_time.isoformat(),
                    entry.end_time.isoformat() if entry.end_time else "",
                    entry.duration or 0,
                    duration_hms,
                    entry.notes,
                    ", ".join(entry.tags),
                    "Yes" if entry.is_billable else "No"
                ])
            
            return output.getvalue()
        else:
            raise PluginError(f"Export format not supported: {format_type}")
    
    def _save_entries(self) -> None:
        """Save time entries to the data file."""
        config = self.get_config()
        self.data_file = config.get("data_file", "time_tracking_data.json")
        
        data = [entry.to_dict() for entry in self.entries]
        
        try:
            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(data)} time entries to {self.data_file}")
        except Exception as e:
            logger.error(f"Error saving time entries: {str(e)}")
    
    def _load_entries(self) -> None:
        """Load time entries from the data file."""
        config = self.get_config()
        self.data_file = config.get("data_file", "time_tracking_data.json")
        
        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)
            
            self.entries = [TimeEntry.from_dict(entry_data) for entry_data in data]
            logger.debug(f"Loaded {len(self.entries)} time entries from {self.data_file}")
        except FileNotFoundError:
            logger.info(f"No time tracking data file found at {self.data_file}")
            self.entries = []
        except Exception as e:
            logger.error(f"Error loading time entries: {str(e)}")
            self.entries = []
    
    def _on_task_status_change(self, task: Dict[str, Any], old_status: str, new_status: str) -> None:
        """
        Handle task status changes for time tracking.
        
        Args:
            task: The task that was updated
            old_status: The previous status
            new_status: The new status
        """
        config = self.get_config()
        if not config.get("track_status_changes", True):
            return
        
        # Example: Start tracking when a task moves to "in progress"
        if new_status == "in progress":
            # Only start if auto_track is enabled
            if config.get("auto_track", False):
                task_id = task["id"]
                if task_id not in self.active_entries:
                    try:
                        self.start_tracking(task_id, f"Auto-tracked: Status changed to {new_status}")
                    except PluginError:
                        # Already tracking this task
                        pass
        
        # Example: Stop tracking when a task is completed
        elif new_status == "complete":
            task_id = task["id"]
            if task_id in self.active_entries:
                self.stop_tracking(task_id)
    
    def _on_task_selected(self, task: Dict[str, Any]) -> None:
        """
        Handle task selection for automatic time tracking.
        
        Args:
            task: The task that was selected
        """
        config = self.get_config()
        if not config.get("auto_track", False):
            return
        
        task_id = task["id"]
        if task_id not in self.active_entries:
            try:
                self.start_tracking(task_id, "Auto-tracked: Task selected")
            except PluginError:
                # Already tracking this task
                pass
    
    def _on_task_deselected(self, task: Dict[str, Any]) -> None:
        """
        Handle task deselection for automatic time tracking.
        
        Args:
            task: The task that was deselected
        """
        config = self.get_config()
        if not config.get("auto_track", False):
            return
        
        task_id = task["id"]
        if task_id in self.active_entries:
            self.stop_tracking(task_id) 