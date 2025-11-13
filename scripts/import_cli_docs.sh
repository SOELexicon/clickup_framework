#!/bin/bash
#
# import_cli_docs.sh
# Import CLI command reference documentation to ClickUp Docs
#
# Usage:
#   ./scripts/import_cli_docs.sh [workspace_id]
#
# If workspace_id is not provided, uses current context or CLICKUP_DEFAULT_WORKSPACE

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCS_DIR="$PROJECT_ROOT/docs/cli"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Import CLI Command Reference Documentation to ClickUp Docs

Usage:
    $(basename "$0") [OPTIONS] [WORKSPACE_ID]

Arguments:
    WORKSPACE_ID    ClickUp workspace ID (optional)
                    If not provided, uses current context or CLICKUP_DEFAULT_WORKSPACE

Options:
    -h, --help      Show this help message
    -d, --doc-name  Custom doc name (default: "CLI Command Reference")
    -n, --nested    Use nested directory structure
    -c, --check     Check prerequisites without importing

Environment Variables:
    CLICKUP_API_TOKEN           API token for ClickUp (required)
    CLICKUP_DEFAULT_WORKSPACE   Default workspace ID

Examples:
    # Import using current context
    $(basename "$0")

    # Import to specific workspace
    $(basename "$0") 90151898946

    # Import with custom doc name
    $(basename "$0") --doc-name "CLI Reference v2.0"

    # Check prerequisites only
    $(basename "$0") --check

EOF
}

# Parse command line arguments
DOC_NAME="CLI Command Reference"
NESTED=false
CHECK_ONLY=false
WORKSPACE_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -d|--doc-name)
            DOC_NAME="$2"
            shift 2
            ;;
        -n|--nested)
            NESTED=true
            shift
            ;;
        -c|--check)
            CHECK_ONLY=true
            shift
            ;;
        -*)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            WORKSPACE_ID="$1"
            shift
            ;;
    esac
done

# Check prerequisites
print_info "Checking prerequisites..."

# Check if cum command is available
if ! command -v cum &> /dev/null; then
    print_error "cum command not found. Please install the ClickUp Framework first."
    print_info "Run: pip install -e ."
    exit 1
fi
print_success "cum command found"

# Check API token
if [ -z "$CLICKUP_API_TOKEN" ]; then
    print_error "CLICKUP_API_TOKEN environment variable not set"
    print_info "Set it with: export CLICKUP_API_TOKEN='your_token'"
    print_info "Or use: cum set token 'your_token'"
    exit 1
fi
print_success "API token found"

# Check docs directory
if [ ! -d "$DOCS_DIR" ]; then
    print_error "Documentation directory not found: $DOCS_DIR"
    exit 1
fi
print_success "Documentation directory found: $DOCS_DIR"

# Count markdown files
MD_COUNT=$(find "$DOCS_DIR" -maxdepth 1 -name "*.md" | wc -l)
print_info "Found $MD_COUNT markdown file(s) to import"

# Get workspace ID
if [ -z "$WORKSPACE_ID" ]; then
    if [ -n "$CLICKUP_DEFAULT_WORKSPACE" ]; then
        WORKSPACE_ID="$CLICKUP_DEFAULT_WORKSPACE"
        print_info "Using default workspace: $WORKSPACE_ID"
    else
        # Try to get from current context
        WORKSPACE_ID=$(cum show 2>/dev/null | grep -oP 'Workspace:\s*\K\w+' || echo "")
        if [ -z "$WORKSPACE_ID" ]; then
            print_error "No workspace ID provided or found in context"
            print_info "Usage: $(basename "$0") <workspace_id>"
            print_info "Or set: cum set workspace <workspace_id>"
            exit 1
        fi
        print_info "Using workspace from context: $WORKSPACE_ID"
    fi
fi

# If check only, exit here
if [ "$CHECK_ONLY" = true ]; then
    print_success "All prerequisites met!"
    print_info "Workspace ID: $WORKSPACE_ID"
    print_info "Doc name: $DOC_NAME"
    print_info "Files to import: $MD_COUNT"
    print_info "Ready to import. Run without --check flag."
    exit 0
fi

# Set workspace context
print_info "Setting workspace context..."
cum set workspace "$WORKSPACE_ID" > /dev/null 2>&1
print_success "Workspace context set"

# Build import command
IMPORT_CMD="cum doc_import current \"$DOCS_DIR\" --doc-name \"$DOC_NAME\""
if [ "$NESTED" = true ]; then
    IMPORT_CMD="$IMPORT_CMD --nested"
fi

# Show what we're about to do
echo ""
print_info "Import Configuration:"
echo "  Workspace ID: $WORKSPACE_ID"
echo "  Doc Name:     $DOC_NAME"
echo "  Source Dir:   $DOCS_DIR"
echo "  Files:        $MD_COUNT markdown files"
echo "  Nested:       $NESTED"
echo ""

# Confirm import
read -p "Proceed with import? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Import cancelled"
    exit 0
fi

# Perform import
print_info "Importing documentation to ClickUp..."
echo ""

if output=$(eval "$IMPORT_CMD" 2>&1); then
    echo "$output"
    echo ""

    # Extract doc ID from output
    DOC_ID=$(echo "$output" | grep -oP 'Doc ID:\s*\K[a-z0-9-]+' || echo "")

    if [ -n "$DOC_ID" ]; then
        print_success "Documentation imported successfully!"
        echo ""
        print_info "Doc Details:"
        echo "  Name:    $DOC_NAME"
        echo "  Doc ID:  $DOC_ID"
        echo ""
        print_info "View in ClickUp or use:"
        echo "  cum doc_get current $DOC_ID"
        echo "  cum page_list current $DOC_ID"
        echo ""

        # Save doc ID to file for reference
        DOC_ID_FILE="$PROJECT_ROOT/.last_imported_doc_id"
        echo "$DOC_ID" > "$DOC_ID_FILE"
        print_info "Doc ID saved to: $DOC_ID_FILE"
    else
        print_success "Import completed"
    fi
else
    print_error "Import failed"
    echo "$output"
    exit 1
fi

# Show next steps
echo ""
print_info "Next Steps:"
echo "  1. View the doc in ClickUp"
echo "  2. Share with your team"
echo "  3. Update pages as needed with: cum page_update"
echo ""
