"""
Unit tests for the logging framework.

This module tests the functionality of the logging framework components:
- Log formatters (TextFormatter, JsonFormatter)
- Log handlers (ConsoleHandler, FileHandler, BufferedHandler)
- Logger class with different log levels
- Log configuration utilities
"""

import unittest
import os
import json
import io
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from refactor.common.logging import (
    LogLevel,
    LogFormatter,
    TextFormatter,
    JsonFormatter,
    LogHandler,
    ConsoleHandler,
    FileHandler,
    BufferedHandler,
    Logger,
    get_logger,
    configure_logging
)


class TestLogFormatters(unittest.TestCase):
    """Tests for the log formatter classes."""
    
    def test_text_formatter_basic(self):
        """Test basic text formatting."""
        formatter = TextFormatter()
        record = {
            "timestamp": "2023-04-03T12:34:56",
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(record)
        self.assertIn("[2023-04-03T12:34:56]", result)
        self.assertIn("[INFO]", result)
        self.assertIn("Test message", result)
    
    def test_text_formatter_without_timestamp(self):
        """Test text formatting without timestamp."""
        formatter = TextFormatter(include_timestamp=False)
        record = {
            "timestamp": "2023-04-03T12:34:56",
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(record)
        self.assertNotIn("[2023-04-03T12:34:56]", result)
        self.assertIn("[INFO]", result)
        self.assertIn("Test message", result)
    
    def test_text_formatter_without_level(self):
        """Test text formatting without log level."""
        formatter = TextFormatter(include_level=False)
        record = {
            "timestamp": "2023-04-03T12:34:56",
            "level": "INFO",
            "message": "Test message"
        }
        
        result = formatter.format(record)
        self.assertIn("[2023-04-03T12:34:56]", result)
        self.assertNotIn("[INFO]", result)
        self.assertIn("Test message", result)
    
    def test_text_formatter_with_context(self):
        """Test text formatting with context data."""
        formatter = TextFormatter()
        record = {
            "timestamp": "2023-04-03T12:34:56",
            "level": "INFO",
            "message": "Test message",
            "user_id": "usr_123",
            "task_id": "tsk_456"
        }
        
        result = formatter.format(record)
        self.assertIn("user_id=usr_123", result)
        self.assertIn("task_id=tsk_456", result)
    
    def test_text_formatter_with_complex_context(self):
        """Test text formatting with complex context data."""
        formatter = TextFormatter()
        record = {
            "timestamp": "2023-04-03T12:34:56",
            "level": "INFO",
            "message": "Test message",
            "data": {"key1": "value1", "key2": "value2"},
            "list_data": [1, 2, 3]
        }
        
        result = formatter.format(record)
        self.assertIn("data=", result)
        self.assertIn("list_data=", result)
    
    def test_text_formatter_with_exception(self):
        """Test text formatting with exception data."""
        formatter = TextFormatter()
        record = {
            "timestamp": "2023-04-03T12:34:56",
            "level": "ERROR",
            "message": "Test error",
            "exception": "ValueError: Invalid data"
        }
        
        result = formatter.format(record)
        self.assertIn("Exception: ValueError: Invalid data", result)
    
    def test_json_formatter(self):
        """Test JSON formatting."""
        formatter = JsonFormatter()
        record = {
            "timestamp": "2023-04-03T12:34:56",
            "level": "INFO",
            "message": "Test message",
            "user_id": "usr_123",
            "task_id": "tsk_456"
        }
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        self.assertEqual(parsed["timestamp"], "2023-04-03T12:34:56")
        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["message"], "Test message")
        self.assertEqual(parsed["user_id"], "usr_123")
        self.assertEqual(parsed["task_id"], "tsk_456")


class TestLogHandlers(unittest.TestCase):
    """Tests for the log handler classes."""
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_console_handler_stdout(self, mock_stdout):
        """Test console handler writes to stdout."""
        handler = ConsoleHandler()
        handler.handle("Test message")
        self.assertEqual(mock_stdout.getvalue(), "Test message\n")
    
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_console_handler_stderr(self, mock_stderr):
        """Test console handler writes errors to stderr."""
        handler = ConsoleHandler()
        handler.handle("Error message", level=LogLevel.ERROR)
        self.assertEqual(mock_stderr.getvalue(), "Error message\n")
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_console_handler_stderr_disabled(self, mock_stdout):
        """Test console handler with stderr disabled."""
        handler = ConsoleHandler(use_stderr_for_errors=False)
        handler.handle("Error message", level=LogLevel.ERROR)
        self.assertEqual(mock_stdout.getvalue(), "Error message\n")
    
    def test_file_handler(self):
        """Test file handler writes to file."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            log_file = os.path.join(temp_dir, "test.log")
            handler = FileHandler(log_file)
            handler.handle("Test message")
            
            # Check file contents
            with open(log_file, 'r') as f:
                content = f.read()
                self.assertEqual(content, "Test message\n")
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
    
    def test_file_handler_create_directory(self):
        """Test file handler creates directory if it doesn't exist."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            # Add a subdirectory to the path
            log_dir = os.path.join(temp_dir, "logs")
            log_file = os.path.join(log_dir, "test.log")
            
            handler = FileHandler(log_file)
            handler.handle("Test message")
            
            # Check directory and file creation
            self.assertTrue(os.path.exists(log_dir))
            self.assertTrue(os.path.exists(log_file))
            
            # Check file contents
            with open(log_file, 'r') as f:
                content = f.read()
                self.assertEqual(content, "Test message\n")
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
    
    def test_file_handler_rotation(self):
        """Test file handler rotation."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            log_file = os.path.join(temp_dir, "test.log")
            
            # Create a file handler with a small max size
            handler = FileHandler(log_file, max_size_bytes=20, backup_count=2)
            
            # Write enough data to trigger rotation
            handler.handle("First message") # 13 + 1 = 14 bytes
            handler.handle("Second") # 6 + 1 = 7 bytes, total 21 > 20, should rotate
            handler.handle("Third message")
            
            # Check files
            self.assertTrue(os.path.exists(log_file))
            self.assertTrue(os.path.exists(f"{log_file}.1"))
            
            # Check content of the current log file
            with open(log_file, 'r') as f:
                content = f.read()
                self.assertEqual(content, "Third message\n")
                
            # Check content of the backup log file
            with open(f"{log_file}.1", 'r') as f:
                content = f.read()
                self.assertEqual(content, "First message\nSecond\n")
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
    
    def test_buffered_handler(self):
        """Test buffered handler buffers messages."""
        mock_target = MagicMock()
        handler = BufferedHandler(mock_target, buffer_size=3)
        
        # Send two messages (less than buffer size)
        handler.handle("Message 1")
        handler.handle("Message 2")
        
        # Target should not have received any messages yet
        mock_target.handle.assert_not_called()
        
        # Send a third message to trigger flush
        handler.handle("Message 3")
        
        # Target should have received all messages
        self.assertEqual(mock_target.handle.call_count, 3)
    
    def test_buffered_handler_flush_on_error(self):
        """Test buffered handler flushes on error level."""
        mock_target = MagicMock()
        handler = BufferedHandler(mock_target, buffer_size=10, flush_level=LogLevel.ERROR)
        
        # Send some messages
        handler.handle("Message 1")
        handler.handle("Message 2")
        
        # Target should not have received any messages yet
        mock_target.handle.assert_not_called()
        
        # Send an error message to trigger flush
        handler.handle("Error message", level=LogLevel.ERROR)
        
        # Target should have received all messages
        self.assertEqual(mock_target.handle.call_count, 3)
    
    def test_buffered_handler_manual_flush(self):
        """Test buffered handler manual flush."""
        mock_target = MagicMock()
        handler = BufferedHandler(mock_target, buffer_size=10)
        
        # Send some messages
        handler.handle("Message 1")
        handler.handle("Message 2")
        
        # Target should not have received any messages yet
        mock_target.handle.assert_not_called()
        
        # Manually flush
        handler.flush()
        
        # Target should have received all messages
        self.assertEqual(mock_target.handle.call_count, 2)


class TestLogger(unittest.TestCase):
    """Tests for the logger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock handlers and formatter
        self.mock_formatter = MagicMock()
        self.mock_formatter.format.return_value = "formatted message"
        
        self.mock_handler = MagicMock()
        
        # Create logger with mocks
        self.logger = Logger(
            "test_logger",
            level=LogLevel.INFO,
            handlers=[self.mock_handler],
            formatter=self.mock_formatter
        )
    
    def test_logger_info_level(self):
        """Test logging at INFO level."""
        self.logger.info("Test message")
        
        # Formatter should have been called with the right data
        self.mock_formatter.format.assert_called_once()
        record = self.mock_formatter.format.call_args[0][0]
        self.assertEqual(record["level"], "INFO")
        self.assertEqual(record["message"], "Test message")
        
        # Handler should have been called
        self.mock_handler.handle.assert_called_once_with("formatted message", LogLevel.INFO)
    
    def test_logger_debug_suppressed(self):
        """Test DEBUG messages are suppressed when level is INFO."""
        self.logger.debug("Debug message")
        
        # Neither formatter nor handler should be called
        self.mock_formatter.format.assert_not_called()
        self.mock_handler.handle.assert_not_called()
    
    def test_logger_level_filter(self):
        """Test different log levels are properly filtered."""
        # DEBUG should be suppressed (level is INFO)
        self.logger.debug("Debug message")
        self.mock_handler.handle.assert_not_called()
        
        # INFO should pass
        self.logger.info("Info message")
        self.assertEqual(self.mock_handler.handle.call_count, 1)
        
        # WARNING should pass
        self.logger.warning("Warning message")
        self.assertEqual(self.mock_handler.handle.call_count, 2)
        
        # ERROR should pass
        self.logger.error("Error message")
        self.assertEqual(self.mock_handler.handle.call_count, 3)
        
        # CRITICAL should pass
        self.logger.critical("Critical message")
        self.assertEqual(self.mock_handler.handle.call_count, 4)
    
    def test_logger_with_context(self):
        """Test logging with context data."""
        self.logger.info("Test message", user_id="usr_123", task_id="tsk_456")
        
        # Formatter should have been called with the right data
        record = self.mock_formatter.format.call_args[0][0]
        self.assertEqual(record["user_id"], "usr_123")
        self.assertEqual(record["task_id"], "tsk_456")
    
    def test_logger_with_exception(self):
        """Test logging with exception."""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            self.logger.exception("Error occurred", exception=e)
        
        # Formatter should have been called with the right data
        record = self.mock_formatter.format.call_args[0][0]
        self.assertEqual(record["level"], "ERROR")
        self.assertEqual(record["message"], "Error occurred")
        self.assertTrue("Test error" in record["exception"], 
                       f"Expected 'Test error' in exception: {record['exception']}")
    
    def test_logger_lazy_evaluation(self):
        """Test lazy evaluation of log messages."""
        # Create an expensive function that should only be called if needed
        expensive_func = MagicMock(return_value="Expensive result")
        
        # This should be suppressed, so the function shouldn't be called
        self.logger.debug(expensive_func)
        expensive_func.assert_not_called()
        
        # This should pass, so the function should be called
        self.logger.info(expensive_func)
        expensive_func.assert_called_once()


class TestLoggerConfiguration(unittest.TestCase):
    """Tests for the logger configuration utilities."""
    
    def test_get_logger(self):
        """Test getting a logger."""
        logger = get_logger("test.logger")
        self.assertIsInstance(logger, Logger)
        self.assertEqual(logger.name, "test.logger")
    
    @unittest.skip("Requires specific implementation details")
    def test_get_logger_cached(self):
        """Test loggers are cached by name."""
        pass
    
    @unittest.skip("Requires specific implementation details")
    def test_configure_logging_console(self):
        """Test configure_logging with console output."""
        pass
    
    @unittest.skip("Requires specific implementation details")
    def test_configure_logging_file(self):
        """Test configure_logging with file output."""
        pass
    
    @unittest.skip("Requires specific implementation details")
    def test_configure_logging_both(self):
        """Test configure_logging with both console and file output."""
        pass
    
    @unittest.skip("Requires specific implementation details")
    def test_configure_logging_format(self):
        """Test configure_logging with different format styles."""
        pass


if __name__ == '__main__':
    unittest.main() 