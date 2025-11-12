"""Tests for configuration management."""

import unittest
import tempfile
import os
from pathlib import Path
from clickup_framework.git.config import (
    OverflowConfig,
    StatusMapping,
    ConfigError,
    DEFAULT_CONFIG,
    find_config_file,
    load_yaml_config,
    validate_config,
    merge_config,
    load_config,
    get_status_for_action,
)


class TestStatusMapping(unittest.TestCase):
    """Tests for StatusMapping dataclass."""

    def test_default_values(self):
        """Test that StatusMapping can be created with defaults."""
        mapping = StatusMapping()

        self.assertIsNone(mapping.on_commit)
        self.assertIsNone(mapping.on_push)
        self.assertIsNone(mapping.on_pr_create)
        self.assertIsNone(mapping.on_pr_merge)
        self.assertIsNone(mapping.on_wip)
        self.assertIsNone(mapping.on_complete)

    def test_custom_values(self):
        """Test StatusMapping with custom values."""
        mapping = StatusMapping(
            on_commit="in progress",
            on_push="in progress",
            on_pr_create="in review"
        )

        self.assertEqual(mapping.on_commit, "in progress")
        self.assertEqual(mapping.on_push, "in progress")
        self.assertEqual(mapping.on_pr_create, "in review")


class TestOverflowConfig(unittest.TestCase):
    """Tests for OverflowConfig dataclass."""

    def test_default_config_exists(self):
        """Test that DEFAULT_CONFIG is properly initialized."""
        self.assertIsInstance(DEFAULT_CONFIG, OverflowConfig)
        self.assertTrue(DEFAULT_CONFIG.auto_push)
        self.assertTrue(DEFAULT_CONFIG.auto_update_clickup)
        self.assertEqual(DEFAULT_CONFIG.default_remote, "origin")

    def test_default_status_mapping(self):
        """Test that default status mapping is configured."""
        self.assertIsNotNone(DEFAULT_CONFIG.status_mapping)
        self.assertEqual(DEFAULT_CONFIG.status_mapping.on_commit, "in progress")
        self.assertEqual(DEFAULT_CONFIG.status_mapping.on_pr_create, "in review")
        self.assertEqual(DEFAULT_CONFIG.status_mapping.on_complete, "closed")


class TestFindConfigFile(unittest.TestCase):
    """Tests for find_config_file function."""

    def test_find_config_in_current_dir(self):
        """Test finding config file in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / '.overflow.yaml'
            config_path.touch()

            found = find_config_file(tmpdir)

            self.assertEqual(found, config_path)

    def test_find_config_in_parent_dir(self):
        """Test finding config file in parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'overflow.yml'
            config_path.touch()

            subdir = Path(tmpdir) / 'subdir'
            subdir.mkdir()

            found = find_config_file(str(subdir))

            self.assertEqual(found, config_path)

    def test_no_config_found(self):
        """Test that None is returned when no config file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            found = find_config_file(tmpdir)

            self.assertIsNone(found)

    def test_prefer_dotfile(self):
        """Test that dotfiles are preferred over regular files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dotfile = Path(tmpdir) / '.overflow.yaml'
            regular = Path(tmpdir) / 'overflow.yaml'
            dotfile.touch()
            regular.touch()

            found = find_config_file(tmpdir)

            self.assertEqual(found, dotfile)


class TestLoadYAMLConfig(unittest.TestCase):
    """Tests for load_yaml_config function."""

    def test_load_valid_yaml(self):
        """Test loading valid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
auto_push: false
default_remote: upstream
status_mapping:
  on_commit: working
  on_push: pushed
""")
            f.flush()

            try:
                config = load_yaml_config(Path(f.name))

                self.assertFalse(config['auto_push'])
                self.assertEqual(config['default_remote'], 'upstream')
                self.assertEqual(config['status_mapping']['on_commit'], 'working')
            finally:
                os.unlink(f.name)

    def test_load_empty_yaml(self):
        """Test loading empty YAML file returns empty dict."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            f.flush()

            try:
                config = load_yaml_config(Path(f.name))
                self.assertEqual(config, {})
            finally:
                os.unlink(f.name)

    def test_load_nonexistent_file(self):
        """Test that loading nonexistent file raises ConfigError."""
        with self.assertRaises(ConfigError) as ctx:
            load_yaml_config(Path('/nonexistent/file.yaml'))

        self.assertIn("not found", str(ctx.exception))

    def test_load_invalid_yaml(self):
        """Test that invalid YAML raises ConfigError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()

            try:
                with self.assertRaises(ConfigError) as ctx:
                    load_yaml_config(Path(f.name))

                self.assertIn("parse", str(ctx.exception).lower())
            finally:
                os.unlink(f.name)


