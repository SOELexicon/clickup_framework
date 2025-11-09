"""
ANSI Animation Utilities

Provides animated terminal output effects for displaying workspace IDs,
current context, and other CLI elements with visual flair.

Features:
- Gradient text effects
- Pulsing/glowing animations
- Typewriter effects
- Color cycling
- Box drawing with animated borders
"""

import time
import sys
from typing import Optional, List
from clickup_framework.utils.colors import TextColor, colorize, TextStyle


class ANSIAnimations:
    """ANSI animation utilities for terminal output."""

    # Gradient color sequences
    GRADIENT_RAINBOW = [
        TextColor.BRIGHT_RED,
        TextColor.BRIGHT_YELLOW,
        TextColor.BRIGHT_GREEN,
        TextColor.BRIGHT_CYAN,
        TextColor.BRIGHT_BLUE,
        TextColor.BRIGHT_MAGENTA,
    ]

    GRADIENT_BLUE_PURPLE = [
        TextColor.BRIGHT_BLUE,
        TextColor.BLUE,
        TextColor.MAGENTA,
        TextColor.BRIGHT_MAGENTA,
    ]

    GRADIENT_FIRE = [
        TextColor.BRIGHT_RED,
        TextColor.RED,
        TextColor.BRIGHT_YELLOW,
        TextColor.YELLOW,
    ]

    GRADIENT_OCEAN = [
        TextColor.BRIGHT_CYAN,
        TextColor.CYAN,
        TextColor.BRIGHT_BLUE,
        TextColor.BLUE,
    ]

    @staticmethod
    def gradient_text(text: str, colors: Optional[List[TextColor]] = None) -> str:
        """
        Apply a gradient color effect to text.

        Args:
            text: Text to colorize
            colors: List of colors for gradient (defaults to GRADIENT_RAINBOW)

        Returns:
            String with gradient color codes
        """
        if not colors:
            colors = ANSIAnimations.GRADIENT_RAINBOW

        if len(text) == 0:
            return text

        result = []
        color_count = len(colors)

        for i, char in enumerate(text):
            if char == ' ':
                result.append(char)
            else:
                # Calculate which color to use based on position
                color_idx = int((i / len(text)) * color_count) % color_count
                result.append(colorize(char, colors[color_idx]))

        return ''.join(result)

    @staticmethod
    def pulse_text(text: str, color: TextColor = TextColor.BRIGHT_CYAN,
                   pulse_count: int = 3, delay: float = 0.3) -> None:
        """
        Display text with a pulsing effect.

        Args:
            text: Text to display
            color: Color to pulse
            pulse_count: Number of pulses
            delay: Delay between pulses in seconds
        """
        for _ in range(pulse_count):
            # Bright
            sys.stdout.write('\r' + colorize(text, color, TextStyle.BOLD))
            sys.stdout.flush()
            time.sleep(delay)

            # Dim
            sys.stdout.write('\r' + colorize(text, color))
            sys.stdout.flush()
            time.sleep(delay)

        # Final bright
        sys.stdout.write('\r' + colorize(text, color, TextStyle.BOLD) + '\n')
        sys.stdout.flush()

    @staticmethod
    def typewriter_text(text: str, color: Optional[TextColor] = None,
                       delay: float = 0.05) -> None:
        """
        Display text with a typewriter effect.

        Args:
            text: Text to display
            color: Optional color
            delay: Delay between characters
        """
        for char in text:
            if color:
                sys.stdout.write(colorize(char, color))
            else:
                sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        sys.stdout.write('\n')

    @staticmethod
    def animated_box(title: str, content: List[str],
                    color: TextColor = TextColor.BRIGHT_BLUE,
                    width: Optional[int] = None) -> str:
        """
        Create a box with animated-style borders.

        Args:
            title: Box title
            content: List of content lines
            color: Border color
            width: Box width (auto-calculated if None)

        Returns:
            Formatted box string
        """
        from .colors import strip_ansi

        # Calculate width (strip ANSI codes for accurate measurement)
        if width is None:
            max_content_len = max(len(strip_ansi(line)) for line in content) if content else 20
            title_len = len(strip_ansi(title))
            width = max(max_content_len, title_len) + 4

        # Box drawing characters
        top_left = "╔"
        top_right = "╗"
        bottom_left = "╚"
        bottom_right = "╝"
        horizontal = "═"
        vertical = "║"

        lines = []

        # Top border with title
        title_len_visible = len(strip_ansi(title))
        top_line = (
            colorize(top_left + horizontal * 2, color) +
            " " + title + " " +
            colorize(horizontal * (width - title_len_visible - 5) + top_right, color)
        )
        lines.append(top_line)

        # Content lines
        for line in content:
            line_len_visible = len(strip_ansi(line))
            padding = width - line_len_visible - 4
            content_line = (
                colorize(vertical, color) +
                " " + line + " " * padding + " " +
                colorize(vertical, color)
            )
            lines.append(content_line)

        # Bottom border
        bottom_line = colorize(bottom_left + horizontal * (width - 2) + bottom_right, color)
        lines.append(bottom_line)

        return '\n'.join(lines)

    @staticmethod
    def spinning_indicator(duration: float = 2.0, message: str = "Loading") -> None:
        """
        Display a spinning indicator animation.

        Args:
            duration: How long to spin (seconds)
            message: Message to display next to spinner
        """
        frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        end_time = time.time() + duration
        i = 0

        while time.time() < end_time:
            frame = frames[i % len(frames)]
            sys.stdout.write(f'\r{colorize(frame, TextColor.BRIGHT_CYAN)} {message}...')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

        sys.stdout.write('\r' + ' ' * (len(message) + 10) + '\r')
        sys.stdout.flush()

    @staticmethod
    def rainbow_banner(text: str, width: Optional[int] = None) -> str:
        """
        Create a rainbow-colored banner.

        Args:
            text: Banner text
            width: Banner width (defaults to terminal width or 80)

        Returns:
            Formatted banner string
        """
        if width is None:
            try:
                import shutil
                width = shutil.get_terminal_size().columns
            except:
                width = 80

        # Create top and bottom borders
        border = '━' * width
        top_border = ANSIAnimations.gradient_text(border, ANSIAnimations.GRADIENT_RAINBOW)
        bottom_border = top_border

        # Center the text
        padding = (width - len(text)) // 2
        centered_text = ' ' * padding + text + ' ' * (width - len(text) - padding)
        colored_text = ANSIAnimations.gradient_text(centered_text, ANSIAnimations.GRADIENT_RAINBOW)

        return f"{top_border}\n{colored_text}\n{bottom_border}"

    @staticmethod
    def highlight_id(label: str, id_value: str,
                    label_color: TextColor = TextColor.BRIGHT_BLACK,
                    id_color: TextColor = TextColor.BRIGHT_CYAN) -> str:
        """
        Format an ID with label in a highlighted style.

        Args:
            label: Label text (e.g., "Workspace ID")
            id_value: The ID value
            label_color: Color for label
            id_color: Color for ID

        Returns:
            Formatted string
        """
        return (
            colorize(label + ": ", label_color) +
            colorize(id_value, id_color, TextStyle.BOLD)
        )

    @staticmethod
    def success_message(message: str) -> str:
        """Format a success message with checkmark."""
        checkmark = "✓"
        return colorize(f"{checkmark} {message}", TextColor.BRIGHT_GREEN, TextStyle.BOLD)

    @staticmethod
    def error_message(message: str) -> str:
        """Format an error message with X mark."""
        xmark = "✗"
        return colorize(f"{xmark} {message}", TextColor.BRIGHT_RED, TextStyle.BOLD)

    @staticmethod
    def info_message(message: str) -> str:
        """Format an info message with info icon."""
        info_icon = "ℹ"
        return colorize(f"{info_icon} {message}", TextColor.BRIGHT_BLUE, TextStyle.BOLD)

    @staticmethod
    def warning_message(message: str) -> str:
        """Format a warning message with warning icon."""
        warning_icon = "⚠"
        return colorize(f"{warning_icon} {message}", TextColor.BRIGHT_YELLOW, TextStyle.BOLD)


