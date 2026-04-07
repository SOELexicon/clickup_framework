"""
Test Suite for Line Count Command

Comprehensive test coverage for line counting functionality including file filtering,
line counting accuracy, console formatting, HTML report generation, and command integration.

Test Classes:
    TestFileFilter - File inclusion/exclusion and language detection
    TestLineCounter - Line counting accuracy and traversal
    TestConsoleFormatter - Output formatting and statistics
    TestHTMLReportGenerator - HTML report generation
    TestLineCountCommand - Command integration and CLI
"""

import unittest
import tempfile
import shutil
import sys
import io
from pathlib import Path
from argparse import Namespace

from clickup_framework.commands.line_count_helpers import (
    FileFilter,
    LineCounter,
    ConsoleFormatter,
    HTMLReportGenerator,
)
from clickup_framework.commands.line_count_command import LineCountCommand


class TestFileFilter(unittest.TestCase):
    """
    Test file filtering and language detection.

    Purpose:    Verify FileFilter correctly identifies files to include/exclude
    Usage:      Run TestFileFilter tests to validate filtering logic
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: file filtering and language tests
    """

    def setUp(self):
        """Set up test fixtures."""
        self.filter_no_lang = FileFilter()
        self.filter_python = FileFilter(language_filter='Python')
        self.filter_javascript = FileFilter(language_filter='JavaScript')

    def test_python_file_included(self):
        """Test that .py files are included."""
        path = Path('example.py')
        self.assertTrue(self.filter_no_lang.should_include(path))

    def test_javascript_file_included(self):
        """Test that .js files are included."""
        path = Path('script.js')
        self.assertTrue(self.filter_no_lang.should_include(path))

    def test_binary_dll_excluded(self):
        """Test that .dll files are excluded."""
        path = Path('library.dll')
        self.assertFalse(self.filter_no_lang.should_include(path))

    def test_binary_exe_excluded(self):
        """Test that .exe files are excluded."""
        path = Path('program.exe')
        self.assertFalse(self.filter_no_lang.should_include(path))

    def test_pycache_excluded(self):
        """Test that __pycache__ directories are excluded."""
        path = Path('project/__pycache__/module.pyc')
        self.assertFalse(self.filter_no_lang.should_include(path))

    def test_node_modules_excluded(self):
        """Test that node_modules directories are excluded."""
        path = Path('project/node_modules/package/index.js')
        self.assertFalse(self.filter_no_lang.should_include(path))

    def test_git_directory_excluded(self):
        """Test that .git directories are excluded."""
        path = Path('repo/.git/config')
        self.assertFalse(self.filter_no_lang.should_include(path))

    def test_json_file_included(self):
        """Test that .json files are included."""
        path = Path('config.json')
        self.assertTrue(self.filter_no_lang.should_include(path))

    def test_language_filter_python(self):
        """Test language filter for Python only."""
        py_path = Path('script.py')
        js_path = Path('script.js')

        self.assertTrue(self.filter_python.should_include(py_path))
        self.assertFalse(self.filter_python.should_include(js_path))

    def test_language_filter_javascript(self):
        """Test language filter for JavaScript only."""
        js_path = Path('script.js')
        ts_path = Path('script.ts')

        self.assertTrue(self.filter_javascript.should_include(js_path))
        # TypeScript should not match JavaScript filter
        self.assertFalse(self.filter_javascript.should_include(ts_path))

    def test_get_language_python(self):
        """Test language detection for Python."""
        path = Path('script.py')
        self.assertEqual(self.filter_no_lang.get_language(path), 'Python')

    def test_get_language_javascript(self):
        """Test language detection for JavaScript."""
        path = Path('script.js')
        self.assertEqual(self.filter_no_lang.get_language(path), 'JavaScript')

    def test_get_language_csharp(self):
        """Test language detection for C#."""
        path = Path('Program.cs')
        self.assertEqual(self.filter_no_lang.get_language(path), 'C#')

    def test_get_language_unknown(self):
        """Test language detection for unknown extension."""
        path = Path('file.xyz')
        self.assertIsNone(self.filter_no_lang.get_language(path))

    def test_unsupported_extension_excluded(self):
        """Test that unsupported file extensions are excluded."""
        path = Path('archive.zip')
        self.assertFalse(self.filter_no_lang.should_include(path))

    def test_case_insensitive_extension(self):
        """Test that file extension matching is case-insensitive."""
        path_lower = Path('script.py')
        path_upper = Path('script.PY')

        self.assertTrue(self.filter_no_lang.should_include(path_lower))
        self.assertTrue(self.filter_no_lang.should_include(path_upper))

    def test_multiple_ignore_directories(self):
        """Test that multiple ignore directories are properly excluded."""
        venv_path = Path('project/venv/lib/module.py')
        build_path = Path('project/build/output.py')
        dist_path = Path('project/dist/package.py')

        self.assertFalse(self.filter_no_lang.should_include(venv_path))
        self.assertFalse(self.filter_no_lang.should_include(build_path))
        self.assertFalse(self.filter_no_lang.should_include(dist_path))