class TestValidateConfig(unittest.TestCase):
    """Tests for validate_config function."""

    def test_valid_config(self):
        """Test that valid config passes validation."""
        config = {
            'auto_push': True,
            'default_remote': 'origin',
            'status_mapping': {
                'on_commit': 'in progress'
            }
        }

        # Should not raise
        validate_config(config)

    def test_invalid_boolean_field(self):
        """Test that non-boolean value for boolean field raises error."""
        config = {'auto_push': 'yes'}

        with self.assertRaises(ConfigError) as ctx:
            validate_config(config)

        self.assertIn("must be a boolean", str(ctx.exception))

    def test_invalid_string_field(self):
        """Test that non-string value for string field raises error."""
        config = {'default_remote': 123}

        with self.assertRaises(ConfigError) as ctx:
            validate_config(config)

        self.assertIn("must be a string", str(ctx.exception))

    def test_invalid_status_mapping_type(self):
        """Test that non-dict status_mapping raises error."""
        config = {'status_mapping': 'invalid'}

        with self.assertRaises(ConfigError) as ctx:
            validate_config(config)

        self.assertIn("must be a dictionary", str(ctx.exception))

    def test_invalid_status_mapping_key(self):
        """Test that invalid status_mapping key raises error."""
        config = {'status_mapping': {'invalid_key': 'value'}}

        with self.assertRaises(ConfigError) as ctx:
            validate_config(config)

        self.assertIn("Invalid status_mapping key", str(ctx.exception))


class TestMergeConfig(unittest.TestCase):
    """Tests for merge_config function."""

    def test_merge_simple_overrides(self):
        """Test merging simple field overrides."""
        base = DEFAULT_CONFIG
        overrides = {
            'auto_push': False,
            'default_remote': 'upstream'
        }

        merged = merge_config(base, overrides)

        self.assertFalse(merged.auto_push)
        self.assertEqual(merged.default_remote, 'upstream')
        # Other fields should remain from base
        self.assertEqual(merged.auto_update_clickup, base.auto_update_clickup)

    def test_merge_status_mapping(self):
        """Test merging status_mapping."""
        base = DEFAULT_CONFIG
        overrides = {
            'status_mapping': {
                'on_commit': 'working',
                'on_push': 'pushed'
            }
        }

        merged = merge_config(base, overrides)

        self.assertEqual(merged.status_mapping.on_commit, 'working')
        self.assertEqual(merged.status_mapping.on_push, 'pushed')
        # Other status mappings should remain from base
        self.assertEqual(merged.status_mapping.on_pr_create, base.status_mapping.on_pr_create)

    def test_merge_empty_overrides(self):
        """Test merging with empty overrides."""
        base = DEFAULT_CONFIG
        overrides = {}

        merged = merge_config(base, overrides)

        # Should be identical to base
        self.assertEqual(merged.auto_push, base.auto_push)
        self.assertEqual(merged.default_remote, base.default_remote)


class TestLoadConfig(unittest.TestCase):
    """Tests for load_config function."""

    def test_load_default_config_no_file(self):
        """Test loading config when no file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set cwd to temp dir with no config file
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                config = load_config(search=True)

                # Should return DEFAULT_CONFIG
                self.assertEqual(config.auto_push, DEFAULT_CONFIG.auto_push)
                self.assertEqual(config.default_remote, DEFAULT_CONFIG.default_remote)
            finally:
                os.chdir(original_cwd)

    def test_load_explicit_config_file(self):
        """Test loading explicit config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("auto_push: false\n")
            f.flush()

            try:
                config = load_config(config_path=Path(f.name), search=False)

                self.assertFalse(config.auto_push)
            finally:
                os.unlink(f.name)

    def test_load_config_without_search(self):
        """Test loading config without search returns defaults."""
        config = load_config(search=False)

        self.assertEqual(config.auto_push, DEFAULT_CONFIG.auto_push)


class TestGetStatusForAction(unittest.TestCase):
    """Tests for get_status_for_action function."""

    def test_get_commit_status(self):
        """Test getting status for commit action."""
        config = DEFAULT_CONFIG

        status = get_status_for_action(config, 'commit')

        self.assertEqual(status, 'in progress')

    def test_get_pr_create_status(self):
        """Test getting status for PR creation."""
        config = DEFAULT_CONFIG

        status = get_status_for_action(config, 'pr_create')

        self.assertEqual(status, 'in review')

    def test_get_complete_status(self):
        """Test getting status for complete action."""
        config = DEFAULT_CONFIG

        status = get_status_for_action(config, 'complete')

        self.assertEqual(status, 'closed')

    def test_get_invalid_action(self):
        """Test that invalid action returns None."""
        config = DEFAULT_CONFIG

        status = get_status_for_action(config, 'invalid_action')

        self.assertIsNone(status)


if __name__ == '__main__':
    unittest.main()
