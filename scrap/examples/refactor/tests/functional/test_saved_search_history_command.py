"""
Functional test for saved search history commands.

This module tests the functionality of the search history-related commands
in the SavedSearchCommand, including:
- Adding entries to search history
- Listing search history
- Clearing search history
- Running a search from history
- Saving a search from history
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import json
import sys
import time

from refactor.cli.commands.saved_search_command import SavedSearchCommand
from refactor.storage.saved_searches import SavedSearch, SearchHistoryEntry


# First, create the missing modules we need for the test
class MockUtils:
    """Mock utility classes needed by SavedSearchCommand."""
    
    @staticmethod
    def patch_modules():
        """Patch all utility modules needed by the command."""
        # Create modules if they don't exist
        if 'refactor.utils' not in sys.modules:
            sys.modules['refactor.utils'] = MagicMock()
        
        if 'refactor.utils.formatting' not in sys.modules:
            formatting_module = MagicMock()
            # Mock the format_table function to emit the actual table output instead of a message
            formatting_module.format_table = lambda headers, rows, **kwargs: f"| {' | '.join(headers)} | \n|{'-'*19}|{'-'*34}|{'-'*13}|{'-'*9}|\n" + "\n".join([f"| {' | '.join(str(cell) for cell in row)} | " for row in rows]) + "\n"
            # Mock the colorize function
            formatting_module.colorize = lambda text, color: f"{text}"
            # Mock the Color enum
            color_mock = MagicMock()
            color_mock.CYAN = "CYAN"
            color_mock.GREEN = "GREEN"
            formatting_module.Color = color_mock
            sys.modules['refactor.utils.formatting'] = formatting_module
        
        if 'refactor.utils.json_utils' not in sys.modules:
            json_utils_module = MagicMock()
            # Mock the load_json_data function
            json_utils_module.load_json_data = lambda file_path: json.loads(open(file_path).read()) if os.path.exists(file_path) else {}
            sys.modules['refactor.utils.json_utils'] = json_utils_module
        
        if 'refactor.utils.error_formatter' not in sys.modules:
            error_formatter_module = MagicMock()
            # Mock the format_error_message function
            error_formatter_module.format_error_message = lambda msg: f"Error: {msg}"
            sys.modules['refactor.utils.error_formatter'] = error_formatter_module


# Mocked SavedSearchesManager that doesn't try to write to a file
class MockSavedSearchesManager:
    """Mock manager for testing that doesn't save to disk."""
    
    def __init__(self):
        """Initialize with empty collections."""
        self.searches = {}
        self.history = []
    
    def save_search(self, name, query, description="", tags=None, category="general", 
                   is_template=False, variables=None, is_favorite=False):
        """Mock saving a search."""
        if name in self.searches and not is_template:
            return False
        
        search = {
            "name": name,
            "query": query,
            "description": description,
            "tags": tags or [],
            "category": category,
            "is_template": is_template,
            "variables": variables or [],
            "is_favorite": is_favorite,
            "created_at": time.time(),
            "last_used_at": None,
            "use_count": 0
        }
        
        self.searches[name] = search
        return True
    
    def update_search(self, name, **kwargs):
        """Mock updating a search."""
        if name not in self.searches:
            return False
        
        for key, value in kwargs.items():
            if key in self.searches[name]:
                self.searches[name][key] = value
        
        return True
    
    def get_search(self, name):
        """Mock retrieving a search."""
        if name not in self.searches:
            raise KeyError(f"No saved search found with name '{name}'")
        
        return self.searches[name]
    
    def add_to_history(self, query, saved_search_name=None, result_count=None):
        """Mock adding to search history."""
        entry = {
            "query": query,
            "saved_search_name": saved_search_name,
            "executed_at": time.time(),
            "result_count": result_count or 0
        }
        
        self.history.insert(0, entry)
        
        # Limit history size
        if len(self.history) > 50:
            self.history = self.history[:50]
    
    def get_history(self, limit=None, query_contains=None):
        """Mock retrieving search history."""
        # Start with all history entries
        filtered = self.history.copy()
        
        # Filter by query text if needed
        if query_contains:
            filtered = [entry for entry in filtered 
                      if query_contains.lower() in entry["query"].lower()]
        
        # Apply limit if needed
        if limit is not None:
            filtered = filtered[:limit]
        
        return filtered
    
    def clear_history(self):
        """Mock clearing search history."""
        count = len(self.history)
        self.history = []
        return count
    
    def delete_history_entry(self, timestamp):
        """Mock deleting a history entry by timestamp."""
        original_count = len(self.history)
        self.history = [entry for entry in self.history if entry["executed_at"] != timestamp]
        return len(self.history) < original_count


# Apply the patches before importing the command
MockUtils.patch_modules()