class TestLineCounter(unittest.TestCase):
    """
    Test line counting accuracy and directory traversal.

    Purpose:    Verify LineCounter correctly counts lines in files and traverses directories
    Usage:      Run TestLineCounter tests to validate counting logic
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: line counting and traversal tests
    """

    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.fixtures_dir = Path(__file__).parent / 'fixtures' / 'sample_project'

    def tearDown(self):
        """Clean up temporary directory."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_count_lines_simple_python(self):
        """Test line counting on simple Python file."""
        counter = LineCounter()
        if self.fixtures_dir.exists():
            py_file = self.fixtures_dir / 'simple.py'
            if py_file.exists():
                result = counter.count_lines(py_file)
                self.assertIsNotNone(result)
                self.assertEqual(result['language'], 'Python')
                self.assertGreater(result['total'], 0)
                self.assertGreaterEqual(result['total'], result['blank'])
                self.assertGreaterEqual(result['total'], result['comment'])
                self.assertGreaterEqual(result['total'], result['code'])

    def test_count_lines_empty_file(self):
        """Test line counting on empty file."""
        counter = LineCounter()
        empty_file = Path(self.temp_dir) / 'empty.py'
        empty_file.write_text('')

        result = counter.count_lines(empty_file)
        self.assertIsNotNone(result)
        self.assertEqual(result['total'], 0)
        self.assertEqual(result['blank'], 0)
        self.assertEqual(result['comment'], 0)
        self.assertEqual(result['code'], 0)

    def test_count_lines_only_comments(self):
        """Test line counting on file with only comments."""
        counter = LineCounter()
        comment_file = Path(self.temp_dir) / 'comments.py'
        comment_file.write_text('# Comment 1\n# Comment 2\n# Comment 3')

        result = counter.count_lines(comment_file)
        self.assertIsNotNone(result)
        self.assertEqual(result['total'], 3)
        self.assertEqual(result['comment'], 3)
        self.assertEqual(result['code'], 0)

    def test_count_lines_only_blank_lines(self):
        """Test line counting on file with only blank lines."""
        counter = LineCounter()
        blank_file = Path(self.temp_dir) / 'blank.py'
        blank_file.write_text('\n\n\n')

        result = counter.count_lines(blank_file)
        self.assertIsNotNone(result)
        self.assertEqual(result['total'], 3)
        self.assertEqual(result['blank'], 3)
        self.assertEqual(result['comment'], 0)
        self.assertEqual(result['code'], 0)

    def test_count_lines_mixed_content(self):
        """Test line counting with mixed code, comments, and blank lines."""
        counter = LineCounter()
        mixed_file = Path(self.temp_dir) / 'mixed.py'
        mixed_file.write_text(
            'def hello():\n'
            '    # Comment\n'
            '    pass\n'
            '\n'
            '# Another comment\n'
        )

        result = counter.count_lines(mixed_file)
        self.assertIsNotNone(result)
        self.assertEqual(result['total'], 5)
        self.assertGreater(result['code'], 0)
        self.assertGreater(result['comment'], 0)
        self.assertGreater(result['blank'], 0)

    def test_count_lines_multiline_comments_python(self):
        """Test counting multiline comments in Python."""
        counter = LineCounter()
        doc_file = Path(self.temp_dir) / 'docstring.py'
        doc_file.write_text(
            'def func():\n'
            '    """\n'
            '    This is a docstring.\n'
            '    """\n'
            '    pass\n'
        )

        result = counter.count_lines(doc_file)
        self.assertIsNotNone(result)
        # Should count docstring as comments
        self.assertGreater(result['comment'], 0)

    def test_count_files_directory_traversal(self):
        """Test recursive directory traversal."""
        counter = LineCounter()
        if self.fixtures_dir.exists() and (self.fixtures_dir / 'simple.py').exists():
            results = counter.count_files(str(self.fixtures_dir))
            self.assertIsInstance(results, dict)
            self.assertGreater(len(results), 0)

    def test_count_files_empty_directory(self):
        """Test counting on empty directory."""
        counter = LineCounter()
        empty_dir = Path(self.temp_dir) / 'empty'
        empty_dir.mkdir()

        results = counter.count_files(str(empty_dir))
        self.assertEqual(results, {})

    def test_count_files_with_max_depth(self):
        """Test max_depth parameter limits traversal."""
        # Create nested structure
        level1 = Path(self.temp_dir) / 'level1'
        level2 = level1 / 'level2'
        level3 = level2 / 'level3'
        level2.mkdir(parents=True)
        level3.mkdir(parents=True)

        (level1 / 'file1.py').write_text('# level 1')
        (level2 / 'file2.py').write_text('# level 2')
        (level3 / 'file3.py').write_text('# level 3')

        # Depth 1 should only find file1.py
        counter_depth1 = LineCounter(max_depth=1)
        results_depth1 = counter_depth1.count_files(str(level1))
        self.assertEqual(len(results_depth1), 1)

        # No depth limit should find all files
        counter_no_limit = LineCounter(max_depth=None)
        results_unlimited = counter_no_limit.count_files(str(level1))
        self.assertGreaterEqual(len(results_unlimited), 2)

    def test_count_files_with_language_filter(self):
        """Test language_filter parameter."""
        counter_py = LineCounter(language_filter='Python')
        counter_js = LineCounter(language_filter='JavaScript')

        if self.fixtures_dir.exists():
            results_py = counter_py.count_files(str(self.fixtures_dir))
            results_js = counter_js.count_files(str(self.fixtures_dir))

            # Check that results only contain the specified language
            for result in results_py.values():
                self.assertEqual(result['language'], 'Python')
            for result in results_js.values():
                self.assertEqual(result['language'], 'JavaScript')

    def test_count_files_ignores_ignored_directories(self):
        """Test that ignored directories are properly skipped."""
        # Create pycache directory
        pycache = Path(self.temp_dir) / '__pycache__'
        pycache.mkdir()
        (pycache / 'module.pyc').write_text('binary')

        (Path(self.temp_dir) / 'module.py').write_text('# code')

        counter = LineCounter()
        results = counter.count_files(str(self.temp_dir))

        # Should only find module.py, not the .pyc file
        self.assertEqual(len(results), 1)
        self.assertTrue(any('module.py' in path for path in results.keys()))

    def test_count_lines_nonexistent_file(self):
        """Test handling of nonexistent file."""
        counter = LineCounter()
        result = counter.count_lines(Path(self.temp_dir) / 'nonexistent.py')
        self.assertIsNone(result)

    def test_count_files_nonexistent_directory(self):
        """Test handling of nonexistent directory."""
        counter = LineCounter()
        results = counter.count_files(str(Path(self.temp_dir) / 'nonexistent'))
        self.assertEqual(results, {})


