"""Pie chart diagram generator."""

from .base_generator import BaseGenerator
from ..exceptions import DataValidationError


class PieChartGenerator(BaseGenerator):
    """Generate pie chart diagrams showing language distribution."""

    def validate_inputs(self, **kwargs) -> None:
        """Validate pie chart diagram specific inputs."""
        by_language = self.stats.get('by_language', {})
        if not by_language:
            raise DataValidationError.missing_required_field(
                field_name='by_language',
                generator_type='pie_chart',
                stats_keys=list(self.stats.keys())
            )

    def generate_body(self, **kwargs) -> None:
        """Generate pie chart diagram body."""
        by_language = self.stats.get('by_language', {})

        self._add_diagram_declaration("pie title Code Distribution by Language")

        for lang in sorted(by_language.keys()):
            count = sum(by_language[lang].values())
            self._add_line(f'    "{lang}" : {count}')
