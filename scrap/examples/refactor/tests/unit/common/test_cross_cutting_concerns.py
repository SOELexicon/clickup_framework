"""
Unit tests for cross-cutting concerns.

Tests the middleware pipeline components, including validation, logging,
error handling, and recovery mechanisms.
"""
import unittest
import logging
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from argparse import Namespace, ArgumentParser

from refactor.cli.middleware import (
    PipelineConfig,
    ValidationError,
    ValidationMiddleware,
    LoggingMiddleware,
    ErrorHandlingMiddleware,
    RecoveryMiddleware,
    EnhancedMiddlewarePipeline
)
from refactor.cli.command import CommandContext, Command


class TestCommand(Command):
    """Test command for testing middleware."""
    
    def __init__(self, name="test", allow_retry=True, should_fail=False):
        """Initialize test command."""
        self._name = name
        self.allow_retry = allow_retry
        self.should_fail = should_fail
        self.execution_count = 0
    
    @property
    def name(self) -> str:
        """Get the name of the command."""
        return self._name
    
    @property
    def description(self) -> str:
        """Get the description of the command."""
        return "Test command for middleware tests"
    
    def configure_parser(self, parser: ArgumentParser) -> None:
        """Configure the argument parser for this command."""
        parser.add_argument("--test-arg", help="Test argument")
    
    def execute(self, args):
        """Execute the test command."""
        self.execution_count += 1
        if self.should_fail:
            raise ValueError("Command failed")
        return 0


class MockCommandContext(CommandContext):
    """Command context with metadata support for testing middleware."""
    
    def __init__(self, command=None, args=None):
        """Initialize the command context with metadata for tests."""
        super().__init__(command, args)
        # Middleware implementation uses metadata instead of values
        self.metadata = self.values


class TestValidationMiddleware(unittest.TestCase):
    """Tests for the ValidationMiddleware."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = PipelineConfig(enable_validation=True)
        self.middleware = ValidationMiddleware(self.config)
        self.command = TestCommand()
        self.args = Namespace(arg1="value1", arg2="value2")
        self.context = MockCommandContext(self.command, self.args)

    def test_valid_command(self):
        """Test validation of a valid command."""
        def valid_validator(context):
            return []
        
        self.middleware.add_validator("test", valid_validator)
        self.middleware.before_execution(self.context)
        
        self.assertFalse(self.context.aborted)
        self.assertIsNone(self.context.error)
    
    def test_invalid_command(self):
        """Test validation of an invalid command."""
        def invalid_validator(context):
            return [
                ValidationError(
                    field="arg1",
                    message="Invalid value",
                    code="INVALID_VALUE"
                )
            ]
        
        self.middleware.add_validator("test", invalid_validator)
        self.middleware.before_execution(self.context)
        
        self.assertTrue(self.context.aborted)
        self.assertIsNotNone(self.context.error)
        self.assertIn('validation_errors', self.context.metadata)
        self.assertEqual(len(self.context.metadata['validation_errors']), 1)
        self.assertEqual(self.context.metadata['validation_errors'][0].field, "arg1")
    
    def test_exception_in_validator(self):
        """Test handling of exceptions in validators."""
        def exception_validator(context):
            raise RuntimeError("Validator failed")
        
        self.middleware.add_validator("test", exception_validator)
        self.middleware.before_execution(self.context)
        
        self.assertTrue(self.context.aborted)
        self.assertIsNotNone(self.context.error)
        self.assertIn('validation_errors', self.context.metadata)
        self.assertEqual(self.context.metadata['validation_errors'][0].code, "VALIDATOR_ERROR")
    
    def test_validation_disabled(self):
        """Test that validation can be disabled."""
        self.config.enable_validation = False
        
        def invalid_validator(context):
            return [
                ValidationError(
                    field="arg1",
                    message="Invalid value",
                    code="INVALID_VALUE"
                )
            ]
        
        self.middleware.add_validator("test", invalid_validator)
        self.middleware.before_execution(self.context)
        
        self.assertFalse(self.context.aborted)
        self.assertIsNone(self.context.error)
    
    def test_after_execution_noop(self):
        """Test that after_execution is a no-op."""
        # Should not raise any exceptions
        self.middleware.after_execution(self.context)
        
        self.assertFalse(self.context.aborted)
        self.assertIsNone(self.context.error)


class TestLoggingMiddleware(unittest.TestCase):
    """Tests for the LoggingMiddleware."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = PipelineConfig(enable_logging=True)
        self.middleware = LoggingMiddleware(self.config)
        self.command = TestCommand()
        self.args = Namespace(arg1="value1", arg2="value2")
        self.context = MockCommandContext(self.command, self.args)
    
    @patch('refactor.cli.middleware.logging.Logger.info')
    def test_before_execution_logging(self, mock_info):
        """Test logging before command execution."""
        self.middleware.before_execution(self.context)
        
        self.assertIn('start_time', self.context.metadata)
        mock_info.assert_called_once()
        message = mock_info.call_args[0][0]
        self.assertIn("Executing command 'test'", message)
    
    @patch('refactor.cli.middleware.logging.Logger.info')
    def test_after_execution_success_logging(self, mock_info):
        """Test logging after successful command execution."""
        self.context.metadata['start_time'] = time.time() - 1  # 1 second ago
        self.context.result = 0
        
        self.middleware.after_execution(self.context)
        
        mock_info.assert_called_once()
        message = mock_info.call_args[0][0]
        self.assertIn("completed in", message)
        self.assertIn("with result: 0", message)
    
    @patch('refactor.cli.middleware.logging.Logger.error')
    def test_after_execution_error_logging(self, mock_error):
        """Test logging after failed command execution."""
        self.context.metadata['start_time'] = time.time() - 1  # 1 second ago
        self.context.error = ValueError("Command failed")
        
        self.middleware.after_execution(self.context)
        
        mock_error.assert_called_once()
        message = mock_error.call_args[0][0]
        self.assertIn("Command 'test' failed", message)
        self.assertIn("Command failed", message)
    
    def test_logging_disabled(self):
        """Test that logging can be disabled."""
        self.config.enable_logging = False
        
        with patch('refactor.cli.middleware.logging.Logger.info') as mock_info:
            self.middleware.before_execution(self.context)
            self.middleware.after_execution(self.context)
            
            mock_info.assert_not_called()