def demo_animations():
    """Demo function showing various animation effects."""
    print("\n" + "=" * 60)
    print("ANSI Animation Demo")
    print("=" * 60 + "\n")

    # Gradient text
    print("1. Gradient Text:")
    print(ANSIAnimations.gradient_text("Rainbow Gradient Text!", ANSIAnimations.GRADIENT_RAINBOW))
    print(ANSIAnimations.gradient_text("Ocean Gradient Text!", ANSIAnimations.GRADIENT_OCEAN))
    print(ANSIAnimations.gradient_text("Fire Gradient Text!", ANSIAnimations.GRADIENT_FIRE))
    print()

    # Highlighted IDs
    print("2. Highlighted IDs:")
    print(ANSIAnimations.highlight_id("Workspace ID", "90151898946"))
    print(ANSIAnimations.highlight_id("Task ID", "86c6e0q06", id_color=TextColor.BRIGHT_MAGENTA))
    print()

    # Animated box
    print("3. Animated Box:")
    box = ANSIAnimations.animated_box(
        "Current Context",
        [
            ANSIAnimations.highlight_id("Workspace", "90151898946"),
            ANSIAnimations.highlight_id("List", "901517404278"),
            ANSIAnimations.highlight_id("Task", "86c6e0q06"),
        ],
        color=TextColor.BRIGHT_CYAN
    )
    print(box)
    print()

    # Messages
    print("4. Status Messages:")
    print(ANSIAnimations.success_message("Operation completed successfully!"))
    print(ANSIAnimations.error_message("An error occurred!"))
    print(ANSIAnimations.info_message("Information message"))
    print(ANSIAnimations.warning_message("Warning message"))
    print()

    # Banner
    print("5. Rainbow Banner:")
    print(ANSIAnimations.rainbow_banner("CLI Framework"))
    print()

    # Typewriter (slower, so we'll keep it short)
    print("6. Typewriter Effect:")
    ANSIAnimations.typewriter_text("Loading CLI...", TextColor.BRIGHT_GREEN, delay=0.03)
    print()

    # Pulse effect
    print("7. Pulse Effect:")
    ANSIAnimations.pulse_text("⚡ Status Updated!", TextColor.BRIGHT_YELLOW, pulse_count=2, delay=0.2)
    print()

    # Spinner
    print("8. Spinning Indicator:")
    ANSIAnimations.spinning_indicator(1.5, "Processing")
    print(ANSIAnimations.success_message("Done!"))
    print()

    print("=" * 60)


if __name__ == "__main__":
    demo_animations()
