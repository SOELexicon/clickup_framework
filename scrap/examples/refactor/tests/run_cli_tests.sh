#!/bin/bash

# Run CLI tests for ClickUp JSON Manager refactored codebase
# This script uses python3 -m to ensure proper module resolution

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Add the repository root to PYTHONPATH
export PYTHONPATH="$REPO_ROOT:$PYTHONPATH"

# Run the CLI tests using unittest discover
echo "Running CLI tests..."
python3 -m unittest discover -s "$SCRIPT_DIR/unit/cli" -p "test_*.py" -v

exit_code=$?

# Run the specific CLI argument validation tests
echo -e "\nRunning CLI argument validation tests..."
python3 -m refactor.tests.unit.cli.test_cli_commands

# Exit with the status of the first test run
exit $exit_code 