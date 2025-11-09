"""
Common Formatting Utilities

This package contains common formatting utilities for the CLI.

Task: tsk_1e88842d - Tree Structure Validation
dohcount: 1
"""

from refactor.cli.formatting.common.tags import format_tag_line, TAG_EMOJI
from refactor.cli.formatting.common.task_info import format_task_basic_info, format_task_score
from refactor.cli.formatting.common.display_options import DisplayOptions, process_display_options

# Add logger setup for the common formatting module
import logging

# Create logger for the formatting modules
logger = logging.getLogger('refactor.cli.formatting')

# The logger will be configured at the application level, so we don't set
# handlers or levels here. This just ensures the logger is available.

__all__ = [
    'format_tag_line',
    'TAG_EMOJI',
    'format_task_basic_info',
    'format_task_score',
    'DisplayOptions',
    'process_display_options'
] 