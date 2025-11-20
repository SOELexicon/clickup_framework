"""Class diagram generator."""

from pathlib import Path
from .base_generator import BaseGenerator
from ..config import get_config
from ..exceptions import DataValidationError


class ClassDiagramGenerator(BaseGenerator):
    """Generate class diagrams showing detailed code structure with inheritance."""

    def __init__(self, *args, **kwargs):
        """Initialize class diagram generator with configuration."""
        super().__init__(*args, **kwargs)
        self.config = get_config().class_diagram

    def validate_inputs(self, **kwargs) -> None:
        """Validate class diagram specific inputs."""
        symbols_by_file = self.stats.get('symbols_by_file', {})
        if not symbols_by_file:
            raise DataValidationError.missing_required_field(
                field_name='symbols_by_file',
                generator_type='class_diagram',
                stats_keys=list(self.stats.keys())
            )

    def generate_body(self, **kwargs) -> None:
        """Generate class diagram body."""
        symbols_by_file = self.stats.get('symbols_by_file', {})

        self._add_diagram_declaration("classDiagram")

        all_classes = {}
        class_count = 0

        for file_path, symbols in sorted(symbols_by_file.items()):
            if class_count >= self.config.max_classes:
                break

            classes = [s for s in symbols if s.get('kind') == 'class']
            for cls in classes:
                class_name = cls.get('name', 'Unknown')

                if class_name in all_classes:
                    continue

                all_classes[class_name] = {
                    'file': Path(file_path).name,
                    'line': cls.get('line', 0),
                    'methods': [],
                    'members': []
                }

                methods = [s for s in symbols
                          if s.get('scope') == class_name
                          and s.get('kind') in ['function', 'method']]

                members = [s for s in symbols
                          if s.get('scope') == class_name
                          and s.get('kind') in ['member', 'variable']]

                all_classes[class_name]['methods'] = methods[:self.config.max_methods_per_class]
                all_classes[class_name]['members'] = members[:self.config.max_members_per_class]

                class_count += 1

        for class_name, details in sorted(all_classes.items()):
            self._add_line(f"    class {class_name} {{")
            self._add_line(f"        <<{details['file']}>>")

            for member in details['members']:
                member_name = member.get('name', '')
                self._add_line(f"        -{member_name}")

            for method in details['methods']:
                method_name = method.get('name', '')
                if method_name.startswith('__'):
                    visibility = '-'
                elif method_name.startswith('_'):
                    visibility = '-'
                else:
                    visibility = '+'
                self._add_line(f"        {visibility}{method_name}()")

            self._add_line("    }")

        self._add_line("")
        self._add_line("    %% Inheritance relationships")
        for class_name in all_classes.keys():
            if 'Base' in class_name:
                for other_class in all_classes.keys():
                    if other_class != class_name and 'Base' not in other_class:
                        if any(word in other_class for word in class_name.replace('Base', '').split()):
                            self._add_line(f"    {class_name} <|-- {other_class}")
