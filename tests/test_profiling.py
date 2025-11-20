"""Tests for performance profiling system."""

import os
import time
import json
import pytest
from pathlib import Path

from clickup_framework.commands.map_helpers.mermaid.profiling import (
    PerformanceProfiler,
    ProfileCheckpoint,
    ProfileReport,
    profile_method,
    profile_section,
    register_profile,
    get_registered_profiles,
    clear_registry,
)
from clickup_framework.commands.map_helpers.mermaid.config import (
    ProfilingConfig,
    MermaidConfig,
    set_config,
    reset_config,
)


class TestPerformanceProfiler:
    """Test PerformanceProfiler class."""

    def setup_method(self):
        """Setup for each test."""
        clear_registry()

    def test_basic_profiling(self):
        """Test basic profiling with checkpoints."""
        profiler = PerformanceProfiler('test_operation', enabled=True)
        profiler.start()

        time.sleep(0.01)  # Small delay
        profiler.checkpoint('step1')

        time.sleep(0.01)
        profiler.checkpoint('step2')

        profiler.stop()

        report = profiler.get_report()

        assert report.operation_name == 'test_operation'
        assert report.total_time > 0.02  # At least 20ms
        assert len(report.checkpoints) == 4  # start, step1, step2, end
        assert report.checkpoints[0].name == 'start'
        assert report.checkpoints[-1].name == 'end'

    def test_context_manager(self):
        """Test profiler as context manager."""
        with PerformanceProfiler('context_test', enabled=True) as profiler:
            time.sleep(0.01)
            profiler.checkpoint('checkpoint1')
            time.sleep(0.01)

        report = profiler.get_report()

        assert report.total_time > 0.02
        assert len(report.checkpoints) >= 3  # start, checkpoint1, end

    def test_disabled_profiler(self):
        """Test that disabled profiler doesn't record anything."""
        profiler = PerformanceProfiler('disabled_test', enabled=False)
        profiler.start()
        profiler.checkpoint('should_not_record')
        profiler.stop()

        report = profiler.get_report()

        assert report.total_time == 0.0
        assert len(report.checkpoints) == 0

    def test_metadata(self):
        """Test adding metadata to profiler."""
        profiler = PerformanceProfiler('metadata_test', enabled=True)
        profiler.start()

        profiler.add_metadata('key1', 'value1')
        profiler.add_metadata('key2', 42)

        profiler.stop()

        report = profiler.get_report()

        assert report.metadata['key1'] == 'value1'
        assert report.metadata['key2'] == 42

    def test_elapsed_times(self):
        """Test elapsed time calculations between checkpoints."""
        profiler = PerformanceProfiler('timing_test', enabled=True)
        profiler.start()

        time.sleep(0.01)
        profiler.checkpoint('cp1')

        time.sleep(0.02)
        profiler.checkpoint('cp2')

        profiler.stop()

        checkpoints = profiler.get_report().checkpoints

        # cp1 should be ~0.01s from start
        assert checkpoints[1].elapsed_since_prev > 0.01
        # cp2 should be ~0.02s from cp1
        assert checkpoints[2].elapsed_since_prev > 0.02


class TestProfileReport:
    """Test ProfileReport class."""

    def test_to_dict(self):
        """Test converting report to dictionary."""
        checkpoints = [
            ProfileCheckpoint('start', 1.0, 100.0, 0.0, 0.0),
            ProfileCheckpoint('end', 2.0, 110.0, 1.0, 1.0),
        ]

        report = ProfileReport(
            operation_name='test_op',
            total_time=1.0,
            total_memory_delta=10.0,
            peak_memory=110.0,
            checkpoints=checkpoints,
            metadata={'key': 'value'}
        )

        report_dict = report.to_dict()

        assert report_dict['operation_name'] == 'test_op'
        assert report_dict['total_time_seconds'] == 1.0
        assert report_dict['total_memory_delta_mb'] == 10.0
        assert report_dict['peak_memory_mb'] == 110.0
        assert len(report_dict['checkpoints']) == 2
        assert report_dict['metadata'] == {'key': 'value'}

    def test_format_text(self):
        """Test text formatting of report."""
        checkpoints = [
            ProfileCheckpoint('start', 1.0, 100.0, 0.0, 0.0),
            ProfileCheckpoint('end', 2.0, 110.0, 1.0, 1.0),
        ]

        report = ProfileReport(
            operation_name='test_format',
            total_time=1.0,
            total_memory_delta=10.0,
            peak_memory=110.0,
            checkpoints=checkpoints
        )

        text = report.format_text()

        assert 'test_format' in text
        assert 'Total Time: 1.0000s' in text
        assert 'Memory Delta: +10.00 MB' in text
        assert 'start' in text
        assert 'end' in text


