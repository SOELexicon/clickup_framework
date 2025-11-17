"""
Mermaid CLI Wrapper

Provides interface to Mermaid CLI (mmdc) for generating images from mermaid diagrams.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple


class MermaidCLI:
    """
    Wrapper for Mermaid CLI (mmdc) operations.

    Handles detection, validation, and image generation from mermaid code.
    """

    def __init__(self, cli_path: Optional[str] = None):
        """
        Initialize Mermaid CLI wrapper.

        Args:
            cli_path: Path to mmdc executable (None = auto-detect)
        """
        self.cli_path = cli_path or self._detect_cli()

    def _detect_cli(self) -> Optional[str]:
        """
        Detect mermaid CLI installation.

        Returns:
            Path to mmdc or None if not found
        """
        # Check environment variable first
        env_path = os.environ.get('MERMAID_CLI_PATH') or os.environ.get('MMDC_PATH')
        if env_path and os.path.exists(env_path):
            return env_path

        # Try to find mmdc in PATH
        mmdc_path = shutil.which('mmdc')
        if mmdc_path:
            return mmdc_path

        # Try common installation locations
        common_paths = [
            '/usr/local/bin/mmdc',
            '/usr/bin/mmdc',
            os.path.expanduser('~/.npm-global/bin/mmdc'),
            os.path.expanduser('~/node_modules/.bin/mmdc'),
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None

    def is_available(self) -> bool:
        """
        Check if mermaid CLI is available.

        Returns:
            True if mmdc is available
        """
        if not self.cli_path:
            return False

        try:
            result = subprocess.run(
                [self.cli_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            return False

    def get_version(self) -> Optional[str]:
        """
        Get mermaid CLI version.

        Returns:
            Version string or None if not available
        """
        if not self.cli_path:
            return None

        try:
            result = subprocess.run(
                [self.cli_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def generate_image(
        self,
        mermaid_code: str,
        output_path: str,
        image_format: str = 'png',
        background_color: str = 'white',
        width: Optional[int] = None,
        height: Optional[int] = None,
        theme: Optional[str] = None,
        timeout: int = 30
    ) -> Tuple[bool, str]:
        """
        Generate image from mermaid code.

        Args:
            mermaid_code: Mermaid diagram code
            output_path: Path where image should be saved
            image_format: Output format ('png' or 'svg')
            background_color: Background color (default: 'white')
            width: Image width in pixels (optional)
            height: Image height in pixels (optional)
            theme: Mermaid theme ('default', 'dark', 'forest', 'neutral') (optional)
            timeout: Command timeout in seconds

        Returns:
            Tuple of (success, error_message)
        """
        if not self.cli_path:
            return False, "Mermaid CLI (mmdc) not found. Install with: npm install -g @mermaid-js/mermaid-cli"

        if not self.is_available():
            return False, f"Mermaid CLI not available at: {self.cli_path}"

        # Create temporary input file
        temp_input = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.mmd',
            delete=False,
            encoding='utf-8'
        )

        try:
            # Write mermaid code to temp file
            temp_input.write(mermaid_code)
            temp_input.close()

            # Build command
            cmd = [
                self.cli_path,
                '-i', temp_input.name,
                '-o', output_path,
            ]

            # Add optional parameters
            if background_color:
                cmd.extend(['-b', background_color])

            if width:
                cmd.extend(['-w', str(width)])

            if height:
                cmd.extend(['-H', str(height)])

            if theme:
                cmd.extend(['-t', theme])

            # Execute mmdc
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                # Verify output file exists
                if os.path.exists(output_path):
                    return True, ""
                else:
                    return False, "Image file was not created"
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return False, f"Mermaid CLI error: {error_msg.strip()}"

        except subprocess.TimeoutExpired:
            return False, f"Mermaid CLI timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Error generating image: {str(e)}"
        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_input.name)
            except:
                pass


# Module-level singleton for convenience
_default_cli = None


def get_mermaid_cli() -> MermaidCLI:
    """
    Get default MermaidCLI instance.

    Returns:
        Singleton MermaidCLI instance
    """
    global _default_cli
    if _default_cli is None:
        _default_cli = MermaidCLI()
    return _default_cli


def is_mermaid_available() -> bool:
    """
    Check if mermaid CLI is available.

    Returns:
        True if mmdc is available
    """
    return get_mermaid_cli().is_available()


def generate_mermaid_image(
    mermaid_code: str,
    output_path: str,
    **options
) -> Tuple[bool, str]:
    """
    Convenience function to generate mermaid image.

    Args:
        mermaid_code: Mermaid diagram code
        output_path: Output file path
        **options: Additional options (image_format, background_color, etc.)

    Returns:
        Tuple of (success, error_message)
    """
    return get_mermaid_cli().generate_image(mermaid_code, output_path, **options)
