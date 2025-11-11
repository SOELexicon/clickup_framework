"""
Configuration management for parent task automation.

Handles loading, saving, and validating automation configuration.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List


@dataclass
class AutomationConfig:
    """
    Configuration for parent task auto-update automation.

    Attributes:
        enabled: Global enable/disable flag
        post_comment: Whether to post automation comments
        comment_template: Template string for comments
        trigger_statuses: List of subtask statuses that trigger automation
        parent_inactive_statuses: Parent must be in one of these to update
        parent_target_status: Status to set parent task to
        update_delay_seconds: Delay before updating (for batching)
        retry_on_failure: Whether to retry failed updates
        max_retries: Maximum retry attempts
        log_automation_events: Whether to log all automation events
        verbose_output: Show detailed automation output in CLI
    """

    enabled: bool = True
    post_comment: bool = True
    comment_template: str = "🤖 **Automated Update:** Status changed to '{new_status}' because subtask '{subtask_name}' started development."
    trigger_statuses: List[str] = field(default_factory=lambda: [
        "in progress",
        "in development",
        "in dev",
        "active",
        "working",
        "started"
    ])
    parent_inactive_statuses: List[str] = field(default_factory=lambda: [
        "to do",
        "todo",
        "backlog",
        "not started",
        "open",
        "ready",
        "planned"
    ])
    parent_target_status: str = "in progress"
    update_delay_seconds: int = 2
    retry_on_failure: bool = True
    max_retries: int = 3
    log_automation_events: bool = True
    verbose_output: bool = False

    def to_dict(self):
        """Convert config to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'AutomationConfig':
        """Create config from dictionary."""
        # Filter out any extra keys not in dataclass
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)


def get_config_path() -> Path:
    """Get path to automation configuration file."""
    config_dir = Path.home() / ".clickup"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "automation_config.json"


def load_automation_config() -> AutomationConfig:
    """
    Load automation configuration from file.

    Returns:
        AutomationConfig instance with loaded or default values

    Change History:
        v1.0.0 - Initial implementation
    """
    config_path = get_config_path()

    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)

            # Handle nested structure for backward compatibility
            if 'automation' in data and 'parent_update' in data['automation']:
                config_data = data['automation']['parent_update']
            else:
                config_data = data

            return AutomationConfig.from_dict(config_data)

        except (json.JSONDecodeError, IOError, KeyError) as e:
            # If file is corrupted, use defaults
            print(f"Warning: Could not load automation config: {e}. Using defaults.")
            return AutomationConfig()
    else:
        # No config file, use defaults
        return AutomationConfig()


def save_automation_config(config: AutomationConfig) -> None:
    """
    Save automation configuration to file.

    Args:
        config: AutomationConfig instance to save

    Change History:
        v1.0.0 - Initial implementation
    """
    config_path = get_config_path()

    # Create nested structure
    data = {
        "automation": {
            "parent_update": config.to_dict()
        }
    }

    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)

    # Set file permissions to user-only (0600)
    try:
        os.chmod(config_path, 0o600)
    except OSError:
        # On Windows, chmod may not work as expected
        pass


def update_config_value(key: str, value) -> None:
    """
    Update a single configuration value.

    Args:
        key: Configuration key to update
        value: New value

    Change History:
        v1.0.0 - Initial implementation
    """
    config = load_automation_config()

    if hasattr(config, key):
        setattr(config, key, value)
        save_automation_config(config)
    else:
        raise ValueError(f"Invalid configuration key: {key}")