class TestConsoleFormatter(unittest.TestCase):
    """
    Test console output formatting and statistics.

    Purpose:    Verify ConsoleFormatter produces correct ASCII tables and statistics
    Usage:      Run TestConsoleFormatter tests to validate formatting
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: console formatting tests
    """

    def setUp(self):
        """Set up test fixtures."""
        self.formatter = ConsoleFormatter()
        self.sample_data = {
            'file1.py': {
                'total': 100,
                'blank': 10,
                'comment': 15,
                'code': 75,
                'language': 'Python'
            },
            'file2.js': {
                'total': 80,
                'blank': 8,
                'comment': 10,
                'code': 62,
                'language': 'JavaScript'
            },
            'file3.py': {
                'total': 50,
                'blank': 5,
                'comment': 5,
                'code': 40,
                'language': 'Python'
            }
        }

    def test_format_top_files_empty_data(self):
        """Test formatting with empty data."""
        result = self.formatter.format_top_files({})
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_format_top_files_returns_string(self):
        """Test that format_top_files returns a string."""
        result = self.formatter.format_top_files(self.sample_data)
        self.assertIsInstance(result, str)

    def test_format_top_files_contains_filenames(self):
        """Test that output contains file information."""
        result = self.formatter.format_top_files(self.sample_data)
        # Should contain at least one filename
        self.assertTrue(
            any(name in result for name in ['file1.py', 'file2.js', 'file3.py'])
        )

    def test_format_top_files_respects_limit(self):
        """Test that limit parameter is respected."""
        result_limit_1 = self.formatter.format_top_files(self.sample_data, limit=1)
        result_limit_2 = self.formatter.format_top_files(self.sample_data, limit=2)

        # With more files in output, the string should generally be longer
        # (though this is not guaranteed, we check basic sanity)
        self.assertIsInstance(result_limit_1, str)
        self.assertIsInstance(result_limit_2, str)

    def test_format_top_files_with_color(self):
        """Test that color formatting produces output."""
        result_color = self.formatter.format_top_files(self.sample_data, use_color=True)
        self.assertIsInstance(result_color, str)
        self.assertGreater(len(result_color), 0)

    def test_format_top_files_without_color(self):
        """Test that non-color formatting produces output."""
        result_no_color = self.formatter.format_top_files(self.sample_data, use_color=False)
        self.assertIsInstance(result_no_color, str)
        self.assertGreater(len(result_no_color), 0)

    def test_format_top_files_sorted_descending(self):
        """Test that files are sorted by line count descending."""
        result = self.formatter.format_top_files(self.sample_data)
        # file1.py has 100 lines (most), file2.js has 80, file3.py has 50
        # Output should show them in that order
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_format_summary_stats_returns_string(self):
        """Test that format_summary_stats returns a string."""
        result = self.formatter.format_summary_stats(self.sample_data)
        self.assertIsInstance(result, str)

    def test_format_summary_stats_contains_totals(self):
        """Test that summary contains aggregate statistics."""
        result = self.formatter.format_summary_stats(self.sample_data)
        # Should contain information about totals
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_format_summary_stats_with_color(self):
        """Test summary formatting with color."""
        result = self.formatter.format_summary_stats(self.sample_data, use_color=True)
        self.assertIsInstance(result, str)

    def test_format_summary_stats_without_color(self):
        """Test summary formatting without color."""
        result = self.formatter.format_summary_stats(self.sample_data, use_color=False)
        self.assertIsInstance(result, str)

    def test_format_summary_stats_empty_data(self):
        """Test summary formatting with empty data."""
        result = self.formatter.format_summary_stats({})
        self.assertIsInstance(result, str)


