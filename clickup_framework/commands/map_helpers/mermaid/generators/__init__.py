"""Mermaid diagram generators.

This module provides generator classes for creating various types of Mermaid diagrams.
All generators inherit from BaseGenerator and follow the template method pattern.

Available Generators:
    BaseGenerator - Abstract base class for all generators (template method pattern)

Usage:
    from clickup_framework.commands.map_helpers.mermaid.generators import BaseGenerator

    class MyGenerator(BaseGenerator):
        def validate_inputs(self, **kwargs):
            pass

        def generate_body(self, **kwargs):
            self._add_diagram_declaration('graph TD')
            # ... add nodes and edges
"""

from .base_generator import BaseGenerator

__all__ = [
    'BaseGenerator',
]
