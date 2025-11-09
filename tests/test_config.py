"""
Test Configuration

Configuration for ClickUp Framework tests.
Tests will run in the specified ClickUp space.
"""

import os

# Test Space Configuration
# Space URL: https://app.clickup.com/90151898946/v/s/90158025753
TEST_SPACE_ID = "90158025753"
TEST_TEAM_ID = "90151898946"

# API Token (from environment)
API_TOKEN = os.environ.get("CLICKUP_API_TOKEN")

# Test naming prefix (to identify and clean up test resources)
TEST_PREFIX = "[TEST]"

# Test resource names
TEST_FOLDER_NAME = f"{TEST_PREFIX} Framework Tests"
TEST_LIST_NAME = f"{TEST_PREFIX} Test Tasks"
TEST_TASK_PREFIX = f"{TEST_PREFIX}"

# Test configuration
CLEANUP_AFTER_TESTS = True  # Set to False to keep test data for inspection
VERBOSE_OUTPUT = True  # Print detailed test information
