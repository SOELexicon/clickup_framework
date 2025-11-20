# ctags on Windows - Troubleshooting & Setup

## The Error You're Seeing

```
ctags.exe: Notice: ignoring null tag in ./.venv/Lib/site-packages/...
```

**What it means:** ctags found some malformed code in third-party libraries (minified/compiled JavaScript). These are harmless warnings.

**Solution:** Just exclude `.venv` directory (which you should anyway).

---

## Quick Fix

### Option 1: Use .ctags Config File (Recommended)

Copy the `.ctags` file to your project root:

```powershell
# Copy provided .ctags
Copy-Item .ctags .

# Now run ctags - it auto-reads .ctags
ctags --output-format=json -R .
```

The `--quiet` option in `.ctags` suppresses these notices.

### Option 2: Command-Line Argument

```bash
ctags --output-format=json --quiet \
  --exclude=.venv \
  --exclude=node_modules \
  -R . > tags.json
```

### Option 3: Use the Batch Script

```powershell
# Windows batch script handles everything
.\generate_codemap.bat
```

---

## Installation on Windows

### Step 1: Install ctags

**Option A: Chocolatey (Easiest)**
```powershell
choco install universal-ctags
```

**Option B: Direct Download**
1. Go to https://github.com/universal-ctags/ctags-win32/releases
2. Download latest `ctags-*-x64.zip` or `ctags-*-x86.zip`
3. Extract to `C:\Program Files\universal-ctags\` or similar
4. Add to PATH:
   ```powershell
   $env:PATH += ";C:\Program Files\universal-ctags"
   [Environment]::SetEnvironmentVariable("PATH", $env:PATH, "User")
   ```

### Step 2: Verify Installation

```powershell
# Check version
ctags --version
# Should show: Universal Ctags ...

# Verify JSON support
ctags --list-features | Select-String json
# Should show: json
```

If JSON support missing:
- You need ctags built with libjansson
- Download newer release from ctags-win32
- Or build from source with jansson support

### Step 3: Test It

```powershell
# Create test file
@'
def hello():
    print("world")

class MyClass:
    def method(self):
        pass
'@ | Out-File -Encoding UTF8 test.py

# Generate tags
ctags --output-format=json test.py > tags.json

# View output
Get-Content tags.json
```

---

## Common Issues on Windows

### Issue 1: "ctags not found"

```powershell
# Check if installed
where ctags
# If blank, ctags not in PATH

# Add to PATH temporarily
$env:PATH += ";C:\Program Files\universal-ctags"

# Or install via Chocolatey
choco install universal-ctags
```

### Issue 2: "unknown output format name supplied for 'output-format=json'"

libjansson not linked. Need newer build:

```powershell
# Uninstall old version
choco uninstall universal-ctags

# Install latest
choco install universal-ctags

# Or download directly
# https://github.com/universal-ctags/ctags-win32/releases
```

### Issue 3: "Permission denied" errors

Likely .git directory locked:

```powershell
# Try with git excluded
ctags --output-format=json --exclude=.git -R . > tags.json

# Or use the batch script (handles this)
.\generate_codemap.bat
```

### Issue 4: JSON file is huge or slow

Too many directories being scanned:

```powershell
# Check what's being indexed
ctags --output-format=json -R . | wc -l

# Exclude more directories
ctags --output-format=json \
  --exclude=.venv \
  --exclude=node_modules \
  --exclude=.git \
  --exclude=bin \
  --exclude=obj \
  -R . > tags.json

# Or limit to source directories only
ctags --output-format=json -R src/ tests/ > tags.json
```

### Issue 5: "Notice: ignoring null tag" warnings won't stop

Those notices come from minified JavaScript. They're harmless but annoying:

```powershell
# Option A: Use --quiet flag
ctags --output-format=json --quiet -R . > tags.json

# Option B: Redirect to file, suppress stderr
ctags --output-format=json -R . > tags.json 2> $null

