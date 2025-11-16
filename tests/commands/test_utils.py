"""
Test suite for clickup_framework/commands/utils.py

Tests for argument parsing, shortcodes, and preset configurations.
"""

import unittest
import argparse
from unittest.mock import patch, Mock

from clickup_framework.commands.utils import create_format_options, add_common_args
from clickup_framework.components import FormatOptions


class TestPresetMapping(unittest.TestCase):
    """Test preset argument mapping (numeric and named)."""

    @patch('clickup_framework.commands.utils.get_context_manager')
    def test_numeric_preset_0_minimal(self, mock_context):
        """Test numeric preset 0 maps to minimal."""
        mock_context.return_value.get_ansi_output.return_value = True

        args = argparse.Namespace(preset='0', depth=None, show_emoji=None)
        options = create_format_options(args)

        # Minimal preset should show IDs but not tags or descriptions
        self.assertTrue(options.show_ids)
        self.assertFalse(options.show_tags)
        self.assertFalse(options.show_descriptions)
        self.assertIsInstance(options, FormatOptions)

    @patch('clickup_framework.commands.utils.get_context_manager')
    def test_numeric_preset_1_summary(self, mock_context):
        """Test numeric preset 1 maps to summary."""
        mock_context.return_value.get_ansi_output.return_value = True

        args = argparse.Namespace(preset='1', depth=None, show_emoji=None)
        options = create_format_options(args)

        # Summary preset should show tags
        self.assertTrue(options.show_tags)
        self.assertIsInstance(options, FormatOptions)

    @patch('clickup_framework.commands.utils.get_context_manager')
    def test_numeric_preset_2_detailed(self, mock_context):
        """Test numeric preset 2 maps to detailed."""
        mock_context.return_value.get_ansi_output.return_value = True

        args = argparse.Namespace(preset='2', depth=None, show_emoji=None)
        options = create_format_options(args)

        # Detailed preset should show descriptions
        self.assertTrue(options.show_descriptions)
        self.assertIsInstance(options, FormatOptions)

    @patch('clickup_framework.commands.utils.get_context_manager')
    def test_numeric_preset_3_full(self, mock_context):
        """Test numeric preset 3 maps to full."""
        mock_context.return_value.get_ansi_output.return_value = True

        args = argparse.Namespace(preset='3', depth=None, show_emoji=None)
        options = create_format_options(args)

        # Full preset should show everything
        self.assertTrue(options.show_ids)
        self.assertTrue(options.show_tags)
        self.assertTrue(options.show_descriptions)
        self.assertIsInstance(options, FormatOptions)

    @patch('clickup_framework.commands.utils.get_context_manager')
    def test_named_preset_minimal(self, mock_context):
        """Test named preset 'minimal' still works."""
        mock_context.return_value.get_ansi_output.return_value = True

        args = argparse.Namespace(preset='minimal', depth=None, show_emoji=None)
        options = create_format_options(args)

        self.assertTrue(options.show_ids)
        self.assertFalse(options.show_tags)
        self.assertFalse(options.show_descriptions)

    @patch('clickup_framework.commands.utils.get_context_manager')
    def test_named_preset_summary(self, mock_context):
        """Test named preset 'summary' still works."""
        mock_context.return_value.get_ansi_output.return_value = True

        args = argparse.Namespace(preset='summary', depth=None, show_emoji=None)
        options = create_format_options(args)

        self.assertTrue(options.show_tags)

    @patch('clickup_framework.commands.utils.get_context_manager')
    def test_named_preset_detailed(self, mock_context):
        """Test named preset 'detailed' still works."""
        mock_context.return_value.get_ansi_output.return_value = True

        args = argparse.Namespace(preset='detailed', depth=None, show_emoji=None)
        options = create_format_options(args)

        self.assertTrue(options.show_descriptions)

    @patch('clickup_framework.commands.utils.get_context_manager')
    def test_named_preset_full(self, mock_context):
        """Test named preset 'full' still works."""
        mock_context.return_value.get_ansi_output.return_value = True

        args = argparse.Namespace(preset='full', depth=None, show_emoji=None)
        options = create_format_options(args)

        self.assertTrue(options.show_ids)
        self.assertTrue(options.show_tags)
        self.assertTrue(options.show_descriptions)

    @patch('clickup_framework.commands.utils.get_context_manager')
    def test_preset_with_depth_override(self, mock_context):
        """Test preset can be overridden with depth argument."""
        mock_context.return_value.get_ansi_output.return_value = True

        args = argparse.Namespace(preset='1', depth=2, show_emoji=None)
        options = create_format_options(args)

        # Depth should override preset's max_depth
        self.assertEqual(options.max_depth, 2)

    @patch('clickup_framework.commands.utils.get_context_manager')
    def test_preset_with_emoji_override(self, mock_context):
        """Test preset can be overridden with emoji argument."""
        mock_context.return_value.get_ansi_output.return_value = True

        args = argparse.Namespace(preset='3', depth=None, show_emoji=False)
        options = create_format_options(args)

        # show_emoji should override preset's setting
        self.assertFalse(options.show_type_emoji)


