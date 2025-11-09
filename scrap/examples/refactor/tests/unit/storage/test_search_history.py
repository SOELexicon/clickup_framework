import unittest
import tempfile
import os
import json
import time
from unittest.mock import patch

from refactor.storage.saved_searches import SavedSearchesManager, SearchHistoryEntry


class TestSearchHistory(unittest.TestCase):
    """Test cases for search history functionality in SavedSearchesManager."""
    
    def setUp(self):
        """Set up a temporary directory for test files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = self.temp_dir.name
        
        # Create a manager instance with the test storage directory
        self.manager = SavedSearchesManager(storage_dir=self.storage_dir)
        
        # Ensure we start with an empty history
        self.manager.clear_history()
    
    def tearDown(self):
        """Clean up temporary directory after tests."""
        self.temp_dir.cleanup()
    
    def test_add_to_history(self):
        """Test adding a search query to history."""
        query = "name contains 'Task' and status == 'in progress'"
        saved_search_name = "test_search"
        result_count = 5
        
        # Add to history
        self.manager.add_to_history(query, saved_search_name, result_count)
        
        # Get history and check if entry was added
        history = self.manager.get_history()
        self.assertEqual(len(history), 1)
        
        entry = history[0]
        self.assertEqual(entry.query, query)
        self.assertEqual(entry.saved_search_name, saved_search_name)
        self.assertEqual(entry.result_count, result_count)
        self.assertIsNotNone(entry.executed_at)
    
    def test_history_limit(self):
        """Test that history is limited to the maximum size."""
        # Override the default limit for testing
        original_limit = SavedSearchesManager.DEFAULT_HISTORY_LIMIT
        test_limit = 3
        
        # Create a new manager with a smaller history limit
        manager = SavedSearchesManager(storage_dir=self.storage_dir, history_limit=test_limit)
        
        try:
            # Add more entries than the limit
            for i in range(5):
                manager.add_to_history(f"query{i}", None, i)
                time.sleep(0.01)  # Ensure different timestamps
            
            # Verify only the latest entries are kept
            history = manager.get_history()
            self.assertEqual(len(history), test_limit)
            
            # Check that the oldest entries were removed (history is returned newest first)
            queries = [entry.query for entry in history]
            self.assertIn("query4", queries)
            self.assertIn("query3", queries)
            self.assertIn("query2", queries)
            self.assertNotIn("query1", queries)
            self.assertNotIn("query0", queries)
        finally:
            # Restore the original limit (not strictly necessary since we use a different instance)
            SavedSearchesManager.DEFAULT_HISTORY_LIMIT = original_limit
    
    def test_get_history_with_limit(self):
        """Test retrieving history with a limit parameter."""
        # Add several entries
        for i in range(5):
            self.manager.add_to_history(f"query{i}", None, i)
            time.sleep(0.01)  # Ensure different timestamps
        
        # Get limited history
        history = self.manager.get_history(limit=2)
        self.assertEqual(len(history), 2)
        
        # Check that we got the most recent entries (history is returned newest first)
        self.assertEqual(history[0].query, "query4")
        self.assertEqual(history[1].query, "query3")
    
    def test_get_history_with_query_filter(self):
        """Test retrieving history filtered by query content."""
        # Add entries with different queries
        self.manager.add_to_history("find task", None, 1)
        self.manager.add_to_history("list projects", None, 2)
        self.manager.add_to_history("find user", None, 3)
        
        # Filter by 'find'
        history = self.manager.get_history(query_contains="find")
        self.assertEqual(len(history), 2)
        queries = [entry.query for entry in history]
        self.assertIn("find task", queries)
        self.assertIn("find user", queries)
        
        # Filter by 'task'
        history = self.manager.get_history(query_contains="task")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].query, "find task")
    
    def test_clear_history(self):
        """Test clearing all history entries."""
        # Add some entries
        for i in range(3):
            self.manager.add_to_history(f"query{i}", None, i)
        
        # Verify we have entries
        self.assertEqual(len(self.manager.get_history()), 3)
        
        # Clear history
        count = self.manager.clear_history()
        self.assertEqual(count, 3)
        
        # Verify history is empty
        self.assertEqual(len(self.manager.get_history()), 0)
    
    def test_delete_history_entry(self):
        """Test deleting a specific history entry by timestamp."""
        # Add entries
        for i in range(3):
            self.manager.add_to_history(f"query{i}", None, i)
            time.sleep(0.01)  # Ensure different timestamps
        
        # Get the entries
        entries = self.manager.get_history()
        self.assertEqual(len(entries), 3)
        
        # Delete the middle entry
        timestamp = entries[1].executed_at
        success = self.manager.delete_history_entry(timestamp)
        self.assertTrue(success)
        
        # Verify entry was deleted
        updated_entries = self.manager.get_history()
        self.assertEqual(len(updated_entries), 2)
        timestamps = [e.executed_at for e in updated_entries]
        self.assertNotIn(timestamp, timestamps)
    
    def test_delete_nonexistent_history_entry(self):
        """Test deleting a history entry that doesn't exist."""
        # Add an entry
        self.manager.add_to_history("query", None, 1)
        
        # Try to delete with a non-existent timestamp
        success = self.manager.delete_history_entry(99999.99)
        self.assertFalse(success)
        
        # Verify no entries were removed
        self.assertEqual(len(self.manager.get_history()), 1)
    
    def test_history_persistence(self):
        """Test that history is saved and loaded from storage."""
        # Add some entries
        self.manager.add_to_history("query1", "saved1", 1)
        self.manager.add_to_history("query2", None, 2)
        
        # Save to storage (this happens automatically in add_to_history)
        
        # Create a new manager instance that will load from the same file
        new_manager = SavedSearchesManager(storage_dir=self.storage_dir)
        
        # Check that history was loaded
        history = new_manager.get_history()
        self.assertEqual(len(history), 2)
        
        # Verify entry details were preserved
        entry1 = next((e for e in history if e.query == "query1"), None)
        self.assertIsNotNone(entry1)
        self.assertEqual(entry1.saved_search_name, "saved1")
        self.assertEqual(entry1.result_count, 1)
        
        entry2 = next((e for e in history if e.query == "query2"), None)
        self.assertIsNotNone(entry2)
        self.assertIsNone(entry2.saved_search_name)
        self.assertEqual(entry2.result_count, 2)
    
    def test_search_history_entry_serialization(self):
        """Test that SearchHistoryEntry can be serialized and deserialized correctly."""
        # Create an entry
        entry = SearchHistoryEntry(query="test query", saved_search_name="test_search")
        entry.executed_at = 123456.789
        entry.set_result_count(10)
        
        # Serialize to dict
        entry_dict = entry.to_dict()
        
        # Deserialize from dict
        recreated = SearchHistoryEntry.from_dict(entry_dict)
        
        # Compare attributes
        self.assertEqual(recreated.query, entry.query)
        self.assertEqual(recreated.executed_at, entry.executed_at)
        self.assertEqual(recreated.saved_search_name, entry.saved_search_name)
        self.assertEqual(recreated.result_count, entry.result_count)
    
    def test_search_history_in_json_format(self):
        """Test that search history can be stored in a valid JSON format."""
        # Add entries
        self.manager.add_to_history("query1", "saved1", 1)
        self.manager.add_to_history("query2", None, 2)
        
        # Storage happens automatically in add_to_history
        
        # Get the storage file path from the manager
        storage_file = self.manager.storage_file
        
        # Verify the storage file exists
        self.assertTrue(os.path.exists(storage_file))
        
        # Read the file directly
        with open(storage_file, 'r') as f:
            data = json.load(f)
        
        # Verify the structure
        self.assertIn("history", data)
        self.assertEqual(len(data["history"]), 2)
        
        # Check the format of an entry
        entry = data["history"][0]
        self.assertIn("query", entry)
        self.assertIn("executed_at", entry)
        self.assertIn("result_count", entry)
        
        # Check types
        self.assertIsInstance(entry["query"], str)
        self.assertIsInstance(entry["executed_at"], float)
        self.assertIsInstance(entry["result_count"], int)


if __name__ == "__main__":
    unittest.main() 