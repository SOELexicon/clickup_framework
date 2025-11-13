#!/bin/bash
# Setup git hooks for ClickUp Framework
# This script installs pre-commit hooks and configures git to use .githooks directory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   ClickUp Framework - Git Hooks Setup${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Get the project root directory (parent of scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📂 Project root: $PROJECT_ROOT"
echo ""

# Step 1: Check if git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: Not a git repository${NC}"
    echo "Run this script from the project root directory"
    exit 1
fi

# Step 2: Install pre-commit if not already installed
echo "🔧 Checking dependencies..."
if ! command -v pre-commit &> /dev/null; then
    echo -e "${YELLOW}⚠️  pre-commit not found${NC}"
    echo "Installing pre-commit..."

    if command -v pip &> /dev/null; then
        pip install pre-commit
        echo -e "${GREEN}✓ pre-commit installed${NC}"
    else
        echo -e "${RED}❌ Error: pip not found${NC}"
        echo "Please install pip and run this script again"
        exit 1
    fi
else
    echo -e "${GREEN}✓ pre-commit is installed${NC}"
fi
echo ""

# Step 3: Install development dependencies
echo "📦 Installing development dependencies..."
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
    echo -e "${GREEN}✓ Development dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  requirements-dev.txt not found, skipping...${NC}"
fi
echo ""

# Step 4: Configure git to use .githooks directory
echo "⚙️  Configuring git hooks directory..."
git config core.hooksPath .githooks
echo -e "${GREEN}✓ Git hooks directory set to .githooks/${NC}"
echo ""

# Step 5: Make hooks executable
echo "🔐 Making hook scripts executable..."
if [ -d ".githooks" ]; then
    chmod +x .githooks/*
    echo -e "${GREEN}✓ Hook scripts are now executable${NC}"
else
    echo -e "${RED}❌ Error: .githooks directory not found${NC}"
    exit 1
fi
echo ""

# Step 6: Install pre-commit hooks
echo "🪝 Installing pre-commit framework hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit framework hooks installed${NC}"
else
    echo -e "${YELLOW}⚠️  .pre-commit-config.yaml not found, skipping...${NC}"
fi
echo ""

# Step 7: Run pre-commit on all files (optional)
echo "🧪 Testing pre-commit hooks..."
read -p "Do you want to run pre-commit on all files now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running pre-commit on all files..."
    if pre-commit run --all-files; then
        echo -e "${GREEN}✓ All checks passed!${NC}"
    else
        echo -e "${YELLOW}⚠️  Some checks failed${NC}"
        echo "You can fix these issues and run 'pre-commit run --all-files' again"
    fi
else
    echo "Skipped pre-commit run"
fi
echo ""

# Summary
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Git hooks setup complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "What's installed:"
echo "  • Pre-commit framework hooks (format, lint, etc.)"
echo "  • Custom pre-commit hook in .githooks/pre-commit"
echo "  • Development dependencies (pytest, black, flake8, etc.)"
echo ""
echo "To manually run pre-commit checks:"
echo "  pre-commit run --all-files"
echo ""
echo "To bypass hooks (not recommended):"
echo "  git commit --no-verify"
echo ""
echo "To update hooks:"
echo "  pre-commit autoupdate"
echo ""