class TestErrorHandlingMiddleware(unittest.TestCase):
    """Tests for the ErrorHandlingMiddleware."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = PipelineConfig(enable_error_handling=True)
        self.middleware = ErrorHandlingMiddleware(self.config)
        self.command = TestCommand()
        self.args = Namespace(arg1="value1", arg2="value2")
        self.context = MockCommandContext(self.command, self.args)
    
    def test_error_handling(self):
        """Test error handling and metadata collection."""
        self.context.error = ValueError("Command failed")
        
        self.middleware.after_execution(self.context)
        
        self.assertIn('error_info', self.context.metadata)
        error_info = self.context.metadata['error_info']
        self.assertEqual(error_info['command'], "test")
        self.assertEqual(error_info['error_type'], "ValueError")
        self.assertEqual(error_info['message'], "Command failed")
    
    def test_validation_error_handling(self):
        """Test handling of validation errors."""
        self.context.error = ValueError("Command failed")
        self.context.metadata['validation_errors'] = [
            ValidationError(
                field="arg1",
                message="Invalid value",
                code="INVALID_VALUE"
            )
        ]
        
        self.middleware.after_execution(self.context)
        
        self.assertIn('error_info', self.context.metadata)
        error_info = self.context.metadata['error_info']
        self.assertIn('validation_errors', error_info)
        self.assertEqual(len(error_info['validation_errors']), 1)
        self.assertEqual(error_info['validation_errors'][0]['field'], "arg1")
    
    def test_error_handling_disabled(self):
        """Test that error handling can be disabled."""
        self.config.enable_error_handling = False
        self.context.error = ValueError("Command failed")
        
        self.middleware.after_execution(self.context)
        
        self.assertNotIn('error_info', self.context.metadata)
    
    def test_before_execution_noop(self):
        """Test that before_execution is a no-op."""
        # Should not raise any exceptions
        self.middleware.before_execution(self.context)
        
        self.assertFalse(self.context.aborted)
        self.assertIsNone(self.context.error)


class TestRecoveryMiddleware(unittest.TestCase):
    """Tests for the RecoveryMiddleware."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = PipelineConfig(
            enable_recovery=True,
            max_retries=3,
            retry_delay=0.01  # Small delay for testing
        )
        self.middleware = RecoveryMiddleware(self.config)
        self.command = TestCommand(allow_retry=True)
        self.args = Namespace(arg1="value1", arg2="value2")
        self.context = MockCommandContext(self.command, self.args)
    
    def test_retry_successful(self):
        """Test successful retry after failure."""
        # Make the command fail on first execution then succeed
        self.command.should_fail = True
        self.context.error = ValueError("Command failed")
        
        with patch.object(self.command, 'execute', wraps=self.command.execute) as mock_execute:
            # On first retry, make the command succeed
            mock_execute.side_effect = [0]  # Success on retry
            
            self.middleware.after_execution(self.context)
            
            # Command should have been executed once more
            self.assertEqual(mock_execute.call_count, 1)
            self.assertEqual(self.context.metadata['retry_count'], 1)
            self.assertIsNone(self.context.error)
    
    def test_retry_exhausted(self):
        """Test exhausting all retry attempts."""
        # Make the command always fail
        self.command.should_fail = True
        self.context.error = ValueError("Command failed")
        
        with patch.object(self.command, 'execute', wraps=self.command.execute) as mock_execute:
            # Always raise the same error
            mock_execute.side_effect = ValueError("Command failed")
            
            self.middleware.after_execution(self.context)
            
            # Command should have been executed max_retries times
            self.assertEqual(mock_execute.call_count, self.config.max_retries)
            self.assertEqual(self.context.metadata['retry_count'], self.config.max_retries)
            self.assertIsNotNone(self.context.error)
    
    def test_retry_not_allowed(self):
        """Test command that doesn't allow retries."""
        # Create a command that doesn't allow retries
        self.command = TestCommand(allow_retry=False)
        self.context = MockCommandContext(self.command, self.args)
        self.context.error = ValueError("Command failed")
        
        with patch.object(self.command, 'execute') as mock_execute:
            self.middleware.after_execution(self.context)
            
            # Command should not have been retried
            mock_execute.assert_not_called()
    
    def test_recovery_disabled(self):
        """Test that recovery can be disabled."""
        self.config.enable_recovery = False
        self.context.error = ValueError("Command failed")
        
        with patch.object(self.command, 'execute') as mock_execute:
            self.middleware.after_execution(self.context)
            
            # Command should not have been retried
            mock_execute.assert_not_called()


