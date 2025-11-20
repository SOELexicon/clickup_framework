# Universal Ctags Setup & Configuration Guide

## Installation

### Prerequisites: libjansson (Required for JSON output)

**macOS (Homebrew):**
```bash
brew install libjansson
brew install universal-ctags
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install libjansson-dev
sudo apt-get install universal-ctags
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install jansson-devel
sudo dnf install universal-ctags
```

**Windows:**
Download pre-built binary from: https://github.com/universal-ctags/ctags-win32/releases

### Verify Installation

```bash
ctags --version
ctags --list-features | grep json
```

If `json` appears in the features list, JSON output is enabled.

---

## Basic Usage

### Generate Tags (Default Format)
```bash
ctags -R .
```

### Generate JSON Output (Recommended)
```bash
ctags --output-format=json -R . > tags.json
```

### Multi-Language with Filtering
```bash
ctags --output-format=json \
  --languages=Python,C#,JavaScript \
  --exclude=.git \
  --exclude=node_modules \
  --exclude=.venv \
  -R . > tags.json
```

---

## JSON Output Format

Each line is a complete JSON object (JSON Lines format):

```json
{
  "_type": "ptag",
  "name": "JSON_OUTPUT_VERSION",
  "path": "1.0",
  "pattern": "in development"
}
{
  "_type": "tag",
  "name": "MyFunction",
  "path": "src/module.py",
  "pattern": "/^def MyFunction(arg1, arg2):$/",
  "language": "Python",
  "kind": "function",
  "line": 42,
  "end": 50
}
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `_type` | string | "tag" or "ptag" (pseudo-tag) |
| `name` | string | Symbol name (function, variable, class, etc.) |
| `path` | string | File path |
| `line` | integer | Starting line number |
| `end` | integer | Ending line number |
| `kind` | string | Symbol kind (function, class, variable, member, etc.) |
| `scope` | string | Parent scope (class name for methods, etc.) |
| `scopeKind` | string | Kind of scope (class, namespace, etc.) |
| `language` | string | Programming language detected |
| `pattern` | string | Regex pattern for location |

---

## Common Options

### Fields Control
```bash
# Include end line numbers, exclude pattern
ctags --output-format=json --fields=-P +e -R .

# List available fields
ctags --output-format=json --list-fields
```

### Extras (Additional Information)
```bash
# Include pseudo-tags, extra data
ctags --output-format=json --extras=+p -R .

# List available extras
ctags --list-extras
```

### Language-Specific
```bash
# Python only
ctags --output-format=json --languages=Python -R src/

# C# and JavaScript
ctags --output-format=json --languages=C#,JavaScript -R .
```

### Exclude Patterns
```bash
ctags --output-format=json \
  --exclude=.git \
  --exclude=node_modules \
  --exclude=__pycache__ \
  --exclude=.venv \
  --exclude=.pytest_cache \
  --exclude=bin \
  --exclude=obj \
  -R .
```

---

## Interactive Mode (Programmatic)

For real-time, streaming analysis:

```bash
echo '{"command":"generate-tags", "filename":"test.py"}' | ctags --_interactive
```

Response:
```json
{"_type": "program", "name": "Universal Ctags", "version": "0.0.0"}
{"_type": "tag", "name": "foo", "path": "test.py", "pattern": "/^def foo():$/", "kind": "function"}
{"_type": "completed", "command": "generate-tags"}
```

---

## Recommended Configuration File (.ctags)

Create `.ctags` or `.ctags.d/default.ctags` in your project root:

```
# Output format
--output-format=json

# Standard excludes
--exclude=.git
--exclude=.gitignore
--exclude=.venv
--exclude=venv
--exclude=node_modules
--exclude=__pycache__
--exclude=.pytest_cache
--exclude=.mypy_cache
--exclude=bin
--exclude=obj
--exclude=.vs
--exclude=.vscode

# Include line numbers and extras
--fields=+l +e +S
--extras=+p

# All supported languages
--languages=all
```

Then run simply:
```bash
ctags -R .
```

---

## Language Support Matrix

Universal Ctags supports 100+ languages including:

- **Web:** JavaScript, TypeScript, HTML, CSS, JSON, XML
- **Backend:** Python, C#, Java, C++, C, PHP, Ruby, Go, Rust
- **Scripting:** PowerShell, Bash, Perl, Lua
- **Data:** YAML, Toml, Properties
- **Other:** Kotlin, Swift, Objective-C, Scala, Haskell, Clojure

Check full list:
```bash
ctags --list-languages
```

---

## Parsing Output Programmatically

### Python Example
```python
import json

with open('tags.json') as f:
    for line in f:
        tag = json.loads(line)
        if tag.get('_type') != 'tag':
            continue
        
        print(f"{tag['name']} ({tag['kind']}) @ {tag['path']}:{tag['line']}")
```

### PowerShell Example
```powershell
Get-Content tags.json | ForEach-Object {
    $tag = $_ | ConvertFrom-Json
    if ($tag._type -eq 'tag') {
        Write-Host "$($tag.name) ($($tag.kind)) @ $($tag.path):$($tag.line)"
    }
}
```

---

## Performance Tips

- Use `--languages=` to restrict to needed languages (faster)
- Use `--exclude=` for directories you don't need
- For large projects, consider splitting by directory
- JSON output is slightly slower than default format; use for automation only

---

## Troubleshooting

### "ctags: unknown output format name supplied for 'output-format=json'"

libjansson not linked. Rebuild with jansson support:

**macOS:**
```bash
brew uninstall universal-ctags
brew install --HEAD universal-ctags
```

**Linux (from source):**
```bash
git clone https://github.com/universal-ctags/ctags.git
cd ctags
./autogen.sh
./configure --enable-json
make
sudo make install
```

---

## References

- Official Docs: https://docs.ctags.io/
- GitHub: https://github.com/universal-ctags/ctags
- JSON Output Spec: https://docs.ctags.io/en/latest/man/ctags-json-output.5.html
