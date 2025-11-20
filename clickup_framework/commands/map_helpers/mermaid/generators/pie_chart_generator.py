"""Pie chart diagram generator."""

from .base_generator import BaseGenerator


class PieChartGenerator(BaseGenerator):
    """Generate pie chart diagrams showing language distribution."""

    def validate_inputs(self, **kwargs) -> None:
        """Validate pie chart diagram specific inputs."""
        by_language = self.stats.get('by_language', {})
        if not by_language:
            raise ValueError("No by_language data found in stats")

    def generate_body(self, **kwargs) -> None:
        """Generate pie chart diagram body."""
        by_language = self.stats.get('by_language', {})

        self._add_diagram_declaration("pie title Code Distribution by Language")

        for lang in sorted(by_language.keys()):
            count = sum(by_language[lang].values())
            self._add_line(f'    "{lang}" : {count}')