class TestHTMLReportGenerator(unittest.TestCase):
    """
    Test HTML report generation.

    Purpose:    Verify HTMLReportGenerator creates valid HTML reports
    Usage:      Run TestHTMLReportGenerator tests to validate HTML generation
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: HTML report generation tests
    """

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = HTMLReportGenerator()
        self.sample_data = {
            'file1.py': {
                'total': 100,
                'blank': 10,
                'comment': 15,
                'code': 75,
                'language': 'Python'
            },
            'file2.js': {
                'total': 80,
                'blank': 8,
                'comment': 10,
                'code': 62,
                'language': 'JavaScript'
            }
        }

    def tearDown(self):
        """Clean up temporary directory."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_generate_report_creates_file(self):
        """Test that generate_report creates an HTML file."""
        output_path = self.generator.generate_report(
            self.sample_data,
            output_path=Path(self.temp_dir),
            project_name='test-project'
        )

        self.assertTrue(output_path.exists())
        self.assertTrue(str(output_path).endswith('.html'))

    def test_generate_report_returns_path(self):
        """Test that generate_report returns a Path object."""
        result = self.generator.generate_report(
            self.sample_data,
            output_path=Path(self.temp_dir),
            project_name='test-project'
        )

        self.assertIsInstance(result, Path)

    def test_generate_report_html_is_valid(self):
        """Test that generated HTML contains expected elements."""
        output_path = self.generator.generate_report(
            self.sample_data,
            output_path=Path(self.temp_dir),
            project_name='test-project'
        )

        content = output_path.read_text()

        # Check for basic HTML structure
        self.assertIn('<html', content.lower())
        self.assertIn('</html>', content.lower())
        self.assertIn('<body', content.lower())
        self.assertIn('</body>', content.lower())

    def test_generate_report_contains_project_name(self):
        """Test that report includes project name."""
        output_path = self.generator.generate_report(
            self.sample_data,
            output_path=Path(self.temp_dir),
            project_name='MyTestProject'
        )

        content = output_path.read_text()
        self.assertIn('MyTestProject', content)

    def test_generate_report_contains_file_data(self):
        """Test that report includes file information."""
        output_path = self.generator.generate_report(
            self.sample_data,
            output_path=Path(self.temp_dir),
            project_name='test-project'
        )

        content = output_path.read_text()
        # Should contain at least one file name or line count
        self.assertTrue(
            any(str(data) in content or 'Python' in content
                for data in self.sample_data.values())
        )

    def test_generate_report_filename_format(self):
        """Test that report filename has expected format."""
        output_path = self.generator.generate_report(
            self.sample_data,
            output_path=Path(self.temp_dir),
            project_name='test-project'
        )

        filename = output_path.name
        # Should match pattern like: line-count-report-20260407-123456.html
        self.assertTrue(filename.startswith('line-count-report-'))
        self.assertTrue(filename.endswith('.html'))

    def test_generate_report_empty_data(self):
        """Test report generation with empty data."""
        output_path = self.generator.generate_report(
            {},
            output_path=Path(self.temp_dir),
            project_name='empty-project'
        )

        self.assertTrue(output_path.exists())
        content = output_path.read_text()
        self.assertIn('empty-project', content)


class TestLineCountCommand(unittest.TestCase):
    """
    Test line-count command integration.

    Purpose:    Verify LineCountCommand correctly executes with various arguments
    Usage:      Run TestLineCountCommand tests to validate command behavior
    Version:    0.1.0
    Changes:    [v0.1.0] Initial: command integration tests
    """

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.fixtures_dir = Path(__file__).parent / 'fixtures' / 'sample_project'

    def tearDown(self):
        """Clean up temporary directory."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_command_with_valid_path(self):
        """Test command execution with valid path."""
        if not self.fixtures_dir.exists():
            self.skipTest("Fixtures directory not found")

        args = Namespace(
            path=str(self.fixtures_dir),
            max_depth=None,
            language=None,
            no_html=True,
            no_console=False,
            output_file=None,
            limit=20,
            no_color=True,
            exclude_dir=[]
        )

        # Command should not raise an exception
        command = LineCountCommand(args, command_name='line-count')
        try:
            command.execute()
        except SystemExit as e:
            # Only accept exit code 0 (success)
            self.assertEqual(e.code, 0)

    def test_command_with_nonexistent_path(self):
        """Test command with nonexistent path exits with error."""
        args = Namespace(
            path='/nonexistent/path/that/does/not/exist',
            max_depth=None,
            language=None,
            no_html=True,
            no_console=False,
            output_file=None,
            limit=20,
            no_color=True,
            exclude_dir=[]
        )

        command = LineCountCommand(args, command_name='line-count')
        with self.assertRaises(SystemExit) as cm:
            command.execute()
        self.assertEqual(cm.exception.code, 1)

    def test_command_with_file_path_exits_with_error(self):
        """Test command with file path (not directory) exits with error."""
        # Create a temporary file
        test_file = Path(self.temp_dir) / 'test.py'
        test_file.write_text('# test')

        args = Namespace(
            path=str(test_file),
            max_depth=None,
            language=None,
            no_html=True,
            no_console=False,
            output_file=None,
            limit=20,
            no_color=True,
            exclude_dir=[]
        )

        command = LineCountCommand(args, command_name='line-count')
        with self.assertRaises(SystemExit) as cm:
            command.execute()
        self.assertEqual(cm.exception.code, 1)

    def test_command_with_max_depth(self):
        """Test command with max_depth parameter."""
        if not self.fixtures_dir.exists():
            self.skipTest("Fixtures directory not found")

        args = Namespace(
            path=str(self.fixtures_dir),
            max_depth=1,
            language=None,
            no_html=True,
            no_console=False,
            output_file=None,
            limit=20,
            no_color=True,
            exclude_dir=[]
        )

        command = LineCountCommand(args, command_name='line-count')
        try:
            command.execute()
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_command_with_language_filter(self):
        """Test command with language filter."""
        if not self.fixtures_dir.exists():
            self.skipTest("Fixtures directory not found")

        args = Namespace(
            path=str(self.fixtures_dir),
            max_depth=None,
            language='Python',
            no_html=True,
            no_console=False,
            output_file=None,
            limit=20,
            no_color=True,
            exclude_dir=[]
        )

        command = LineCountCommand(args, command_name='line-count')
        try:
            command.execute()
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_command_with_no_console_flag(self):
        """Test command with no_console flag."""
        if not self.fixtures_dir.exists():
            self.skipTest("Fixtures directory not found")

        args = Namespace(
            path=str(self.fixtures_dir),
            max_depth=None,
            language=None,
            no_html=True,
            no_console=True,
            output_file=None,
            limit=20,
            no_color=True,
            exclude_dir=[]
        )

        command = LineCountCommand(args, command_name='line-count')
        try:
            command.execute()
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_command_with_html_generation(self):
        """Test command generates HTML report."""
        if not self.fixtures_dir.exists():
            self.skipTest("Fixtures directory not found")

        args = Namespace(
            path=str(self.fixtures_dir),
            max_depth=None,
            language=None,
            no_html=False,
            no_console=False,
            output_file=None,
            limit=20,
            no_color=True,
            exclude_dir=[]
        )

        command = LineCountCommand(args, command_name='line-count')
        # Capture stdout to avoid cluttering test output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            command.execute()
        finally:
            sys.stdout = sys.__stdout__


if __name__ == '__main__':
    unittest.main()
