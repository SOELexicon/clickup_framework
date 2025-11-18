"""
Console output to image export utilities.

Provides functions to convert console/ANSI output to JPG/PNG images
for use in commands and documentation.
"""

import sys
import os
import re
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from rich.console import Console
    from rich.terminal_theme import TerminalTheme
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def console_to_jpg(
    text: str,
    output_path: str,
    width: int = 1200,
    bg_color: str = "black",
    quality: int = 95
) -> bool:
    """
    Convert console/ANSI output to JPG image with specified background color.
    
    This function attempts to use Rich for better ANSI color support,
    falling back to PIL for basic text rendering if Rich is unavailable.
    
    Args:
        text: Text string (may contain ANSI color codes)
        output_path: Path to output JPG file
        width: Image width in pixels (default: 1200)
        bg_color: Background color - "black" or "white" (default: "black")
        quality: JPG quality 1-100 (default: 95)
    
    Returns:
        True if successful, False otherwise
    
    Raises:
        ImportError: If neither PIL nor Rich are available
        IOError: If output file cannot be written
    
    Example:
        >>> from clickup_framework.utils.image_export import console_to_jpg
        >>> output = "Hello \\x1b[31mWorld\\x1b[0m"
        >>> console_to_jpg(output, "output.jpg", bg_color="black")
        True
    """
    if not PIL_AVAILABLE and not RICH_AVAILABLE:
        raise ImportError(
            "Neither PIL/Pillow nor Rich are available. "
            "Install with: pip install pillow rich"
        )
    
    # Try Rich method first (better ANSI support)
    if RICH_AVAILABLE:
        try:
            return _rich_ansi_to_jpg(text, output_path, width, bg_color, quality)
        except Exception:
            # Fall back to PIL if Rich fails
            pass
    
    # Fallback to PIL method
    if PIL_AVAILABLE:
        return _pil_text_to_jpg(text, output_path, width, bg_color, quality)
    
    return False


