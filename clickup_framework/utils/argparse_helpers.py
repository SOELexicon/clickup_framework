"""Shared argparse formatter helpers for CLI help output."""

import argparse
from functools import partial


def raw_text_formatter(max_help_position: int = 32, width: int = 100):
    """Return a configured RawTextHelpFormatter factory for argparse."""
    return partial(
        argparse.RawTextHelpFormatter,
        max_help_position=max_help_position,
        width=width,
    )


def raw_description_formatter(max_help_position: int = 40, width: int = 80):
    """Return a configured RawDescriptionHelpFormatter factory for argparse."""
    return partial(
        argparse.RawDescriptionHelpFormatter,
        max_help_position=max_help_position,
        width=width,
    )