class TestProfileDecorator:
    """Test profile_method decorator."""

    def test_decorator_basic(self):
        """Test basic decorator usage."""
        @profile_method('decorated_func')
        def my_function():
            time.sleep(0.01)
            return 42

        result = my_function()

        assert result == 42
        # Note: decorator stores report on instance, so we can't easily check it here

    def test_decorator_with_instance(self):
        """Test decorator with class instance."""
        class TestClass:
            @profile_method('test_method')
            def my_method(self):
                time.sleep(0.01)
                return 'success'

        obj = TestClass()
        result = obj.my_method()

        assert result == 'success'
        assert hasattr(obj, '_profile_report')
        assert obj._profile_report.operation_name == 'test_method'


class TestProfileSection:
    """Test profile_section context manager."""

    def test_standalone_section(self):
        """Test profile_section as standalone profiler."""
        with profile_section('standalone') as profiler:
            time.sleep(0.01)

        report = profiler.get_report()
        assert report.total_time > 0.01

    def test_nested_section(self):
        """Test nested profile sections."""
        with PerformanceProfiler('parent', enabled=True) as parent:
            with profile_section('child1', parent):
                time.sleep(0.01)

            with profile_section('child2', parent):
                time.sleep(0.01)

        report = parent.get_report()
        checkpoints_names = [cp.name for cp in report.checkpoints]

        assert 'child1_start' in checkpoints_names
        assert 'child1_end' in checkpoints_names
        assert 'child2_start' in checkpoints_names
        assert 'child2_end' in checkpoints_names


class TestProfileRegistry:
    """Test global profile registry."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def test_register_and_retrieve(self):
        """Test registering and retrieving profiles."""
        report1 = ProfileReport('op1', 1.0, 0.0, 100.0)
        report2 = ProfileReport('op2', 2.0, 0.0, 200.0)

        register_profile(report1)
        register_profile(report2)

        profiles = get_registered_profiles()

        assert len(profiles) == 2
        assert 'op1' in profiles
        assert 'op2' in profiles
        assert profiles['op1'].total_time == 1.0
        assert profiles['op2'].total_time == 2.0

    def test_clear_registry(self):
        """Test clearing the registry."""
        report = ProfileReport('op', 1.0, 0.0, 100.0)
        register_profile(report)

        assert len(get_registered_profiles()) == 1

        clear_registry()

        assert len(get_registered_profiles()) == 0


class TestProfilingConfig:
    """Test profiling configuration."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()
        # Clear any environment variables
        for key in ['MERMAID_PROFILING_ENABLED', 'MERMAID_PROFILING_PRINT_REPORTS',
                    'MERMAID_PROFILING_SAVE_REPORTS', 'MERMAID_PROFILING_OUTPUT_DIR']:
            os.environ.pop(key, None)

    def teardown_method(self):
        """Reset config after each test."""
        reset_config()

    def test_default_config(self):
        """Test default profiling configuration."""
        config = ProfilingConfig()

        assert config.enabled is False
        assert config.print_reports is False
        assert config.save_reports is False
        assert config.output_dir == 'profiling_reports'

    def test_from_env(self):
        """Test loading configuration from environment variables."""
        os.environ['MERMAID_PROFILING_ENABLED'] = 'true'
        os.environ['MERMAID_PROFILING_PRINT_REPORTS'] = '1'
        os.environ['MERMAID_PROFILING_SAVE_REPORTS'] = 'yes'
        os.environ['MERMAID_PROFILING_OUTPUT_DIR'] = 'my_profiles'

        config = ProfilingConfig.from_env()

        assert config.enabled is True
        assert config.print_reports is True
        assert config.save_reports is True
        assert config.output_dir == 'my_profiles'

    def test_integration_with_mermaid_config(self):
        """Test profiling config integration with MermaidConfig."""
        profiling_config = ProfilingConfig(enabled=True, print_reports=True)
        mermaid_config = MermaidConfig(profiling=profiling_config)

        assert mermaid_config.profiling.enabled is True
        assert mermaid_config.profiling.print_reports is True


class TestIntegration:
    """Integration tests for profiling system."""

    def setup_method(self):
        """Setup for integration tests."""
        clear_registry()
        reset_config()

    def teardown_method(self):
        """Teardown after integration tests."""
        reset_config()

    def test_end_to_end_profiling(self):
        """Test complete profiling workflow."""
        # Enable profiling
        config = MermaidConfig(profiling=ProfilingConfig(enabled=True))
        set_config(config)

        # Simulate generator workflow
        with PerformanceProfiler('TestGenerator.generate', enabled=True) as profiler:
            profiler.add_metadata('generator', 'TestGenerator')
            profiler.add_metadata('output_file', 'test.md')

            profiler.checkpoint('validation_complete')
            time.sleep(0.01)

            profiler.checkpoint('body_generated')
            time.sleep(0.01)

            profiler.checkpoint('files_written')

        report = profiler.get_report()

        # Verify report contents
        assert report.operation_name == 'TestGenerator.generate'
        assert report.total_time > 0.02
        assert report.metadata['generator'] == 'TestGenerator'
        assert len(report.checkpoints) >= 5  # start + 3 checkpoints + end

        # Verify checkpoints
        checkpoint_names = [cp.name for cp in report.checkpoints]
        assert 'validation_complete' in checkpoint_names
        assert 'body_generated' in checkpoint_names
        assert 'files_written' in checkpoint_names