def _rich_ansi_to_jpg(
    text: str,
    output_path: str,
    width: int,
    bg_color: str,
    quality: int
) -> bool:
    """Convert ANSI text to JPG using Rich library with proper emoji and color support."""
    import io
    
    # Calculate console width (approximate 8 pixels per character)
    console_width = min(width // 8, 200)
    
    # Create a StringIO buffer to avoid Windows console encoding issues
    # This prevents Rich from trying to write emojis to Windows console (cp1252)
    file_buffer = io.StringIO()
    
    # Create console with proper settings for emoji and color support
    # file=None prevents writing to actual console, which causes encoding issues on Windows
    console = Console(
        file=file_buffer,  # Write to buffer instead of stdout
        width=console_width,
        record=True,
        force_terminal=False,  # Don't force terminal mode (avoids Windows console issues)
        legacy_windows=False,  # Better Unicode support
        emoji=True,  # Enable emoji rendering
        color_system="standard",  # Full color support
        _environ={},  # Don't check environment variables
    )
    
    # Print text to console (which records it with ANSI codes)
    # Use markup=False to preserve ANSI codes, not interpret as Rich markup
    console.print(text, markup=False, highlight=True)
    
    # Create theme with proper color palette for ANSI colors
    if bg_color.lower() == "black":
        # Black background with full ANSI color palette
        theme = TerminalTheme(
            (0, 0, 0),  # background (black)
            (255, 255, 255),  # foreground (white)
            # Standard ANSI colors (16 colors)
            [
                (0, 0, 0),       # 0: black
                (128, 0, 0),     # 1: red
                (0, 128, 0),     # 2: green
                (128, 128, 0),   # 3: yellow
                (0, 0, 128),     # 4: blue
                (128, 0, 128),   # 5: magenta
                (0, 128, 128),   # 6: cyan
                (192, 192, 192), # 7: white
                (128, 128, 128), # 8: bright black
                (255, 0, 0),     # 9: bright red
                (0, 255, 0),     # 10: bright green
                (255, 255, 0),   # 11: bright yellow
                (0, 0, 255),     # 12: bright blue
                (255, 0, 255),   # 13: bright magenta
                (0, 255, 255),   # 14: bright cyan
                (255, 255, 255), # 15: bright white
            ],
            # Bright colors (same as standard for simplicity)
            [
                (0, 0, 0),
                (255, 0, 0),
                (0, 255, 0),
                (255, 255, 0),
                (0, 0, 255),
                (255, 0, 255),
                (0, 255, 255),
                (255, 255, 255),
                (128, 128, 128),
                (255, 128, 128),
                (128, 255, 128),
                (255, 255, 128),
                (128, 128, 255),
                (255, 128, 255),
                (128, 255, 255),
                (255, 255, 255),
            ],
        )
    else:
        # White background
        theme = TerminalTheme(
            (255, 255, 255),  # background (white)
            (0, 0, 0),  # foreground (black)
            # Standard ANSI colors (adjusted for white background)
            [
                (255, 255, 255), # 0: black -> white
                (128, 0, 0),     # 1: red
                (0, 128, 0),     # 2: green
                (128, 128, 0),   # 3: yellow
                (0, 0, 128),     # 4: blue
                (128, 0, 128),   # 5: magenta
                (0, 128, 128),   # 6: cyan
                (0, 0, 0),       # 7: white -> black
                (128, 128, 128), # 8: bright black
                (255, 0, 0),     # 9: bright red
                (0, 255, 0),     # 10: bright green
                (255, 255, 0),   # 11: bright yellow
                (0, 0, 255),     # 12: bright blue
                (255, 0, 255),   # 13: bright magenta
                (0, 255, 255),   # 14: bright cyan
                (0, 0, 0),       # 15: bright white -> black
            ],
            [
                (255, 255, 255),
                (255, 0, 0),
                (0, 255, 0),
                (255, 255, 0),
                (0, 0, 255),
                (255, 0, 255),
                (0, 255, 255),
                (0, 0, 0),
                (128, 128, 128),
                (255, 128, 128),
                (128, 255, 128),
                (255, 255, 128),
                (128, 128, 255),
                (255, 128, 255),
                (128, 255, 255),
                (0, 0, 0),
            ],
        )
    
    # Rich exports as HTML or SVG - HTML is better for emojis and colors
    # Try HTML first (better emoji/color support), then SVG, then fallback
    
    # Method 1: Try HTML + wkhtmltoimage (best for emojis and colors)
    temp_html = output_path.replace('.jpg', '.html').replace('.jpeg', '.html')
    try:
        html_content = console.export_html(title="", theme=theme, code_format="<pre>{code}</pre>")
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Try to use wkhtmltoimage if available (best quality)
        import subprocess
        import shutil
        
        wkhtml_path = shutil.which('wkhtmltoimage')
        if wkhtml_path:
            # Use wkhtmltoimage to convert HTML to JPG
            bg_color_arg = '--background' if bg_color.lower() == "white" else ''
            cmd = [
                wkhtml_path,
                '--width', str(width),
                '--format', 'jpg',
                '--quality', str(quality),
                bg_color_arg,
                temp_html,
                output_path
            ]
            # Remove empty string if bg_color_arg is empty
            cmd = [c for c in cmd if c]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(output_path):
                os.remove(temp_html)
                return True
    except Exception as e:
        # HTML method failed, try SVG
        pass
    
    # Method 2: Try SVG + cairosvg/svglib
    temp_svg = output_path.replace('.jpg', '.svg').replace('.jpeg', '.svg')
    try:
        svg_content = console.export_svg(title="", theme=theme)
        with open(temp_svg, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        # Try cairosvg first (better quality)
        try:
            import cairosvg
            temp_png = temp_svg.replace('.svg', '.png')
            cairosvg.svg2png(
                url=temp_svg,
                write_to=temp_png,
                output_width=width,
                background_color='white' if bg_color.lower() == "white" else 'black'
            )
            
            if PIL_AVAILABLE and os.path.exists(temp_png):
                img = Image.open(temp_png)
                rgb_img = img.convert('RGB')
                rgb_img.save(output_path, 'JPEG', quality=quality)
                os.remove(temp_png)
                os.remove(temp_svg)
                if os.path.exists(temp_html):
                    os.remove(temp_html)
                return True
        except ImportError:
            # cairosvg not available, try svglib
            try:
                from svglib.svglib import svg2rlg
                from reportlab.graphics import renderPM
                
                drawing = svg2rlg(temp_svg)
                if drawing:
                    temp_png = temp_svg.replace('.svg', '.png')
                    renderPM.drawToFile(drawing, temp_png, fmt='PNG', dpi=150)
                    
                    if PIL_AVAILABLE and os.path.exists(temp_png):
                        img = Image.open(temp_png)
                        # Resize to desired width if needed
                        if img.width != width:
                            ratio = width / img.width
                            new_height = int(img.height * ratio)
                            img = img.resize((width, new_height), Image.Resampling.LANCZOS)
                        
                        rgb_img = img.convert('RGB')
                        rgb_img.save(output_path, 'JPEG', quality=quality)
                        os.remove(temp_png)
                        os.remove(temp_svg)
                        if os.path.exists(temp_html):
                            os.remove(temp_html)
                        return True
            except ImportError:
                pass
        except Exception:
            # SVG conversion failed, continue to cleanup
            pass
    except Exception:
        # SVG method failed, continue to cleanup
        pass

    # Clean up temp files
    for temp_file in [temp_html, temp_svg]:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    # If all methods failed, raise exception
    raise Exception(
        "Could not convert to JPG. Options:\n"
        "1. Install wkhtmltoimage: sudo apt-get install wkhtmltopdf (best for emojis/colors)\n"
        "2. Install cairosvg: pip install cairosvg\n"
        "3. Install svglib: pip install svglib reportlab"
    )


def _pil_text_to_jpg(
    text: str,
    output_path: str,
    width: int,
    bg_color: str,
    quality: int
) -> bool:
    """Convert text to JPG using PIL (fallback method, strips ANSI codes but preserves emojis)."""
    # Strip ANSI codes but preserve Unicode characters (emojis, special chars)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_text = ansi_escape.sub('', text)
    
    # Ensure UTF-8 encoding is preserved
    if isinstance(clean_text, bytes):
        clean_text = clean_text.decode('utf-8', errors='replace')
    
    # Split into lines
    lines = clean_text.split('\n')
    
    # Calculate dimensions
    font_size = 16  # Slightly larger for better emoji rendering
    line_height = 24
    padding = 20
    
    # Try to load a font that supports emojis
    font = _get_emoji_font(font_size)
    
    # Calculate text dimensions (accounting for emojis which may be wider)
    max_line_width = 0
    for line in lines:
        try:
            # Estimate width: regular chars ~8px, emojis ~16-20px
            estimated_width = 0
            for char in line:
                # Check if character is likely an emoji or wide character
                if ord(char) > 0x1F000 or (0x1F300 <= ord(char) <= 0x1F9FF):
                    estimated_width += 20  # Emoji width
                elif ord(char) > 127:
                    estimated_width += 12  # Wide Unicode char
                else:
                    estimated_width += 8   # Regular ASCII
            
            max_line_width = max(max_line_width, estimated_width)
        except:
            # Fallback estimation
            max_line_width = max(max_line_width, len(line) * 10)
    
    # Calculate image dimensions
    img_width = min(width, max_line_width + (padding * 2))
    img_height = (len(lines) * line_height) + (padding * 2)
    
    # Create image
    bg_rgb = (0, 0, 0) if bg_color.lower() == "black" else (255, 255, 255)
    fg_rgb = (255, 255, 255) if bg_color.lower() == "black" else (0, 0, 0)
    
    img = Image.new('RGB', (img_width, img_height), color=bg_rgb)
    draw = ImageDraw.Draw(img)
    
    # Draw text (preserve Unicode including emojis)
    y = padding
    for line in lines:
        # Don't encode to ASCII - preserve UTF-8 for emojis
        try:
            draw.text((padding, y), line, fill=fg_rgb, font=font, encoding='utf-8')
        except Exception as e:
            # Try without encoding parameter (some PIL versions)
            try:
                draw.text((padding, y), line, fill=fg_rgb, font=font)
            except:
                # Last resort: try with default font
                try:
                    default_font = ImageFont.load_default()
                    draw.text((padding, y), line, fill=fg_rgb, font=default_font)
                except:
                    # Absolute fallback: draw what we can
                    draw.text((padding, y), line[:100], fill=fg_rgb)
        y += line_height
    
    # Save as JPG
    img.save(output_path, 'JPEG', quality=quality)
    return True


def _get_emoji_font(size: int):
    """Get a font that supports emojis and Unicode, trying common system fonts."""
    font_paths = [
        # Windows - fonts with emoji support
        "C:/Windows/Fonts/seguiemj.ttf",  # Segoe UI Emoji
        "C:/Windows/Fonts/segmdl2.ttf",   # Segoe MDL2 Assets (icons)
        "C:/Windows/Fonts/consola.ttf",    # Consolas (monospace)
        "C:/Windows/Fonts/cour.ttf",      # Courier New
        "C:/Windows/Fonts/arial.ttf",     # Arial (has some Unicode)
        # Linux - fonts with emoji support
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        # macOS - fonts with emoji support
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.dfont",
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
    
    # Try to use a default font that might support some Unicode
    try:
        return ImageFont.load_default()
    except:
        # Absolute fallback
        return None


def _get_monospace_font(size: int):
    """Get a monospace font, trying common system fonts."""
    return _get_emoji_font(size)  # Use same function, emoji font is preferred


def capture_command_output_to_jpg(
    command_func,
    output_path: str,
    *args,
    width: int = 1200,
    bg_color: str = "black",
    **kwargs
) -> bool:
    """
    Capture output from a command function and save as JPG.
    
    This is a convenience function that runs a command, captures its output,
    and saves it as a JPG image.
    
    Args:
        command_func: Function that prints output (should use print statements)
        output_path: Path to output JPG file
        *args: Positional arguments to pass to command_func
        width: Image width in pixels (default: 1200)
        bg_color: Background color - "black" or "white" (default: "black")
        **kwargs: Keyword arguments to pass to command_func
    
    Returns:
        True if successful, False otherwise
    
    Example:
        >>> from clickup_framework.utils.image_export import capture_command_output_to_jpg
        >>> def my_command():
        ...     print("Hello World")
        >>> capture_command_output_to_jpg(my_command, "output.jpg")
        True
    """
    import io
    from contextlib import redirect_stdout
    
    # Capture stdout
    f = io.StringIO()
    with redirect_stdout(f):
        try:
            command_func(*args, **kwargs)
        except SystemExit:
            # Commands may call sys.exit(), which is fine
            pass
    
    output = f.getvalue()
    return console_to_jpg(output, output_path, width, bg_color)

