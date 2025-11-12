"""Configuration management for Git Overflow.

Handles loading and validation of overflow workflow configuration from YAML.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass


@dataclass
class StatusMapping:
    """Maps Git actions to ClickUp status changes."""
    on_commit: Optional[str] = None
    on_push: Optional[str] = None
    on_pr_create: Optional[str] = None
    on_pr_merge: Optional[str] = None
    on_wip: Optional[str] = None
    on_complete: Optional[str] = None


@dataclass
class OverflowConfig:
    """
    Configuration for Git Overflow workflows.

    Defines default behavior, status mappings, and workflow settings.
    """
    # Workflow defaults
    auto_push: bool = True
    auto_update_clickup: bool = True
    default_remote: str = "origin"

    # Status mappings
    status_mapping: StatusMapping = field(default_factory=StatusMapping)

    # Comment templates
    commit_comment_template: str = "✅ Committed: {commit_sha_short}\n📝 {commit_message}\n🔗 {commit_url}"
    pr_comment_template: str = "🔀 Pull Request: {pr_url}\n📝 {pr_title}"
    complete_comment_template: str = "✅ Merged and completed\n🔗 {commit_url}"

    # Workflow behavior
    require_task_id: bool = True
    validate_branch_name: bool = True
    branch_prefix: Optional[str] = None

    # Safety settings
    dry_run: bool = False
    confirm_before_push: bool = False

    # Git settings
    git_author_name: Optional[str] = None
    git_author_email: Optional[str] = None


# Default configuration
DEFAULT_CONFIG = OverflowConfig(
    auto_push=True,
    auto_update_clickup=True,
    default_remote="origin",
    status_mapping=StatusMapping(
        on_commit="in progress",
        on_push="in progress",
        on_pr_create="in review",
        on_pr_merge="closed",
        on_wip="in progress",
        on_complete="closed"
    ),
    commit_comment_template="✅ Committed: {commit_sha_short}\n📝 {commit_message}\n🔗 {commit_url}",
    pr_comment_template="🔀 Pull Request: {pr_url}\n📝 {pr_title}",
    complete_comment_template="✅ Merged and completed\n🔗 {commit_url}",
    require_task_id=True,
    validate_branch_name=True,
    branch_prefix=None,
    dry_run=False,
    confirm_before_push=False
)


def find_config_file(start_path: str = ".") -> Optional[Path]:
    """
    Search for overflow config file in current directory and parents.

    Looks for:
    - .overflow.yaml
    - .overflow.yml
    - overflow.yaml
    - overflow.yml

    Args:
        start_path: Directory to start search from

    Returns:
        Path to config file, or None if not found
    """
    config_filenames = ['.overflow.yaml', '.overflow.yml', 'overflow.yaml', 'overflow.yml']

    current_path = Path(start_path).resolve()

    # Search up to repository root or filesystem root
    while True:
        for filename in config_filenames:
            config_path = current_path / filename
            if config_path.exists():
                return config_path

        # Check if we've reached filesystem root or git repo root
        parent = current_path.parent
        if parent == current_path:  # Filesystem root
            break

        # Check for .git directory (repo root)
        if (current_path / '.git').exists():
            break

        current_path = parent

    return None


def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """
    Load YAML configuration from file.

    Args:
        config_path: Path to YAML config file

    Returns:
        Parsed configuration dict

    Raises:
        ConfigError: If file cannot be read or parsed
    """
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        if config_data is None:
            return {}

        if not isinstance(config_data, dict):
            raise ConfigError(f"Config file must contain a YAML dictionary, got {type(config_data)}")

        return config_data

    except FileNotFoundError:
        raise ConfigError(f"Config file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML config: {e}")
    except Exception as e:
        raise ConfigError(f"Failed to load config: {e}")


def validate_config(config_data: Dict[str, Any]) -> None:
    """
    Validate configuration data.

    Args:
        config_data: Configuration dictionary

    Raises:
        ConfigError: If configuration is invalid
    """
    # Validate boolean fields
    bool_fields = ['auto_push', 'auto_update_clickup', 'require_task_id',
                   'validate_branch_name', 'dry_run', 'confirm_before_push']

    for field in bool_fields:
        if field in config_data and not isinstance(config_data[field], bool):
            raise ConfigError(f"Field '{field}' must be a boolean, got {type(config_data[field])}")

    # Validate string fields
    string_fields = ['default_remote', 'commit_comment_template', 'pr_comment_template',
                    'complete_comment_template', 'branch_prefix', 'git_author_name', 'git_author_email']

    for field in string_fields:
        if field in config_data and config_data[field] is not None:
            if not isinstance(config_data[field], str):
                raise ConfigError(f"Field '{field}' must be a string, got {type(config_data[field])}")

    # Validate status_mapping if present
    if 'status_mapping' in config_data:
        if not isinstance(config_data['status_mapping'], dict):
            raise ConfigError(f"'status_mapping' must be a dictionary")

        valid_status_keys = ['on_commit', 'on_push', 'on_pr_create', 'on_pr_merge', 'on_wip', 'on_complete']
        for key in config_data['status_mapping'].keys():
            if key not in valid_status_keys:
                raise ConfigError(f"Invalid status_mapping key: {key}. Valid keys: {valid_status_keys}")


def merge_config(base: OverflowConfig, overrides: Dict[str, Any]) -> OverflowConfig:
    """
    Merge configuration overrides into base config.

    Args:
        base: Base configuration
        overrides: Dictionary of override values

    Returns:
        New OverflowConfig with merged values
    """
    # Start with base values
    merged = OverflowConfig(
        auto_push=overrides.get('auto_push', base.auto_push),
        auto_update_clickup=overrides.get('auto_update_clickup', base.auto_update_clickup),
        default_remote=overrides.get('default_remote', base.default_remote),
        commit_comment_template=overrides.get('commit_comment_template', base.commit_comment_template),
        pr_comment_template=overrides.get('pr_comment_template', base.pr_comment_template),
        complete_comment_template=overrides.get('complete_comment_template', base.complete_comment_template),
        require_task_id=overrides.get('require_task_id', base.require_task_id),
        validate_branch_name=overrides.get('validate_branch_name', base.validate_branch_name),
        branch_prefix=overrides.get('branch_prefix', base.branch_prefix),
        dry_run=overrides.get('dry_run', base.dry_run),
        confirm_before_push=overrides.get('confirm_before_push', base.confirm_before_push),
        git_author_name=overrides.get('git_author_name', base.git_author_name),
        git_author_email=overrides.get('git_author_email', base.git_author_email),
    )

    # Merge status_mapping if present
    if 'status_mapping' in overrides:
        status_overrides = overrides['status_mapping']
        merged.status_mapping = StatusMapping(
            on_commit=status_overrides.get('on_commit', base.status_mapping.on_commit),
            on_push=status_overrides.get('on_push', base.status_mapping.on_push),
            on_pr_create=status_overrides.get('on_pr_create', base.status_mapping.on_pr_create),
            on_pr_merge=status_overrides.get('on_pr_merge', base.status_mapping.on_pr_merge),
            on_wip=status_overrides.get('on_wip', base.status_mapping.on_wip),
            on_complete=status_overrides.get('on_complete', base.status_mapping.on_complete),
        )

    return merged


def load_config(config_path: Optional[Path] = None, search: bool = True) -> OverflowConfig:
    """
    Load overflow configuration from file or use defaults.

    Args:
        config_path: Explicit path to config file (optional)
        search: Whether to search for config file if path not provided

    Returns:
        OverflowConfig instance

    Raises:
        ConfigError: If config file is specified but invalid
    """
    # If explicit path provided, use it
    if config_path:
        config_data = load_yaml_config(config_path)
        validate_config(config_data)
        return merge_config(DEFAULT_CONFIG, config_data)

    # Search for config file if requested
    if search:
        found_path = find_config_file()
        if found_path:
            config_data = load_yaml_config(found_path)
            validate_config(config_data)
            return merge_config(DEFAULT_CONFIG, config_data)

    # No config file found or search disabled, use defaults
    return DEFAULT_CONFIG


def get_status_for_action(config: OverflowConfig, action: str) -> Optional[str]:
    """
    Get the ClickUp status to set for a given action.

    Args:
        config: Overflow configuration
        action: Action name (commit, push, pr_create, pr_merge, wip, complete)

    Returns:
        Status name or None if no mapping configured
    """
    action_map = {
        'commit': config.status_mapping.on_commit,
        'push': config.status_mapping.on_push,
        'pr_create': config.status_mapping.on_pr_create,
        'pr_merge': config.status_mapping.on_pr_merge,
        'wip': config.status_mapping.on_wip,
        'complete': config.status_mapping.on_complete,
    }

    return action_map.get(action)
