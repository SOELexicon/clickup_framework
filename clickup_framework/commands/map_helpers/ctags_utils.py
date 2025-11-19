"""Ctags installation, generation, and parsing utilities."""

import sys
import json
import re
import subprocess
import zipfile
import urllib.request
import shutil
from pathlib import Path
from collections import defaultdict
from typing import Optional, Dict, Union
from clickup_framework.utils.colors import colorize, TextColor

# Constants for ctags installation
CTAGS_DOWNLOAD_URL = "https://github.com/universal-ctags/ctags-win32/releases/download/p6.2.20251116.0/ctags-p6.2.20251116.0-x64.zip"
CTAGS_LOCAL_DIR = Path.home() / ".clickup_framework" / "bin"
CTAGS_EXE = CTAGS_LOCAL_DIR / "ctags.exe"


def get_ctags_executable() -> Optional[str]:
    """
    Get the ctags executable path.

    Checks in order:
    1. Local installation in ~/.clickup_framework/bin/ctags.exe
    2. System PATH

    Returns:
        Path to ctags executable or None if not found
    """
    # Check local installation first
    if CTAGS_EXE.exists():
        return str(CTAGS_EXE)

    # Check system PATH
    try:
        result = subprocess.run(
            ['ctags', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return 'ctags'
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass

    return None


def check_ctags_available() -> bool:
    """Check if ctags is available."""
    return get_ctags_executable() is not None


def install_ctags_locally(use_color: bool = False) -> bool:
    """
    Download and install ctags locally to ~/.clickup_framework/bin/

    Args:
        use_color: Whether to use colored output

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create local bin directory
        CTAGS_LOCAL_DIR.mkdir(parents=True, exist_ok=True)

        # Download the zip file
        zip_path = CTAGS_LOCAL_DIR / "ctags.zip"

        if use_color:
            print(colorize(f"[PROGRESS] Downloading ctags from {CTAGS_DOWNLOAD_URL}...", TextColor.BRIGHT_BLUE))
        else:
            print(f"[PROGRESS] Downloading ctags from {CTAGS_DOWNLOAD_URL}...")

        # Download with progress
        def reporthook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(block_num * block_size * 100 / total_size, 100)
                print(f"\r  Progress: {percent:.1f}%", end='', flush=True)

        urllib.request.urlretrieve(CTAGS_DOWNLOAD_URL, zip_path, reporthook)
        print()  # New line after progress

        # Extract the zip file
        if use_color:
            print(colorize("[PROGRESS] Extracting ctags...", TextColor.BRIGHT_BLUE))
        else:
            print("[PROGRESS] Extracting ctags...")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract only ctags.exe
            for member in zip_ref.namelist():
                if member.endswith('ctags.exe'):
                    # Extract to bin directory
                    source = zip_ref.open(member)
                    target = CTAGS_EXE
                    with target.open('wb') as f:
                        shutil.copyfileobj(source, f)
                    break

        # Clean up zip file
        zip_path.unlink()

        # Verify installation
        if CTAGS_EXE.exists():
            if use_color:
                print(colorize(f"[SUCCESS] ctags installed to {CTAGS_EXE}", TextColor.GREEN))
            else:
                print(f"[SUCCESS] ctags installed to {CTAGS_EXE}")
            return True
        else:
            if use_color:
                print(colorize("[ERROR] Failed to extract ctags.exe", TextColor.RED), file=sys.stderr)
            else:
                print("[ERROR] Failed to extract ctags.exe", file=sys.stderr)
            return False

    except Exception as e:
        if use_color:
            print(colorize(f"[ERROR] Failed to install ctags: {e}", TextColor.RED), file=sys.stderr)
        else:
            print(f"[ERROR] Failed to install ctags: {e}", file=sys.stderr)
        return False


def generate_ctags(language: Optional[str] = None, output_file: str = '.tags.json', ctags_exe: Optional[str] = None, ignore_gitignore: bool = False, in_memory: bool = True) -> Union[bool, str]:
    """
    Generate ctags JSON output.

    Args:
        language: Language filter ('python', 'csharp', 'all', or None for all)
        output_file: Output file path (only used if in_memory=False)
        ctags_exe: Path to ctags executable (if None, will use system ctags)
        ignore_gitignore: If True, scan bin/obj and other typically ignored directories
        in_memory: If True, return JSON string; if False, write to file and return success bool

    Returns:
        If in_memory=True: JSON string on success, None on failure
        If in_memory=False: True if successful, False otherwise
    """
    if ctags_exe is None:
        ctags_exe = 'ctags'

    cmd = [
        ctags_exe,
        '--output-format=json',
        '--fields=+ne',  # n=line number, e=end line
        '--quiet',
        '--exclude=.venv',
        '--exclude=venv',
        '--exclude=env',
        '--exclude=.env',
        '--exclude=node_modules',
        '--exclude=.git',
        '--exclude=__pycache__',
        '--exclude=*.pyc',
        '--exclude=.pytest_cache',
        '--exclude=.tox',
        '--exclude=dist',
        '--exclude=build',
        '--exclude=*.egg-info',
        '--exclude=.coverage',
        '--exclude=htmlcov',
        '--langmap=C#:+.razor',  # Add Razor component support
        '--langmap=C#:+.razor.cs',  # Add Razor code-behind support
        '--langmap=C#:+.cshtml',  # Add Razor view support (traditional Razor Pages)
        '-R',
        '.'
    ]

    # Process .gitignore file
    gitignore_path = Path('.gitignore')
    if ignore_gitignore and gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Remove leading slash if present
                        pattern = line.lstrip('/')
                        # Add as exception to override gitignore
                        cmd.insert(-2, f'--exclude-exception={pattern}')
        except Exception as e:
            print(f"Warning: Could not process .gitignore: {e}", file=sys.stderr)
    elif not ignore_gitignore:
        # Normal behavior: exclude build directories (including nested subdirectories)
        cmd.insert(-2, '--exclude=**/bin/**')
        cmd.insert(-2, '--exclude=**/obj/**')

    # Add language filter if specified
    if language == 'python':
        cmd.extend(['--languages=Python'])
    elif language == 'csharp':
        cmd.extend(['--languages=C#'])
    # 'all' or None means no language filter

    try:
        if in_memory:
            # Run ctags and capture output in memory
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid UTF-8 with placeholder
                timeout=300  # 5 minutes for large projects
            )

            if result.returncode == 0:
                return result.stdout  # Return JSON string
            else:
                print(f"Error generating ctags: {result.stderr}", file=sys.stderr)
                return None
        else:
            # Original file-based approach
            with open(output_file, 'w', encoding='utf-8') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=60
                )

            return result.returncode == 0
    except Exception as e:
        print(f"Error generating ctags: {e}", file=sys.stderr)
        return None if in_memory else False


def parse_tags_file(tags_file: Union[Path, str], from_string: bool = False) -> Dict:
    """
    Parse ctags JSON output and collect statistics plus call graph data.

    Args:
        tags_file: Path to tags JSON file, or JSON string if from_string=True
        from_string: If True, tags_file is a JSON string; if False, it's a file path

    Returns:
        Dictionary with statistics and symbol data
    """
    stats = defaultdict(lambda: defaultdict(int))
    symbols_by_file = defaultdict(list)
    all_symbols = {}  # name -> symbol data
    function_calls = defaultdict(set)  # function -> set of functions it might call
    total = 0
    files = set()

    try:
        # Get iterator for lines (either from file or string)
        if from_string:
            lines = tags_file.splitlines() if isinstance(tags_file, str) else []
        else:
            with open(tags_file, encoding='utf-8') as f:
                lines = f.readlines()

        for line in lines:
            try:
                data = json.loads(line.strip())
                if data.get('_type') != 'tag':
                    continue

                lang = data.get('language', 'Unknown')
                kind = data.get('kind', 'other')
                path = data.get('path', '')
                name = data.get('name', '')
                line_num = data.get('line', 0)
                scope = data.get('scope', '')
                scope_kind = data.get('scopeKind', '')

                stats[lang][kind] += 1
                total += 1
                files.add(path)

                symbol_data = {
                    'name': name,
                    'kind': kind,
                    'language': lang,
                    'line': line_num,
                    'end': data.get('end', line_num),  # Capture end line from ctags
                    'scope': scope,
                    'scopeKind': scope_kind,
                    'path': path,
                    'pattern': data.get('pattern', '')
                }

                # Store symbol info for diagram generation
                symbols_by_file[path].append(symbol_data)

                # Index all functions/methods for call graph
                if kind in ['function', 'method']:
                    full_name = f"{scope}.{name}" if scope else name
                    all_symbols[full_name] = symbol_data
                    all_symbols[name] = symbol_data  # Also index by short name

            except json.JSONDecodeError:
                continue
            except Exception:
                continue

        # Now parse file contents to find function calls using improved pattern matching
        for file_path in files:
            try:
                full_path = Path(file_path)
                if not full_path.exists():
                    continue

                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Remove strings and comments to reduce false positives
                # Remove single-line comments (# in Python, // in C#)
                content_clean = re.sub(r'#.*?$', '', content, flags=re.MULTILINE)
                content_clean = re.sub(r'//.*?$', '', content_clean, flags=re.MULTILINE)
                # Remove multi-line comments (/* */ in C#)
                content_clean = re.sub(r'/\*.*?\*/', '', content_clean, flags=re.DOTALL)
                # Remove string literals (basic approach - may not catch all edge cases)
                content_clean = re.sub(r'"(?:[^"\\]|\\.)*"', '', content_clean)
                content_clean = re.sub(r"'(?:[^'\\]|\\.)*'", '', content_clean)

                # Find functions defined in this file
                file_functions = [s for s in symbols_by_file[file_path]
                                if s['kind'] in ['function', 'method']]

                for func in file_functions:
                    func_name = func['name']
                    full_func_name = f"{func['scope']}.{func_name}" if func['scope'] else func_name

                    # Look for function calls using regex with word boundaries
                    for other_func_name in all_symbols.keys():
                        if other_func_name == func_name or other_func_name == full_func_name:
                            continue

                        short_name = other_func_name.split('.')[-1]

                        # Skip very short names to avoid false positives
                        if len(short_name) < 3:
                            continue

                        # Use regex with word boundaries for accurate matching
                        # Pattern: word boundary, function name, optional whitespace, opening paren
                        pattern = r'\b' + re.escape(short_name) + r'\s*\('

                        if re.search(pattern, content_clean):
                            function_calls[full_func_name].add(other_func_name)

            except Exception:
                continue

        return {
            'total_symbols': total,
            'files_analyzed': len(files),
            'by_language': dict(stats),
            'symbols_by_file': dict(symbols_by_file),
            'files': sorted(files),
            'all_symbols': all_symbols,
            'function_calls': {k: list(v) for k, v in function_calls.items()}
        }
    except Exception as e:
        print(f"Error parsing tags file: {e}", file=sys.stderr)
        return {}
