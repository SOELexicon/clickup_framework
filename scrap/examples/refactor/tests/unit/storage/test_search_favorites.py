"""
Unit tests for the favorites functionality in the SavedSearchesManager class.
"""

import os
import unittest
import tempfile
import shutil
import time
from typing import Dict, List

from refactor.storage.saved_searches import SavedSearchesManager, SavedSearch


class TestSearchFavorites(unittest.TestCase):
    """Test case for the favorites functionality in SavedSearchesManager."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        # Create a SavedSearchesManager with the test directory
        self.manager = SavedSearchesManager(storage_dir=self.test_dir)
        
        # Create some test searches
        self.manager.save_search("test1", "status == 'complete'", category="status")
        self.manager.save_search("test2", "priority >= 3", category="priority")
        self.manager.save_search("test3", "tags contains 'urgent'", category="tags")
        
    def tearDown(self):
        """Clean up test fixtures after each test method."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_create_with_favorite(self):
        """Test creating a search with favorite flag."""
        # Create a new search that should be favorited
        search = self.manager.save_search(
            "favorite_search",
            "status == 'complete'",
            tags=["favorite", "status"]
        )
        
        # Mark it as favorite after creation
        self.manager.add_to_favorites("favorite_search")
        
        # Get the search and verify it's marked as favorite
        favorite_search = self.manager.get_search("favorite_search")
        self.assertTrue(favorite_search.is_favorite)
        
        # It should appear in the list of favorites
        favorites = self.manager.list_favorites()
        favorite_names = [s.name for s in favorites]
        self.assertIn("favorite_search", favorite_names)
    
    def test_toggle_favorite(self):
        """Test toggling the favorite status of a search."""
        # Toggle a search to favorite
        new_status = self.manager.toggle_favorite("test1")
        self.assertTrue(new_status)
        
        # Check if the status was updated
        search = self.manager.get_search("test1")
        self.assertTrue(search.is_favorite)
        
        # Toggle back to not favorite
        new_status = self.manager.toggle_favorite("test1")
        self.assertFalse(new_status)
        
        # Check if the status was updated again
        search = self.manager.get_search("test1")
        self.assertFalse(search.is_favorite)
    
    def test_add_to_favorites(self):
        """Test adding a search to favorites."""
        # Add a search to favorites
        result = self.manager.add_to_favorites("test2")
        self.assertTrue(result)
        
        # Check if it's now a favorite
        search = self.manager.get_search("test2")
        self.assertTrue(search.is_favorite)
        
        # Try adding a non-existent search
        result = self.manager.add_to_favorites("nonexistent")
        self.assertFalse(result)
    
    def test_remove_from_favorites(self):
        """Test removing a search from favorites."""
        # First make it a favorite
        self.manager.add_to_favorites("test3")
        
        # Then remove from favorites
        result = self.manager.remove_from_favorites("test3")
        self.assertTrue(result)
        
        # Check if it's no longer a favorite
        search = self.manager.get_search("test3")
        self.assertFalse(search.is_favorite)
        
        # Try removing a non-existent search
        result = self.manager.remove_from_favorites("nonexistent")
        self.assertFalse(result)
    
    def test_list_favorites(self):
        """Test listing favorite searches."""
        # Make two searches favorites
        self.manager.add_to_favorites("test1")
        self.manager.add_to_favorites("test3")
        
        # List all favorites
        favorites = self.manager.list_favorites()
        self.assertEqual(len(favorites), 2)
        
        # Check that the correct searches are marked as favorites
        favorite_names = [f.name for f in favorites]
        self.assertIn("test1", favorite_names)
        self.assertIn("test3", favorite_names)
        self.assertNotIn("test2", favorite_names)
    
    def test_list_favorites_with_filters(self):
        """Test listing favorites with filters."""
        # Make all searches favorites
        self.manager.add_to_favorites("test1")
        self.manager.add_to_favorites("test2")
        self.manager.add_to_favorites("test3")
        
        # Filter by category
        status_favorites = self.manager.list_favorites(category="status")
        self.assertEqual(len(status_favorites), 1)
        self.assertEqual(status_favorites[0].name, "test1")
        
        # Filter by name
        filtered_favorites = self.manager.list_favorites(name_contains="test")
        self.assertEqual(len(filtered_favorites), 3)
    
    def test_batch_toggle_favorite(self):
        """Test batch toggle favorite functionality."""
        # Add multiple searches to favorites
        result = self.manager.batch_toggle_favorite(["test1", "test2"], True)
        success_count, failed_names = result
        
        # Check results
        self.assertEqual(success_count, 2)
        self.assertEqual(len(failed_names), 0)
        
        # Verify they're marked as favorites
        search1 = self.manager.get_search("test1")
        search2 = self.manager.get_search("test2")
        self.assertTrue(search1.is_favorite)
        self.assertTrue(search2.is_favorite)
        
        # Remove multiple searches from favorites
        result = self.manager.batch_toggle_favorite(["test1", "test2", "nonexistent"], False)
        success_count, failed_names = result
        
        # Check results
        self.assertEqual(success_count, 2)
        self.assertEqual(len(failed_names), 1)
        self.assertEqual(failed_names[0], "nonexistent")
        
        # Verify they're no longer favorites
        search1 = self.manager.get_search("test1")
        search2 = self.manager.get_search("test2")
        self.assertFalse(search1.is_favorite)
        self.assertFalse(search2.is_favorite)
    
    def test_add_to_favorites_batch(self):
        """Test adding multiple searches to favorites at once."""
        # Add multiple searches to favorites
        result = self.manager.add_to_favorites(["test1", "test3"])
        success_count, failed_names = result
        
        # Check results
        self.assertEqual(success_count, 2)
        self.assertEqual(len(failed_names), 0)
        
        # Verify they're marked as favorites
        search1 = self.manager.get_search("test1")
        search3 = self.manager.get_search("test3")
        self.assertTrue(search1.is_favorite)
        self.assertTrue(search3.is_favorite)
    
    def test_remove_from_favorites_batch(self):
        """Test removing multiple searches from favorites at once."""
        # First mark them as favorites
        self.manager.add_to_favorites(["test1", "test2"])
        
        # Remove multiple searches from favorites
        result = self.manager.remove_from_favorites(["test1", "test2", "nonexistent"])
        success_count, failed_names = result
        
        # Check results
        self.assertEqual(success_count, 2)
        self.assertEqual(len(failed_names), 1)
        self.assertEqual(failed_names[0], "nonexistent")
        
        # Verify they're no longer favorites
        search1 = self.manager.get_search("test1")
        search2 = self.manager.get_search("test2")
        self.assertFalse(search1.is_favorite)
        self.assertFalse(search2.is_favorite)


if __name__ == "__main__":
    unittest.main() 