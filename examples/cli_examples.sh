#!/bin/bash
# ClickUp Framework CLI Examples
#
# This script demonstrates various CLI usage patterns.
# Most commands require a ClickUp API key (CLICKUP_API_TOKEN env var)
# but demo mode works without it.

set -e

echo "=================================="
echo "ClickUp Framework CLI Examples"
echo "=================================="
echo

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_example() {
    echo -e "${BLUE}Example: $1${NC}"
    echo -e "${GREEN}$ $2${NC}"
    echo
}

# 1. Help and Documentation
print_example "View all available commands" "./clickup --help"
./clickup --help
echo
echo "---"
echo

# 2. Demo Mode (No API Key Required)
print_example "Hierarchy view demo" "./clickup demo --mode hierarchy"
./clickup demo --mode hierarchy
echo
echo "---"
echo

print_example "Detail view demo with detailed preset" "./clickup demo --mode detail --preset detailed"
./clickup demo --mode detail --preset detailed
echo
echo "---"
echo

print_example "Container view demo" "./clickup demo --mode container"
./clickup demo --mode container
echo
echo "---"
echo

print_example "Statistics demo" "./clickup demo --mode stats"
./clickup demo --mode stats
echo
echo "---"
echo

# 3. Format Presets
print_example "Minimal format (IDs and names only)" "./clickup demo --mode flat --preset minimal"
./clickup demo --mode flat --preset minimal
echo
echo "---"
echo

print_example "Summary format (standard view)" "./clickup demo --mode hierarchy --preset summary"
./clickup demo --mode hierarchy --preset summary
echo
echo "---"
echo

print_example "Detailed format (with descriptions)" "./clickup demo --mode hierarchy --preset detailed"
./clickup demo --mode hierarchy --preset detailed
echo
echo "---"
echo

# 4. Customization Options
print_example "Show IDs and disable colors" "./clickup demo --mode flat --show-ids --no-colorize"
./clickup demo --mode flat --show-ids --no-colorize
echo
echo "---"
echo

print_example "Hide emojis" "./clickup demo --mode hierarchy --no-emoji"
./clickup demo --mode hierarchy --no-emoji
echo
echo "---"
echo

# 5. Real API Usage Examples (commented out - require actual list/task IDs)
cat <<'EOF'

To use with real ClickUp data (requires CLICKUP_API_TOKEN):

# View hierarchy of tasks in a list
./clickup hierarchy <list_id>

# View with custom formatting
./clickup hierarchy <list_id> --show-ids --show-descriptions --preset detailed

# Container view (workspace → space → folder → list)
./clickup container <list_id>

# Filter tasks
./clickup filter <list_id> --status "in progress"
./clickup filter <list_id> --priority 1
./clickup filter <list_id> --tags backend api
./clickup filter <list_id> --status "to do" --view-mode container

# View task details with relationship tree
./clickup detail <task_id> <list_id>

# Statistics
./clickup stats <list_id>

# Multiple options combined
./clickup hierarchy <list_id> \
  --preset detailed \
  --show-ids \
  --show-descriptions \
  --show-dates \
  --show-comments 2 \
  --include-completed

# Different view modes for filtered tasks
./clickup filter <list_id> --status "in progress" --view-mode hierarchy
./clickup filter <list_id> --priority 1 --view-mode container
./clickup filter <list_id> --tags critical --view-mode flat

EOF

echo
echo "=================================="
echo "Examples completed!"
echo "=================================="
echo
echo "For more information:"
echo "  ./clickup <command> --help"
echo "  python -m clickup_framework --help"
