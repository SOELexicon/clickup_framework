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
    def animated_rainbow_text(text: str, frame: int = 0, speed: float = 1.0) -> str:
        """
        Create animated rainbow text that cycles through colors.
        
        Args:
            text: Text to animate
            frame: Current animation frame (increments for animation)
            speed: Speed multiplier (higher = faster)
            
        Returns:
            String with animated rainbow color codes
        """
        if len(text) == 0:
            return text
        
        colors = ANSIAnimations.GRADIENT_RAINBOW
        result = []
        color_count = len(colors)
        
        # Offset based on frame for animation
        offset = int(frame * speed) % color_count
        
        for i, char in enumerate(text):
            if char == ' ':
                result.append(char)
            else:
                # Calculate color with animation offset
                color_idx = (int((i / len(text)) * color_count) + offset) % color_count
                result.append(colorize(char, colors[color_idx]))
        
        return ''.join(result)

    @staticmethod
    def white_sheen_text(text: str, base_color: TextColor = TextColor.BRIGHT_CYAN) -> str:
        """
        Apply enhanced brightness to colored text (clean bold effect).
        Uses bold base color for a clean, bright appearance without jarring patterns.
        
        Args:
            text: Text to enhance
            base_color: Base color for the text
            
        Returns:
            String with enhanced brightness
        """
        # Simply use bold base color for clean, bright appearance
        # No white mixing to avoid checkerboard patterns
        return colorize(text, base_color, TextStyle.BOLD)

    @staticmethod
    def _ansi_256_color(color_num: int) -> str:
        """Get ANSI 256-color escape code."""
        return f"\033[38;5;{color_num}m"
    
    @staticmethod
    def _get_rainbow_256_colors() -> list:
        """Get a smooth rainbow gradient using 256-color palette."""
        # Use bright, vibrant colors from 256-color palette
        # These color numbers create a smooth rainbow spectrum
        # Format: Red -> Orange -> Yellow -> Green -> Cyan -> Blue -> Magenta -> Red
        
        # Bright rainbow colors from 256-color palette (vibrant spectrum)
        rainbow = [
            # Red to Orange
            196, 202, 208, 214, 220,
            # Orange to Yellow  
            226, 227, 228, 229, 230,
            # Yellow to Green
            190, 184, 178, 172, 166, 160, 154, 148, 142, 136, 130, 124, 118, 112, 106, 100, 94, 88, 82, 76, 70, 64, 58, 52, 46,
            # Green to Cyan
            47, 48, 49, 50, 51,
            # Cyan to Blue
            45, 39, 33, 27, 21,
            # Blue to Magenta
            57, 63, 69, 75, 81, 87, 93, 99, 105, 111, 117, 123, 129, 135, 141, 147, 153, 159, 165,
            # Magenta to Red
            171, 177, 183, 189, 195, 201, 207, 213, 219, 225
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_rainbow = []
        for color in rainbow:
            if color not in seen:
                seen.add(color)
                unique_rainbow.append(color)
        
        return unique_rainbow
    
    @staticmethod
    def display_animated_rainbow(text: str, duration: float = 2.0, speed: float = 2.0) -> None:
        """
        Display text with smooth sliding rainbow wave animation using 256-color ANSI codes.
        Creates a wave effect that smoothly slides across the text surface.
        
        Args:
            text: Text to animate
            duration: How long to animate (seconds)
            speed: Animation speed multiplier (wave speed)
        """
        import time
        
        # Get smooth rainbow color palette
        rainbow_colors = ANSIAnimations._get_rainbow_256_colors()
        color_count = len(rainbow_colors)
        
        # Higher frame rate for smoother animation
        frames = int(duration * 20)  # 20 frames per second for very smooth animation
        frame_delay = max(0.05, duration / frames)
        
        reset_code = "\033[0m"
        bold_code = "\033[1m"
        
        # Create smooth sliding wave effect
        for frame in range(frames):
            # Calculate wave offset - this creates the sliding effect
            # Use a smooth progression that wraps around
            wave_offset = (frame * speed * 2.0) % color_count
            
            # Build animated text with sliding rainbow wave
            result = []
            for i, char in enumerate(text):
                if char == ' ':
                    result.append(char)
                else:
                    # Calculate position in the wave
                    # Use the character position plus wave offset to create sliding effect
                    # The wave moves from left to right (or right to left)
                    char_pos = i / max(len(text), 1)  # Normalized position 0-1
                    
                    # Create wave pattern: position in color spectrum
                    # Add wave_offset to make it slide
                    wave_position = (char_pos * color_count + wave_offset) % color_count
                    color_idx = int(wave_position)
                    
                    # Ensure we stay within bounds
                    color_idx = color_idx % color_count
                    color_num = rainbow_colors[color_idx]
                    
                    # Use 256-color ANSI code with bold
                    result.append(f"{bold_code}{ANSIAnimations._ansi_256_color(color_num)}{char}")
            
            # Add single reset at the end
            animated_text = ''.join(result) + reset_code
            
            # Clear line and write animated text
            sys.stdout.write(f'\r\033[K{animated_text}')
            sys.stdout.flush()
            time.sleep(frame_delay)
        
        # Final frame - keep it visible with final wave position
        final_wave_offset = (frames * speed * 2.0) % color_count
        result = []
        for i, char in enumerate(text):
            if char == ' ':
                result.append(char)
            else:
                char_pos = i / max(len(text), 1)
                wave_position = (char_pos * color_count + final_wave_offset) % color_count
                color_idx = int(wave_position) % color_count
                color_num = rainbow_colors[color_idx]
                result.append(f"{bold_code}{ANSIAnimations._ansi_256_color(color_num)}{char}")
        
        final_text = ''.join(result) + reset_code
        sys.stdout.write(f'\r\033[K{final_text}\n')
        sys.stdout.flush()

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

    @staticmethod
    def looping_animation(message: str = "Working", stop_event=None) -> None:
        """
        Display a looping animation that runs until stop_event is set.
        Designed to run in a background thread while a long process executes.

        Shows funny rotating ASCII art with colorful effects.

        Args:
            message: Message to display with the animation
            stop_event: threading.Event to signal when to stop
        """
        import threading

        # Funny rotating ASCII frames - bouncing droplets theme
        frames = [
            "💧    ",
            " 💧   ",
            "  💧  ",
            "   💧 ",
            "    💧",
            "   💧 ",
            "  💧  ",
            " 💧   ",
        ]

        # Alternative frames for extra flair
        emoji_frames = [
            "🌊",
            "💦",
            "💧",
            "💦",
        ]

        colors = [
            TextColor.BRIGHT_CYAN,
            TextColor.BRIGHT_BLUE,
            TextColor.BRIGHT_MAGENTA,
            TextColor.BRIGHT_CYAN,
        ]

        i = 0
        emoji_i = 0

        # If no stop_event provided, create a dummy one that never triggers
        if stop_event is None:
            stop_event = threading.Event()

        while not stop_event.is_set():
            # Get current frame and emoji
            frame = frames[i % len(frames)]
            emoji = emoji_frames[emoji_i % len(emoji_frames)]
            color = colors[i % len(colors)]

            # Create animated message
            colored_msg = colorize(message, color, TextStyle.BOLD)
            animated_line = f"\r{emoji} {frame} {colored_msg}... {frame} {emoji}"

            sys.stdout.write(animated_line)
            sys.stdout.flush()

            time.sleep(0.12)
            i += 1

            # Emoji changes slower than frames
            if i % 2 == 0:
                emoji_i += 1

        # Clear the line when done
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()

    @staticmethod
    def run_with_looping_animation(func, message: str = "Working"):
        """
        Run a function with a looping animation in the background.

        Args:
            func: Function to execute (should be a callable)
            message: Message to display with animation

        Returns:
            The return value of func
        """
        import threading

        stop_event = threading.Event()

        # Start animation in background thread
        anim_thread = threading.Thread(
            target=ANSIAnimations.looping_animation,
            args=(message, stop_event),
            daemon=True
        )
        anim_thread.start()

        try:
            # Run the actual function
            result = func()
        finally:
            # Stop animation
            stop_event.set()
            anim_thread.join(timeout=1.0)

        return result


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
