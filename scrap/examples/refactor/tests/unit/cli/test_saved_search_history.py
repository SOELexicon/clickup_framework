"""
Unit test for saved search history functionality.

This module provides a simple test for the search history functionality
in the SavedSearchesManager class.
"""

import unittest
import tempfile
import os
import time
from unittest.mock import MagicMock

from refactor.storage.saved_searches import SavedSearchesManager, SearchHistoryEntry


class TestSearchHistoryBasics(unittest.TestCase):
    """Test the basic functionality of search history in SavedSearchesManager."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        # Create a saved searches manager
        self.manager = SavedSearchesManager(storage_dir=self.temp_dir.name)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        self.temp_dir.cleanup()
    
    def test_add_and_retrieve_history(self):
        """Test adding and retrieving search history entries."""
        # Add entries to history
        self.manager.add_to_history("query1", "search1", 5)
        self.manager.add_to_history("query2", None, 10)
        
        # Get history
        history = self.manager.get_history()
        
        # Check size
        self.assertEqual(len(history), 2)
        
        # Check entry properties
        entry1 = history[0] if history[0].query == "query2" else history[1]
        self.assertEqual(entry1.query, "query2")
        self.assertIsNone(entry1.saved_search_name)
        self.assertEqual(entry1.result_count, 10)
        
        entry2 = history[0] if history[0].query == "query1" else history[1]
        self.assertEqual(entry2.query, "query1")
        self.assertEqual(entry2.saved_search_name, "search1")
        self.assertEqual(entry2.result_count, 5)
    
    def test_history_limit(self):
        """Test that history is limited to max size."""
        # Set a small limit for testing
        limit = 3
        manager = SavedSearchesManager(
            storage_dir=self.temp_dir.name,
            history_limit=limit
        )
        
        # Add more entries than the limit
        for i in range(5):
            manager.add_to_history(f"query{i}", None, i)
            time.sleep(0.01)  # Ensure different timestamps
        
        # Get history and check size
        history = manager.get_history()
        self.assertEqual(len(history), limit)
        
        # Check that we have the most recent entries
        queries = [entry.query for entry in history]
        for i in range(2, 5):
            self.assertIn(f"query{i}", queries)
        
        # Check that older entries were discarded
        self.assertNotIn("query0", queries)
        self.assertNotIn("query1", queries)
    
    def test_clear_history(self):
        """Test clearing search history."""
        # Add entries
        for i in range(3):
            self.manager.add_to_history(f"query{i}", None, i)
        
        # Verify entries were added
        self.assertEqual(len(self.manager.get_history()), 3)
        
        # Clear history
        count = self.manager.clear_history()
        
        # Check that the count matches
        self.assertEqual(count, 3)
        
        # Verify history is empty
        self.assertEqual(len(self.manager.get_history()), 0)
    
    def test_delete_history_entry(self):
        """Test deleting a specific history entry."""
        # Add entries with a delay to ensure different timestamps
        self.manager.add_to_history("query1", None, 1)
        time.sleep(0.01)  # Ensure different timestamps
        self.manager.add_to_history("query2", None, 2)
        
        # Get the entries
        history = self.manager.get_history()
        entry_to_delete = history[0]
        remaining_entry_query = history[1].query
        
        # Delete one entry
        success = self.manager.delete_history_entry(entry_to_delete.executed_at)
        
        # Check success
        self.assertTrue(success)
        
        # Check that only one entry remains
        updated_history = self.manager.get_history()
        self.assertEqual(len(updated_history), 1)
        
        # Check that the correct entry remains
        self.assertEqual(updated_history[0].query, remaining_entry_query)
    
    def test_history_query_filtering(self):
        """Test filtering history by query content."""
        # Add entries with different queries
        self.manager.add_to_history("find users", None, 3)
        self.manager.add_to_history("list tasks", None, 5)
        self.manager.add_to_history("find bugs", None, 2)
        
        # Filter by "find"
        find_results = self.manager.get_history(query_contains="find")
        
        # Check results
        self.assertEqual(len(find_results), 2)
        queries = [entry.query for entry in find_results]
        self.assertIn("find users", queries)
        self.assertIn("find bugs", queries)
        
        # Filter by "tasks"
        task_results = self.manager.get_history(query_contains="tasks")
        
        # Check results
        self.assertEqual(len(task_results), 1)
        self.assertEqual(task_results[0].query, "list tasks")


if __name__ == "__main__":
    unittest.main() 