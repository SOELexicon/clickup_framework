"""
Unit tests for the batch operations functionality in the SavedSearchesManager class.
"""

import os
import unittest
import tempfile
import shutil
import time
from typing import Dict, List

from refactor.storage.saved_searches import SavedSearchesManager, SavedSearch


class TestSearchBatchOperations(unittest.TestCase):
    """Test case for the batch operations functionality in SavedSearchesManager."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        # Create a SavedSearchesManager with the test directory
        self.manager = SavedSearchesManager(storage_dir=self.test_dir)
        
        # Create some test searches
        self.manager.save_search("test1", "status == 'complete'", tags=["status", "complete"])
        self.manager.save_search("test2", "priority >= 3", tags=["priority", "high"])
        self.manager.save_search("test3", "tags contains 'urgent'", tags=["tags", "urgent"])
        self.manager.save_search("test4", "assignee == 'me'", tags=["assignee"])
        self.manager.save_search("test5", "due_date < today()", tags=["date", "urgent"])
        
    def tearDown(self):
        """Clean up test fixtures after each test method."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_batch_delete(self):
        """Test deleting multiple searches at once."""
        # Delete multiple searches
        success_count, failed_names = self.manager.batch_delete(["test1", "test2", "nonexistent"])
        
        # Check results
        self.assertEqual(success_count, 2)
        self.assertEqual(len(failed_names), 1)
        self.assertEqual(failed_names[0], "nonexistent")
        
        # Verify the searches were deleted
        searches = self.manager.list_searches()
        search_names = [s.name for s in searches]
        self.assertNotIn("test1", search_names)
        self.assertNotIn("test2", search_names)
        self.assertIn("test3", search_names)
        
        # Check total count
        self.assertEqual(len(searches), 3)
    
    def test_batch_categorize(self):
        """Test setting category for multiple searches at once."""
        # Set category for multiple searches
        new_category = "important"
        success_count, failed_names = self.manager.batch_categorize(
            ["test1", "test3", "test5", "nonexistent"], 
            new_category
        )
        
        # Check results
        self.assertEqual(success_count, 3)
        self.assertEqual(len(failed_names), 1)
        self.assertEqual(failed_names[0], "nonexistent")
        
        # Verify the categories were updated
        search1 = self.manager.get_search("test1")
        search3 = self.manager.get_search("test3")
        search5 = self.manager.get_search("test5")
        
        self.assertEqual(search1.category, new_category)
        self.assertEqual(search3.category, new_category)
        self.assertEqual(search5.category, new_category)
        
        # Check that other search wasn't affected
        search2 = self.manager.get_search("test2")
        self.assertNotEqual(search2.category, new_category)
    
    def test_batch_add_tags(self):
        """Test adding tags to multiple searches at once."""
        # Add tags to multiple searches
        new_tags = ["featured", "important"]
        success_count, failed_names = self.manager.batch_add_tags(
            ["test1", "test2", "nonexistent"], 
            new_tags
        )
        
        # Check results
        self.assertEqual(success_count, 2)
        self.assertEqual(len(failed_names), 1)
        self.assertEqual(failed_names[0], "nonexistent")
        
        # Verify the tags were added
        search1 = self.manager.get_search("test1")
        search2 = self.manager.get_search("test2")
        
        for tag in new_tags:
            self.assertIn(tag, search1.tags)
            self.assertIn(tag, search2.tags)
        
        # Check that original tags are preserved
        self.assertIn("status", search1.tags)
        self.assertIn("complete", search1.tags)
        self.assertIn("priority", search2.tags)
        self.assertIn("high", search2.tags)
        
        # Check that other search wasn't affected
        search3 = self.manager.get_search("test3")
        for tag in new_tags:
            self.assertNotIn(tag, search3.tags)
    
    def test_batch_remove_tags(self):
        """Test removing tags from multiple searches at once."""
        # Remove tags from multiple searches
        tags_to_remove = ["urgent"]
        success_count, failed_names = self.manager.batch_remove_tags(
            ["test3", "test5", "nonexistent"], 
            tags_to_remove
        )
        
        # Check results
        self.assertEqual(success_count, 2)
        self.assertEqual(len(failed_names), 1)
        self.assertEqual(failed_names[0], "nonexistent")
        
        # Verify the tags were removed
        search3 = self.manager.get_search("test3")
        search5 = self.manager.get_search("test5")
        
        self.assertNotIn("urgent", search3.tags)
        self.assertNotIn("urgent", search5.tags)
        
        # Check that other tags are preserved
        self.assertIn("tags", search3.tags)
        self.assertIn("date", search5.tags)
    
    def test_batch_toggle_favorite(self):
        """Test toggling favorite status for multiple searches at once."""
        # Mark multiple searches as favorites
        success_count, failed_names = self.manager.batch_toggle_favorite(
            ["test1", "test3", "nonexistent"], 
            True
        )
        
        # Check results
        self.assertEqual(success_count, 2)
        self.assertEqual(len(failed_names), 1)
        self.assertEqual(failed_names[0], "nonexistent")
        
        # Verify the favorite status was updated
        search1 = self.manager.get_search("test1")
        search3 = self.manager.get_search("test3")
        
        self.assertTrue(search1.is_favorite)
        self.assertTrue(search3.is_favorite)
        
        # Check that other search wasn't affected
        search2 = self.manager.get_search("test2")
        self.assertFalse(search2.is_favorite)
    
    def test_delete_searches_alias(self):
        """Test the delete_searches alias method."""
        # Use the alias method
        success_count, failed_names = self.manager.delete_searches(["test4", "nonexistent"])
        
        # Check results
        self.assertEqual(success_count, 1)
        self.assertEqual(len(failed_names), 1)
        
        # Verify the search was deleted
        searches = self.manager.list_searches()
        search_names = [s.name for s in searches]
        self.assertNotIn("test4", search_names)
    
    def test_categorize_searches_alias(self):
        """Test the categorize_searches alias method."""
        # Use the alias method
        success_count, failed_names = self.manager.categorize_searches(
            ["test1", "nonexistent"], 
            "new_category"
        )
        
        # Check results
        self.assertEqual(success_count, 1)
        self.assertEqual(len(failed_names), 1)
        
        # Verify the category was updated
        search1 = self.manager.get_search("test1")
        self.assertEqual(search1.category, "new_category")
    
    def test_tag_searches_alias(self):
        """Test the tag_searches alias method."""
        # Use the alias method
        success_count, failed_names = self.manager.tag_searches(
            ["test1", "nonexistent"], 
            ["new_tag"]
        )
        
        # Check results
        self.assertEqual(success_count, 1)
        self.assertEqual(len(failed_names), 1)
        
        # Verify the tag was added
        search1 = self.manager.get_search("test1")
        self.assertIn("new_tag", search1.tags)
    
    def test_untag_searches_alias(self):
        """Test the untag_searches alias method."""
        # Use the alias method
        success_count, failed_names = self.manager.untag_searches(
            ["test1", "nonexistent"], 
            ["status"]
        )
        
        # Check results
        self.assertEqual(success_count, 1)
        self.assertEqual(len(failed_names), 1)
        
        # Verify the tag was removed
        search1 = self.manager.get_search("test1")
        self.assertNotIn("status", search1.tags)
    
    def test_batch_operations_with_empty_list(self):
        """Test batch operations with empty list of names."""
        # Try batch operations with empty list
        success_count, failed_names = self.manager.batch_delete([])
        self.assertEqual(success_count, 0)
        self.assertEqual(len(failed_names), 0)
        
        success_count, failed_names = self.manager.batch_categorize([], "category")
        self.assertEqual(success_count, 0)
        self.assertEqual(len(failed_names), 0)
        
        success_count, failed_names = self.manager.batch_add_tags([], ["tag"])
        self.assertEqual(success_count, 0)
        self.assertEqual(len(failed_names), 0)
        
        success_count, failed_names = self.manager.batch_remove_tags([], ["tag"])
        self.assertEqual(success_count, 0)
        self.assertEqual(len(failed_names), 0)
        
        success_count, failed_names = self.manager.batch_toggle_favorite([], True)
        self.assertEqual(success_count, 0)
        self.assertEqual(len(failed_names), 0)


if __name__ == "__main__":
    unittest.main() 