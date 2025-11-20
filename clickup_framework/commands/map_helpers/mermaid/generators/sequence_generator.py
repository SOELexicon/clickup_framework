"""Sequence diagram generator."""

from .base_generator import BaseGenerator


class SequenceGenerator(BaseGenerator):
    """Generate sequence diagrams showing typical execution flow."""

    def validate_inputs(self, **kwargs) -> None:
        """Validate sequence diagram specific inputs."""
        function_calls = self.stats.get('function_calls', {})
        all_symbols = self.stats.get('all_symbols', {})
        if not function_calls or not all_symbols:
            raise ValueError("No function_calls or all_symbols data found in stats")

    def generate_body(self, **kwargs) -> None:
        """Generate sequence diagram body."""
        function_calls = self.stats.get('function_calls', {})
        all_symbols = self.stats.get('all_symbols', {})

        self._add_diagram_declaration("sequenceDiagram")

        entry_patterns = ['main', '__init__', 'run', 'execute', 'start', 'process']
        entry_funcs = []

        for func_name in function_calls.keys():
            short_name = func_name.split('.')[-1].lower()
            if any(pattern in short_name for pattern in entry_patterns):
                entry_funcs.append(func_name)

        if not entry_funcs:
            entry_funcs = sorted(function_calls.keys(),
                               key=lambda f: len(function_calls.get(f, [])),
                               reverse=True)[:3]

        if entry_funcs:
            entry = entry_funcs[0]
            participants = set()

            def trace_calls(func, depth=0, max_depth=5):
                if depth > max_depth:
                    return

                symbol = all_symbols.get(func, {})
                scope = symbol.get('scope', 'Module')
                func_short = func.split('.')[-1]

                if scope:
                    participants.add(scope)

                for called in function_calls.get(func, [])[:3]:
                    called_symbol = all_symbols.get(called, {})
                    called_scope = called_symbol.get('scope', 'Module')
                    called_short = called.split('.')[-1]

                    if called_scope:
                        participants.add(called_scope)

                    from_participant = scope if scope else 'Module'
                    to_participant = called_scope if called_scope else 'Module'

                    self._add_line(f"    {from_participant}->>+{to_participant}: {called_short}()")
                    trace_calls(called, depth + 1, max_depth)
                    self._add_line(f"    {to_participant}-->>-{from_participant}: return")

            for participant in sorted(participants)[:10]:
                self.lines.insert(len(self.lines) - len([l for l in self.lines if '->>' in l]), f"    participant {participant}")

            entry_short = entry.split('.')[-1]
            entry_scope = all_symbols.get(entry, {}).get('scope', 'Main')
            if entry_scope:
                self._add_line(f"    Note over {entry_scope}: {entry_short}() starts")
            trace_calls(entry, depth=0, max_depth=4)

    def _add_footer(self) -> None:
        """Override footer to add sequence-specific description."""
        self.lines.extend([
            "```",
            "",
            "## Description",
            "This sequence diagram shows the typical execution flow starting from an entry point.",
            "Arrows show function calls and returns between different components.",
        ])

        # Add entry point info
        function_calls = self.stats.get('function_calls', {})
        entry_patterns = ['main', '__init__', 'run', 'execute', 'start', 'process']
        entry_funcs = []

        for func_name in function_calls.keys():
            short_name = func_name.split('.')[-1].lower()
            if any(pattern in short_name for pattern in entry_patterns):
                entry_funcs.append(func_name)

        if not entry_funcs:
            entry_funcs = sorted(function_calls.keys(),
                               key=lambda f: len(function_calls.get(f, [])),
                               reverse=True)[:3]

        self.lines.extend([
            "",
            f"## Entry Point",
            f"- Starting from: `{entry_funcs[0] if entry_funcs else 'N/A'}`",
        ])

        # Don't call parent _add_footer as we're replacing it entirely
