# Puppeteer Version Information

## Latest Versions (as of November 2025)

### Puppeteer
- **Latest Version**: 24.30.0 (npm)
- **Recent Versions**: 24.24.1, 24.25.0, 24.26.0, 24.26.1, 24.27.0, 24.28.0, 24.29.0, 24.29.1, 24.30.0
- **Chrome Compatibility**: Puppeteer v24.x is compatible with Chrome 142.x

### Mermaid CLI
- **Current Installed Version**: 11.12.0
- **Latest Available Version**: 11.12.0
- **Puppeteer Dependency**: Uses an older version of puppeteer-core (likely 23.x or earlier)
  - This version expects Chrome 131.0.6778.204
  - But we have Chrome 142 installed

## Version Mismatch Issue

The problem is:
- **mermaid-cli 11.12.0** uses **puppeteer-core** (older version) that expects **Chrome 131**
- We installed **Chrome 142** (newer version)
- This causes the "Could not find Chrome (ver. 131.0.6778.204)" error

## Solutions

### Option 1: Install Chrome 131
```bash
npx puppeteer browsers install chrome@131.0.6778.204
```
(Already attempted, but mmdc still can't find it)

### Option 2: Update mermaid-cli
Check if there's a newer version that uses a newer Puppeteer:
```bash
npm install -g @mermaid-js/mermaid-cli@latest
```

### Option 3: Use SVG output
SVG might not require Chrome:
```bash
mmdc -i input.mmd -o output.svg
```

### Option 4: Configure Puppeteer cache
Set environment variable to point to the correct Chrome location:
```bash
$env:PUPPETEER_CACHE_DIR="C:\Users\craig\.cache\puppeteer"
```

## Current Status

- ✅ Puppeteer latest: 24.30.0
- ✅ Mermaid CLI: 11.12.0 (latest)
- ❌ Chrome version mismatch blocking image generation
- ✅ Mermaid parsing and placeholder generation working