# Option C: Use the .ctags config (has --quiet)
ctags --output-format=json -R . > tags.json
```

---

## Performance Tips for Windows

### Slow on First Run?

1. **Exclude .venv and node_modules:**
   ```powershell
   ctags --output-format=json \
     --exclude=.venv \
     --exclude=node_modules \
     -R . > tags.json
   ```

2. **Limit languages:**
   ```powershell
   ctags --output-format=json --languages=C#,Python -R . > tags.json
   ```

3. **Index only source code:**
   ```powershell
   ctags --output-format=json -R src/ > tags.json
   ```

### Use PowerShell Jobs for Large Scans

```powershell
# Run in background
$job = Start-Job -ScriptBlock {
    cd C:\your\project
    ctags --output-format=json -R . > tags.json
}

Wait-Job $job
Get-Content tags.json | Measure-Object -Line
```

---

## Integration with Your Workflow

### Windows PowerShell Automation

Create `scripts\Generate-CodeMap.ps1`:

```powershell
# Run ctags
ctags --output-format=json --quiet `
  --exclude=.venv `
  --exclude=node_modules `
  -R . > .tags.json

Write-Host "✅ Code map generated"

# Parse with PowerShell module
Import-Module .\CtagsMapper.psm1
$parser = New-CtagsParser '.tags.json'
$stats = Get-TagsStatistics -Parser $parser

$stats | ConvertTo-Json | Write-Host
```

Run it:
```powershell
.\scripts\Generate-CodeMap.ps1
```

### Git Hook (Windows)

Create `.git\hooks\post-merge` (no extension):

```bash
#!/bin/bash
# Auto-refresh code map after merge

echo "🔄 Updating code map..."

ctags --output-format=json --quiet \
  --exclude=.venv \
  --exclude=node_modules \
  -R . > .tags.json 2>/dev/null

echo "✅ Code map updated"
```

Or as PowerShell (`.git\hooks\post-merge.ps1`):

```powershell
Write-Host "🔄 Updating code map..."

ctags --output-format=json --quiet `
  --exclude=.venv `
  --exclude=node_modules `
  -R . > .tags.json

Write-Host "✅ Code map updated"
```

### ClickUp Integration

See `CTAGS_INTEGRATION_EXAMPLE.md` for syncing with ClickUp tasks.

---

## Using the Batch Script

Easy Windows automation:

```powershell
# Generate full code map
.\generate_codemap.bat

# Python only
.\generate_codemap.bat --python

# C# only
.\generate_codemap.bat --csharp

# Show statistics
.\generate_codemap.bat --stats

# Help
.\generate_codemap.bat --help
```

Outputs:
- `.tags.json` - All tags
- `docs\codemap\statistics.json` - Metrics
- `docs\codemap\README.md` - Summary

---

## Configuration File Location

Put `.ctags` in any of these locations:

1. **Project root** (recommended):
   ```
   C:\Users\You\project\.ctags
   ```

2. **Home directory**:
   ```
   C:\Users\You\.ctags
   ```

3. **AppData directory**:
   ```
   C:\Users\You\AppData\Local\ctags\.ctags
   ```

Then just run:
```powershell
ctags --output-format=json -R .
```

It auto-loads the config.

---

## Verify It Works

Quick test:

```powershell
# 1. Create test Python file
'
class User:
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f"Hello, {self.name}"
' | Out-File test.py

# 2. Generate tags
ctags --output-format=json test.py > tags.json

# 3. Check output
Get-Content tags.json

# Should show User class and methods with line numbers
```

Expected output:
```json
{"_type": "tag", "name": "User", "kind": "class", "line": 1, ...}
{"_type": "tag", "name": "__init__", "kind": "method", "scope": "User", "line": 2, ...}
{"_type": "tag", "name": "greet", "kind": "method", "scope": "User", "line": 5, ...}
```

---

## Next Steps

1. **Copy `.ctags` to your project root**
2. **Run the batch script: `.\generate_codemap.bat`**
3. **Use PowerShell module to analyze: `Show-SymbolTree`**
4. **Integrate with your workflow**

See other documentation files for:
- CTAGS_QUICK_REFERENCE.md - Command examples
- CTAGS_INTEGRATION_EXAMPLE.md - ClickUp/CI-CD setup
- ctags_parser.py - Python analysis tool

---

## Resources

- Official: https://docs.ctags.io/
- Windows Builds: https://github.com/universal-ctags/ctags-win32/releases
- Issues: https://github.com/universal-ctags/ctags/issues
