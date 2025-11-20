# ctags Quick Reference

## Installation One-Liner

```bash
# macOS
brew install libjansson universal-ctags

# Ubuntu/Debian
sudo apt-get install libjansson-dev universal-ctags

# Fedora/RHEL
sudo dnf install jansson-devel universal-ctags
```

---

## Generate Tags

### Basic (All Languages)
```bash
ctags --output-format=json -R . > tags.json
```

### Specific Languages
```bash
# Python only
ctags --output-format=json --languages=Python -R . > py_tags.json

# C# and JavaScript
ctags --output-format=json --languages=C#,JavaScript -R . > dotnet_tags.json

# Exclude directories
ctags --output-format=json \
  --exclude=.git \
  --exclude=node_modules \
  --exclude=__pycache__ \
  -R . > tags.json
```

### With Line Numbers and Metadata
```bash
ctags --output-format=json \
  --fields=+e +l +S \
  --extras=+p \
  -R . > tags.json
```

---

## Python Usage

### Setup
```bash
# Make executable
chmod +x ctags_parser.py

# Basic usage
python3 ctags_parser.py tags.json

# Show file symbols
python3 ctags_parser.py tags.json show src/module.py

# Filter by language
python3 ctags_parser.py tags.json filter Python

# Filter by language and kind
python3 ctags_parser.py tags.json filter C# class

# Statistics
python3 ctags_parser.py tags.json stats

# Export markdown
python3 ctags_parser.py tags.json markdown src/module.py
```

### Programmatic
```python
from ctags_parser import CtagsParser

parser = CtagsParser('tags.json')

# Show file structure
print(parser.format_symbols('src/services/user_service.py'))

# Get all Python functions
funcs = parser.filter_tags(language='Python', kind='function')
for func in funcs:
    print(f"{func.name} @ {func.path}:{func.line}")

# Find scope at line number
code_map = parser.build_code_map('src/module.py')
scope = parser.get_line_range('src/module.py', 42)
print(f"Line 42 is in: {scope.name}")

# Statistics
stats = parser.statistics()
print(f"Total symbols: {stats['total_tags']}")
```

---

## PowerShell Usage

### Setup
```powershell
# Import module
Import-Module .\CtagsMapper.psm1

# Create parser
$parser = New-CtagsParser 'tags.json'

# Show file symbols
Show-SymbolTree -Parser $parser -FilePath 'src/Services/UserService.cs'

# Get statistics
$stats = Get-TagsStatistics -Parser $parser
$stats | ConvertTo-Json

# Filter tags
$csharpClasses = Filter-Tags -Parser $parser -Language 'C#' -Kind 'class'
$csharpClasses | Format-Table -Property Name, Path, Line, End

# Export markdown
Export-CodeMap -Parser $parser -FilePath 'src/module.py' -OutputFile 'module.md'
```

---

## CI/CD Integration

### GitHub Actions
```yaml
name: Generate Code Map
on: [push]

jobs:
  codemap:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install ctags
        run: sudo apt-get install -y universal-ctags
      
      - name: Generate tags
        run: |
          ctags --output-format=json \
            --languages=Python,C#,JavaScript \
            --exclude=.git \
            -R . > tags.json
      
      - name: Parse and document
        run: |
          pip install -r requirements.txt
          python3 ctags_parser.py tags.json stats > code_stats.txt
          python3 ctags_parser.py tags.json markdown src/main.py > CODE_MAP.md
      
      - uses: actions/upload-artifact@v2
        with:
          name: code-documentation
          path: |
            tags.json
            code_stats.txt
            CODE_MAP.md
```

### Local Git Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Generating code map..."
ctags --output-format=json \
  --exclude=.git \
  --exclude=node_modules \
  -R . > .tags.json 2>/dev/null

python3 ctags_parser.py .tags.json stats > .code_stats.txt

exit 0
```

---

## ClickUp Integration

### Document Automation
```python
import subprocess
import json
from clickup_api import ClickUp

# Generate code map
subprocess.run([
    'ctags', '--output-format=json',
    '--languages=C#,Python',
    '-R', '.', '>', 'tags.json'
], shell=True)

# Parse and upload
parser = CtagsParser('tags.json')
stats = parser.statistics()

# Create ClickUp task with documentation
clickup = ClickUp(token='your_token')
task = clickup.create_task(
    list_id='123',
    name=f"Code Map Generated - {stats['total_tags']} symbols",
    description=f"""
# Code Structure

Total Symbols: {stats['total_tags']}
Files Analyzed: {stats['files']}

## By Language
{json.dumps(stats['by_language'], indent=2)}

## By Kind
{json.dumps(stats['by_kind'], indent=2)}
    """
)
```

---

## Common Patterns

### Find All Classes in Project
```bash
# Bash
ctags --output-format=json -R . | \
  jq -r 'select(.kind=="class") | "\(.path):\(.line) \(.name)"'

# PowerShell
$parser = New-CtagsParser 'tags.json'
Filter-Tags -Parser $parser -Kind 'class' | 
  Select-Object Name, Path, Line, Language
```

### Generate Module Documentation
```bash
for file in $(find src -name "*.py" -type f); do
  echo "## $file"
  python3 ctags_parser.py tags.json markdown "$file"
  echo ""
done > DOCUMENTATION.md
```

### Map Variable Usage
```python
# Find which function uses variable
parser = CtagsParser('tags.json')
vars = parser.filter_tags(kind='variable')

for var in vars:
    # Find parent function
    scope_tag = parser.get_line_range(var.path, var.line)
    print(f"{var.name} used in {scope_tag.name if scope_tag else 'module'}")
```

### Cross-Language Analysis
```bash
# Count functions by language
ctags --output-format=json -R . | \
  jq -r 'select(.kind=="function") | .language' | \
  sort | uniq -c | sort -rn
```

---

## JSON Output Fields

| Field | Type | Example |
|-------|------|---------|
| `name` | string | `UserService` |
| `path` | string | `src/services/user.py` |
| `kind` | string | `class`, `function`, `variable` |
| `language` | string | `Python`, `C#` |
| `line` | integer | `42` |
| `end` | integer | `87` |
| `scope` | string | `UserService` (parent) |
| `scopeKind` | string | `class` |
| `pattern` | string | `/^class UserService:$/` |

---

## Performance Tips

- **Exclude build dirs**: `--exclude=node_modules --exclude=bin --exclude=obj`
- **Limit languages**: `--languages=Python,C#` (faster than analyzing all)
- **Large projects**: Run on subdirectories separately
- **Default format faster**: Use JSON only for automation

---

## Troubleshooting

### JSON support missing
```bash
# Verify
ctags --list-features | grep json

# If missing, rebuild with jansson
git clone https://github.com/universal-ctags/ctags.git
cd ctags
./autogen.sh
./configure --enable-json
make && sudo make install
```

### Wrong line numbers
- Ensure `--fields=+e` for `end` field
- Line numbers are 1-indexed
- Async functions may have different ranges

### Performance slow
- Use `--languages=` to limit
- Exclude large directories
- Run on specific path: `ctags ... src/` not whole repo

---

## Resources

- Official: https://docs.ctags.io/
- JSON Spec: https://docs.ctags.io/en/latest/man/ctags-json-output.5.html
- GitHub: https://github.com/universal-ctags/ctags