class TestSavedSearchHistoryCommand(unittest.TestCase):
    """
    Test the saved search history command functionality.
    
    This test case focuses on the history-related operations provided
    by the SavedSearchCommand class.
    """
    
    def setUp(self):
        """Set up test environment with mocked core manager and mocked storage."""
        # Mock the core manager
        self.mock_core_manager = MagicMock()
        
        # Create the command with the mocked dependencies
        self.command = SavedSearchCommand(self.mock_core_manager)
        
        # Replace the command's saved searches with our mock manager
        self.saved_searches = MockSavedSearchesManager()
        self.command.saved_searches = self.saved_searches
        
        # Add some test search history entries
        self.saved_searches.add_to_history("query1", None, 5)
        self.saved_searches.add_to_history("query2 and status == 'completed'", "test-search", 10)
        self.saved_searches.add_to_history("priority > 2", None, 3)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_history_list(self, mock_stdout):
        """Test the 'history list' subcommand."""
        # Create mock arguments
        args = MagicMock()
        args.saved_search_command = "history"
        args.history_command = "list"
        args.limit = 5
        args.query_contains = None
        
        # Execute the command
        result = self.command.execute(args)
        
        # Verify success return value
        self.assertEqual(result, 0)
        
        # Check output - now we're looking for the actual table output not the mock table message
        output = mock_stdout.getvalue()
        self.assertIn("Timestamp", output)
        self.assertIn("Search Query", output)
        self.assertIn("Total:", output)
        self.assertIn("query1", output)
        self.assertIn("priority > 2", output)
        
        # Get history directly to verify entries
        history = self.saved_searches.get_history()
        self.assertEqual(len(history), 3)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_history_list_with_query_filter(self, mock_stdout):
        """Test the 'history list' subcommand with query filtering."""
        # Create mock arguments
        args = MagicMock()
        args.saved_search_command = "history"
        args.history_command = "list"
        args.limit = 10
        args.query_contains = "priority"
        
        # Execute the command
        result = self.command.execute(args)
        
        # Verify success return value
        self.assertEqual(result, 0)
        
        # Get filtered history directly to verify filter works
        filtered_history = self.saved_searches.get_history(query_contains="priority")
        self.assertEqual(len(filtered_history), 1)
        self.assertEqual(filtered_history[0]["query"], "priority > 2")
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_history_clear_with_confirmation(self, mock_stdout):
        """Test the 'history clear' subcommand with confirmation."""
        # Create mock arguments
        args = MagicMock()
        args.saved_search_command = "history"
        args.history_command = "clear"
        args.confirm = True
        
        # Execute the command
        result = self.command.execute(args)
        
        # Verify success return value
        self.assertEqual(result, 0)
        
        # Check output
        output = mock_stdout.getvalue()
        self.assertIn("Cleared", output)
        
        # Verify history is empty
        history = self.saved_searches.get_history()
        self.assertEqual(len(history), 0)
    
    @patch('builtins.input', return_value='y')
    @patch('sys.stdout', new_callable=StringIO)
    def test_history_clear_with_prompt_yes(self, mock_stdout, mock_input):
        """Test the 'history clear' subcommand with yes at prompt."""
        # Create mock arguments
        args = MagicMock()
        args.saved_search_command = "history"
        args.history_command = "clear"
        args.confirm = False
        
        # Execute the command
        result = self.command.execute(args)
        
        # Verify success return value
        self.assertEqual(result, 0)
        
        # Check output
        output = mock_stdout.getvalue()
        self.assertIn("Cleared", output)
        
        # Verify history is empty
        history = self.saved_searches.get_history()
        self.assertEqual(len(history), 0)
    
    @patch('builtins.input', return_value='n')
    @patch('sys.stdout', new_callable=StringIO)
    def test_history_clear_with_prompt_no(self, mock_stdout, mock_input):
        """Test the 'history clear' subcommand with no at prompt."""
        # Create mock arguments
        args = MagicMock()
        args.saved_search_command = "history"
        args.history_command = "clear"
        args.confirm = False
        
        # Execute the command
        result = self.command.execute(args)
        
        # Verify success return value
        self.assertEqual(result, 0)
        
        # Check output
        output = mock_stdout.getvalue()
        self.assertIn("cancelled", output.lower())
        
        # Verify history is not cleared
        history = self.saved_searches.get_history()
        self.assertEqual(len(history), 3)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_history_delete(self, mock_stdout):
        """Test the 'history delete' subcommand."""
        # Get a timestamp from one of the entries
        history = self.saved_searches.get_history()
        timestamp = history[1]["executed_at"]
        
        # Create mock arguments
        args = MagicMock()
        args.saved_search_command = "history"
        args.history_command = "delete"
        args.timestamp = timestamp
        
        # Execute the command
        result = self.command.execute(args)
        
        # Verify success return value
        self.assertEqual(result, 0)
        
        # Check output
        output = mock_stdout.getvalue()
        self.assertIn("Deleted history entry", output)
        
        # Verify entry was deleted
        updated_history = self.saved_searches.get_history()
        self.assertEqual(len(updated_history), 2)
        timestamps = [entry["executed_at"] for entry in updated_history]
        self.assertNotIn(timestamp, timestamps)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_history_delete_nonexistent(self, mock_stdout):
        """Test the 'history delete' subcommand with nonexistent timestamp."""
        # Create mock arguments
        args = MagicMock()
        args.saved_search_command = "history"
        args.history_command = "delete"
        args.timestamp = 99999.99
        
        # Execute the command
        result = self.command.execute(args)
        
        # Verify failure return value
        self.assertEqual(result, 1)
        
        # Check error message
        output = mock_stdout.getvalue()
        self.assertIn("Error: No history entry found", output)
        
        # Verify history still has all entries
        history = self.saved_searches.get_history()
        self.assertEqual(len(history), 3)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_history_run(self, mock_stdout):
        """Test the 'history run' subcommand."""
        # Get a timestamp from one of the entries
        history = self.saved_searches.get_history()
        timestamp = history[0]["executed_at"]
        
        # Create mock arguments
        args = MagicMock()
        args.saved_search_command = "history"
        args.history_command = "run"
        args.timestamp = timestamp
        args.limit = None
        
        # Mock the execute_search method in the command
        self.command.execute_search = MagicMock(return_value=0)
        
        # Execute the command
        result = self.command.execute(args)
        
        # Verify success return value
        self.assertEqual(result, 0)
        
        # Verify execute_search was called with the right query
        self.command.execute_search.assert_called_once()
        call_args = self.command.execute_search.call_args[0]
        self.assertEqual(call_args[0], "priority > 2")
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_history_run_with_limit(self, mock_stdout):
        """Test the 'history run' subcommand with result limit."""
        # Get a timestamp from one of the entries
        history = self.saved_searches.get_history()
        timestamp = history[0]["executed_at"]
        
        # Create mock arguments
        args = MagicMock()
        args.saved_search_command = "history"
        args.history_command = "run"
        args.timestamp = timestamp
        args.limit = 10
        
        # Mock the execute_search method in the command
        self.command.execute_search = MagicMock(return_value=0)
        
        # Execute the command
        result = self.command.execute(args)
        
        # Verify success return value
        self.assertEqual(result, 0)
        
        # Verify execute_search was called with the right parameters
        self.command.execute_search.assert_called_once()
        call_args = self.command.execute_search.call_args[0]
        call_kwargs = self.command.execute_search.call_args[1]
        self.assertEqual(call_args[0], "priority > 2")
        self.assertEqual(call_kwargs.get("limit"), 10)
    
    @patch('builtins.input', return_value='status == ${status}')
    @patch('sys.stdout', new_callable=StringIO)
    def test_history_save(self, mock_stdout, mock_input):
        """Test the 'history save' subcommand."""
        # Get a timestamp from one of the entries
        history = self.saved_searches.get_history()
        timestamp = history[0]["executed_at"]  # "priority > 2"
        
        # Create mock arguments
        args = MagicMock()
        args.saved_search_command = "history"
        args.history_command = "save"
        args.timestamp = timestamp
        args.name = "high-priority"
        args.description = "Tasks with high priority"
        args.tags = ["priority", "important"]
        args.category = "filters"
        args.favorite = False
        
        # Mock the template creation method
        self.command._create_template_from_history = MagicMock(return_value=True)
        
        # Execute the command
        result = self.command.execute(args)
        
        # Verify success return value
        self.assertEqual(result, 0)
        
        # Verify template creation was called with right parameters
        self.command._create_template_from_history.assert_called_once()
    
    @patch('builtins.input', return_value='status == ${status}')
    @patch('sys.stdout', new_callable=StringIO)
    def test_history_save_duplicate_name(self, mock_stdout, mock_input):
        """Test the 'history save' subcommand with existing search name."""
        # First save a search with a name we'll try to use again
        self.saved_searches.save_search("existing-search", "some query")
        
        # Get a timestamp from one of the entries
        history = self.saved_searches.get_history()
        timestamp = history[0]["executed_at"]
        
        # Create mock arguments
        args = MagicMock()
        args.saved_search_command = "history"
        args.history_command = "save"
        args.timestamp = timestamp
        args.name = "existing-search"  # This name already exists
        args.description = ""
        args.tags = None
        args.category = "general"
        args.favorite = False
        
        # Mock the template creation method
        self.command._create_template_from_history = MagicMock(return_value=True)
        
        # Execute the command
        result = self.command.execute(args)
        
        # Verify success return value
        self.assertEqual(result, 0)
        
        # Verify template creation was called
        self.command._create_template_from_history.assert_called_once()


if __name__ == '__main__':
    unittest.main() 