class TestEnhancedMiddlewarePipeline(unittest.TestCase):
    """Tests for the EnhancedMiddlewarePipeline."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = PipelineConfig()
        self.pipeline = EnhancedMiddlewarePipeline(self.config)
    
    def test_middleware_registration(self):
        """Test that standard middleware is registered."""
        # By default, all middleware should be registered
        self.assertEqual(len(self.pipeline.middleware_list), 4)
        
        # Check types of registered middleware
        self.assertIsInstance(self.pipeline.middleware_list[0], ValidationMiddleware)
        self.assertIsInstance(self.pipeline.middleware_list[1], LoggingMiddleware)
        self.assertIsInstance(self.pipeline.middleware_list[2], ErrorHandlingMiddleware)
        self.assertIsInstance(self.pipeline.middleware_list[3], RecoveryMiddleware)
    
    def test_execute_success(self):
        """Test successful command execution."""
        command = TestCommand()
        args = Namespace(arg1="value1", arg2="value2")
        context = MockCommandContext(command, args)
        
        # Mock all middleware to avoid side effects
        for middleware in self.pipeline.middleware_list:
            middleware.before_execution = MagicMock()
            middleware.after_execution = MagicMock()
        
        result = self.pipeline.execute(context)
        
        # Command should execute and return 0
        self.assertEqual(result, 0)
        
        # All middleware before_execution should be called
        for middleware in self.pipeline.middleware_list:
            middleware.before_execution.assert_called_once_with(context)
        
        # All middleware after_execution should be called in reverse order
        for middleware in self.pipeline.middleware_list:
            middleware.after_execution.assert_called_once_with(context)
    
    def test_execute_command_failure(self):
        """Test pipeline handling of command failures."""
        command = TestCommand(should_fail=True)
        args = Namespace(arg1="value1", arg2="value2")
        context = MockCommandContext(command, args)
        
        # Mock all middleware to avoid side effects
        for middleware in self.pipeline.middleware_list:
            middleware.before_execution = MagicMock()
            middleware.after_execution = MagicMock()
        
        result = self.pipeline.execute(context)
        
        # Command failed, so result should be 1
        self.assertEqual(result, 1)
        self.assertIsNotNone(context.error)
        
        # All middleware before_execution should be called
        for middleware in self.pipeline.middleware_list:
            middleware.before_execution.assert_called_once_with(context)
        
        # All middleware after_execution should be called in reverse order
        for middleware in self.pipeline.middleware_list:
            middleware.after_execution.assert_called_once_with(context)
    
    def test_execute_middleware_aborts(self):
        """Test pipeline handling when middleware aborts execution."""
        command = TestCommand()
        args = Namespace(arg1="value1", arg2="value2")
        context = MockCommandContext(command, args)
        
        # Mock the first middleware to abort
        self.pipeline.middleware_list[0].before_execution = MagicMock(
            side_effect=lambda ctx: ctx.abort(ValueError("Middleware aborted"))
        )
        
        # Mock remaining middleware
        for middleware in self.pipeline.middleware_list[1:]:
            middleware.before_execution = MagicMock()
        
        for middleware in self.pipeline.middleware_list:
            middleware.after_execution = MagicMock()
        
        result = self.pipeline.execute(context)
        
        # Command should not execute and result should be 1
        self.assertEqual(result, 1)
        self.assertIsNotNone(context.error)
        
        # Only the first middleware should have before_execution called
        self.pipeline.middleware_list[0].before_execution.assert_called_once_with(context)
        for middleware in self.pipeline.middleware_list[1:]:
            middleware.before_execution.assert_not_called()
        
        # All middleware after_execution should be called in reverse order
        for middleware in self.pipeline.middleware_list:
            middleware.after_execution.assert_called_once_with(context)


if __name__ == '__main__':
    unittest.main() 