class TestShortcodeArguments(unittest.TestCase):
    """Test shortcode arguments are registered correctly."""

    def test_add_common_args_registers_all_shortcodes(self):
        """Test that all shortcodes are registered with argparse."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')

        # Add common args
        add_common_args(subparser)

        # Parse with shortcodes
        args = subparser.parse_args([
            '-p', '1',
            '-i',
            '-t',
            '-D',
            '-d',
            '-dd',
            '-c', '3',
            '-C',
            '-sc',
            '-ne',
            '-cf',
            '-nt'
        ])

        # Verify all shortcodes are parsed correctly
        self.assertEqual(args.preset, '1')
        self.assertTrue(args.show_ids)
        self.assertTrue(args.show_tags)
        self.assertTrue(args.show_descriptions)
        self.assertTrue(args.full_descriptions)
        self.assertTrue(args.show_dates)
        self.assertEqual(args.show_comments, 3)
        self.assertTrue(args.include_completed)
        self.assertTrue(args.show_closed_only)
        self.assertFalse(args.show_emoji)  # --no-emoji sets to False
        self.assertTrue(args.show_custom_fields)
        self.assertFalse(args.show_tips)  # --no-tips sets to False

    def test_shortcode_p_for_preset(self):
        """Test -p shortcode for --preset."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        # Test numeric preset
        args = subparser.parse_args(['-p', '0'])
        self.assertEqual(args.preset, '0')

        # Test named preset
        args = subparser.parse_args(['-p', 'summary'])
        self.assertEqual(args.preset, 'summary')

    def test_shortcode_i_for_show_ids(self):
        """Test -i shortcode for --show-ids."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['-i'])
        self.assertTrue(args.show_ids)

    def test_shortcode_t_for_show_tags(self):
        """Test -t shortcode for --show-tags."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['-t'])
        self.assertTrue(args.show_tags)

    def test_shortcode_D_for_show_descriptions(self):
        """Test -D shortcode for --show-descriptions."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['-D'])
        self.assertTrue(args.show_descriptions)

    def test_shortcode_d_for_full_descriptions(self):
        """Test -d shortcode for --full-descriptions."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['-d'])
        self.assertTrue(args.full_descriptions)

    def test_shortcode_dd_for_show_dates(self):
        """Test -dd shortcode for --show-dates."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['-dd'])
        self.assertTrue(args.show_dates)

    def test_shortcode_c_for_show_comments(self):
        """Test -c shortcode for --show-comments."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['-c', '10'])
        self.assertEqual(args.show_comments, 10)

    def test_shortcode_C_for_include_completed(self):
        """Test -C shortcode for --include-completed."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['-C'])
        self.assertTrue(args.include_completed)

    def test_shortcode_sc_for_show_closed(self):
        """Test -sc shortcode for --show-closed."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['-sc'])
        self.assertTrue(args.show_closed_only)

    def test_shortcode_ne_for_no_emoji(self):
        """Test -ne shortcode for --no-emoji."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['-ne'])
        self.assertFalse(args.show_emoji)

    def test_shortcode_cf_for_show_custom_fields(self):
        """Test -cf shortcode for --show-custom-fields."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['-cf'])
        self.assertTrue(args.show_custom_fields)

    def test_shortcode_nt_for_no_tips(self):
        """Test -nt shortcode for --no-tips."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['-nt'])
        self.assertFalse(args.show_tips)


class TestLongFormArguments(unittest.TestCase):
    """Test long-form arguments still work alongside shortcodes."""

    def test_long_form_preset(self):
        """Test --preset still works."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['--preset', 'detailed'])
        self.assertEqual(args.preset, 'detailed')

    def test_long_form_show_ids(self):
        """Test --show-ids still works."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['--show-ids'])
        self.assertTrue(args.show_ids)

    def test_long_form_show_tags(self):
        """Test --show-tags still works."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        args = subparser.parse_args(['--show-tags'])
        self.assertTrue(args.show_tags)

    def test_mixed_short_and_long_forms(self):
        """Test mixing short and long form arguments."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        # Mix shortcodes and long-form
        args = subparser.parse_args([
            '-p', '2',  # shortcode
            '--show-ids',  # long-form
            '-D',  # shortcode
            '--show-dates',  # long-form
            '-c', '5'  # shortcode
        ])

        self.assertEqual(args.preset, '2')
        self.assertTrue(args.show_ids)
        self.assertTrue(args.show_descriptions)
        self.assertTrue(args.show_dates)
        self.assertEqual(args.show_comments, 5)


class TestCreateFormatOptionsWithShortcodes(unittest.TestCase):
    """Test create_format_options works correctly with shortcode arguments."""

    @patch('clickup_framework.commands.utils.get_context_manager')
    def test_create_format_options_with_individual_flags(self, mock_context):
        """Test create_format_options with individual flags (no preset)."""
        mock_context.return_value.get_ansi_output.return_value = True

        args = argparse.Namespace(
            preset=None,
            colorize=True,
            show_ids=True,
            show_tags=False,
            show_descriptions=True,
            full_descriptions=False,
            show_dates=True,
            show_comments=3,
            include_completed=True,
            show_closed_only=False,
            show_emoji=False,
            show_custom_fields=True,
            depth=None
        )

        options = create_format_options(args)

        self.assertTrue(options.colorize_output)
        self.assertTrue(options.show_ids)
        self.assertFalse(options.show_tags)
        self.assertTrue(options.show_descriptions)
        self.assertTrue(options.show_dates)
        self.assertEqual(options.show_comments, 3)
        self.assertTrue(options.include_completed)
        self.assertFalse(options.show_closed_only)
        self.assertFalse(options.show_type_emoji)
        self.assertTrue(options.show_custom_fields)

    @patch('clickup_framework.commands.utils.get_context_manager')
    def test_create_format_options_full_descriptions_implies_show_descriptions(self, mock_context):
        """Test that full_descriptions flag implies show_descriptions."""
        mock_context.return_value.get_ansi_output.return_value = True

        args = argparse.Namespace(
            preset=None,
            colorize=None,
            show_ids=False,
            show_tags=True,
            show_descriptions=False,
            full_descriptions=True,  # This should imply show_descriptions
            show_dates=False,
            show_comments=0,
            include_completed=False,
            show_closed_only=False,
            show_emoji=True,
            show_custom_fields=False,
            depth=None
        )

        options = create_format_options(args)

        # full_descriptions should imply show_descriptions
        self.assertTrue(options.show_descriptions)
        self.assertEqual(options.description_length, 10000)  # Full length


class TestPresetChoices(unittest.TestCase):
    """Test that argparse validates preset choices correctly."""

    def test_valid_numeric_presets(self):
        """Test valid numeric preset values."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        # All numeric presets should be valid
        for preset in ['0', '1', '2', '3']:
            args = subparser.parse_args(['-p', preset])
            self.assertEqual(args.preset, preset)

    def test_valid_named_presets(self):
        """Test valid named preset values."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        # All named presets should be valid
        for preset in ['minimal', 'summary', 'detailed', 'full']:
            args = subparser.parse_args(['-p', preset])
            self.assertEqual(args.preset, preset)

    def test_invalid_preset_value(self):
        """Test invalid preset value raises error."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        # Invalid preset should raise SystemExit (argparse error)
        with self.assertRaises(SystemExit):
            subparser.parse_args(['-p', 'invalid'])

    def test_invalid_numeric_preset(self):
        """Test invalid numeric preset value raises error."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        subparser = subparsers.add_parser('test')
        add_common_args(subparser)

        # Preset 4 is not valid (only 0-3)
        with self.assertRaises(SystemExit):
            subparser.parse_args(['-p', '4'])


if __name__ == "__main__":
    unittest.main(verbosity=2)
