# Image Export Utility Usage

The `console_to_jpg` utility function allows any command to export its output to a JPG image with customizable background colors.

## Location

The utility is located in `clickup_framework/utils/image_export.py` and is available through:

```python
from clickup_framework.utils.image_export import console_to_jpg
# Or
from clickup_framework.utils import console_to_jpg
```

## Basic Usage

### Standalone Function

```python
from clickup_framework.utils.image_export import console_to_jpg

# Convert text output to JPG
output_text = "Hello World\nWith ANSI colors: \x1b[31mRed\x1b[0m"
console_to_jpg(output_text, "output.jpg", bg_color="black")
```

### In BaseCommand

Commands extending `BaseCommand` can use the built-in method:

```python
from clickup_framework.commands.base_command import BaseCommand

class MyCommand(BaseCommand):
    def execute(self):
        # Your command logic here
        self.print("Task hierarchy:")
        # ... output code ...
        
        # Export to JPG
        if hasattr(self.args, 'export_jpg') and self.args.export_jpg:
            self.export_output_to_jpg(
                self.args.export_jpg,
                bg_color="black",
                width=1200
            )
```

### From Command Line

```bash
# Pipe command output to JPG
cum h 86c6hvz7y --depth 3 -cf -p 3 --colorize | python scripts/console_to_jpg.py - output.jpg 1200 black

# Or use the utility directly in Python
python -c "from clickup_framework.utils.image_export import console_to_jpg; import sys; console_to_jpg(sys.stdin.read(), 'output.jpg', 1200, 'black')"
```

## Function Signature

```python
def console_to_jpg(
    text: str,
    output_path: str,
    width: int = 1200,
    bg_color: str = "black",
    quality: int = 95
) -> bool:
    """
    Convert console/ANSI output to JPG image.
    
    Args:
        text: Text string (may contain ANSI color codes)
        output_path: Path to output JPG file
        width: Image width in pixels (default: 1200)
        bg_color: Background color - "black" or "white" (default: "black")
        quality: JPG quality 1-100 (default: 95)
    
    Returns:
        True if successful, False otherwise
    """
```

## Parameters

- **text**: The console output text (supports ANSI color codes)
- **output_path**: Full path to the output JPG file
- **width**: Image width in pixels (default: 1200)
- **bg_color**: Background color - `"black"` or `"white"` (default: `"black"`)
- **quality**: JPG compression quality 1-100 (default: 95)

## Examples

### Example 1: Export Hierarchy Command

```python
from clickup_framework.utils.image_export import console_to_jpg
import subprocess

# Run command and capture output
result = subprocess.run(
    ['cum', 'h', '86c6hvz7y', '--depth', '3', '-cf', '-p', '3', '--colorize'],
    capture_output=True,
    text=True
)

# Export to JPG
console_to_jpg(result.stdout, "hierarchy.jpg", bg_color="black")
```

### Example 2: In a Command Class

```python
class HierarchyCommand(BaseCommand):
    def execute(self):
        task_id = self.resolve_id('task', self.args.task_id)
        
        # Generate hierarchy output
        hierarchy = self.client.get_task_hierarchy(task_id, depth=3)
        output = self._format_hierarchy(hierarchy)
        
        # Export if requested
        if hasattr(self.args, 'export') and self.args.export:
            self.export_output_to_jpg(
                self.args.export,
                output_text=output,
                bg_color="black"
            )
        else:
            self.print(output)
```

### Example 3: Capture Function Output

```python
from clickup_framework.utils.image_export import capture_command_output_to_jpg

def my_command():
    print("Hello")
    print("World")

# Capture and export
capture_command_output_to_jpg(
    my_command,
    "output.jpg",
    width=1200,
    bg_color="black"
)
```

## Features

- **ANSI Color Support**: Preserves ANSI color codes when using Rich library
- **Fallback Support**: Falls back to PIL if Rich is unavailable (strips ANSI codes)
- **Customizable**: Adjustable width, background color, and quality
- **Cross-platform**: Works on Windows, Linux, and macOS
- **Font Detection**: Automatically finds monospace fonts on the system

## Requirements

- **Pillow (PIL)**: Required for image generation
  ```bash
  pip install pillow
  ```

- **Rich**: Optional, but recommended for better ANSI color support
  ```bash
  pip install rich
  ```

## Integration with Commands

To add JPG export capability to any command:

1. **Add argument to command parser**:
   ```python
   parser.add_argument('--export-jpg', help='Export output to JPG file')
   ```

2. **Use in command execution**:
   ```python
   if self.args.export_jpg:
       self.export_output_to_jpg(self.args.export_jpg, bg_color="black")
   ```

3. **Or use standalone function**:
   ```python
   from clickup_framework.utils.image_export import console_to_jpg
   console_to_jpg(output_text, output_path, bg_color="black")
   ```

## See Also

- `clickup_framework/utils/image_export.py` - Full implementation
- `clickup_framework/commands/base_command.py` - BaseCommand with export method
- `scripts/console_to_jpg.py` - CLI wrapper script

