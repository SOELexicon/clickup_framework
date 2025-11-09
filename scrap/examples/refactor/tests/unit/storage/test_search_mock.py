"""
Unit tests for the search favorites and batch operations using mocks.
"""

import os
import unittest
import tempfile
import shutil
import json
from unittest import mock

from refactor.storage.saved_searches import SavedSearchesManager, SavedSearch


class TestSearchMockFavoritesAndBatchOperations(unittest.TestCase):
    """Test case for the favorites and batch operations functionality using mocks."""
    
    def setUp(self):
        """Set up test fixtures before each test."""
        # Create test searches
        self.test_searches = [
            SavedSearch(
                name="test1",
                query="status == 'complete'",
                description="Test search 1",
                tags=["status", "complete"],
                category="",
                is_favorite=False
            ),
            SavedSearch(
                name="test2",
                query="priority >= 3",
                description="Test search 2",
                tags=["priority", "high"],
                category="",
                is_favorite=False
            ),
            SavedSearch(
                name="test3",
                query="tags contains 'urgent'",
                description="Test search 3",
                tags=["tags", "urgent"],
                category="",
                is_favorite=False
            ),
            SavedSearch(
                name="test4",
                query="assignee == 'me'",
                description="Test search 4",
                tags=["assignee"],
                category="",
                is_favorite=False
            ),
            SavedSearch(
                name="test5",
                query="due_date < today()",
                description="Test search 5",
                tags=["date", "urgent"],
                category="",
                is_favorite=False
            )
        ]
        
        # Create a mock manager
        self.manager = mock.Mock(spec=SavedSearchesManager)
        
        # Setup initial state for the mock
        self.manager.list_searches.return_value = self.test_searches.copy()
        
        # Setup get_search to return the correct search
        def get_search_side_effect(name):
            for search in self.test_searches:
                if search.name == name:
                    return search
            return None
        
        self.manager.get_search.side_effect = get_search_side_effect
        
        # Setup list_favorites to return searches marked as favorite
        def list_favorites_side_effect(*args, **kwargs):
            return [s for s in self.test_searches if s.is_favorite]
        
        self.manager.list_favorites.side_effect = list_favorites_side_effect
        
        # Setup add_to_favorites to mark a search as favorite
        def add_to_favorites_side_effect(name):
            for search in self.test_searches:
                if search.name == name:
                    search.is_favorite = True
                    return True
            return False
        
        self.manager.add_to_favorites.side_effect = add_to_favorites_side_effect
        
        # Setup remove_from_favorites to unmark a search as favorite
        def remove_from_favorites_side_effect(name):
            for search in self.test_searches:
                if search.name == name:
                    search.is_favorite = False
                    return True
            return False
        
        self.manager.remove_from_favorites.side_effect = remove_from_favorites_side_effect
        
        # Setup batch_toggle_favorite
        def batch_toggle_favorite_side_effect(names, is_favorite):
            success_count = 0
            failed_names = []
            for name in names:
                found = False
                for search in self.test_searches:
                    if search.name == name:
                        search.is_favorite = is_favorite
                        success_count += 1
                        found = True
                        break
                if not found:
                    failed_names.append(name)
            return success_count, failed_names
        
        self.manager.batch_toggle_favorite.side_effect = batch_toggle_favorite_side_effect
        
        # Setup batch_delete
        def batch_delete_side_effect(names):
            success_count = 0
            failed_names = []
            for name in names:
                found = False
                for i, search in enumerate(self.test_searches):
                    if search.name == name:
                        self.test_searches.pop(i)
                        success_count += 1
                        found = True
                        break
                if not found:
                    failed_names.append(name)
            
            # Update the list_searches mock return value
            self.manager.list_searches.return_value = self.test_searches.copy()
            
            return success_count, failed_names
        
        self.manager.batch_delete.side_effect = batch_delete_side_effect
        
        # Setup batch_categorize
        def batch_categorize_side_effect(names, category):
            success_count = 0
            failed_names = []
            for name in names:
                found = False
                for search in self.test_searches:
                    if search.name == name:
                        search.category = category
                        success_count += 1
                        found = True
                        break
                if not found:
                    failed_names.append(name)
            return success_count, failed_names
        
        self.manager.batch_categorize.side_effect = batch_categorize_side_effect
        
        # Setup batch_add_tags
        def batch_add_tags_side_effect(names, tags):
            success_count = 0
            failed_names = []
            for name in names:
                found = False
                for search in self.test_searches:
                    if search.name == name:
                        for tag in tags:
                            if tag not in search.tags:
                                search.tags.append(tag)
                        success_count += 1
                        found = True
                        break
                if not found:
                    failed_names.append(name)
            return success_count, failed_names
        
        self.manager.batch_add_tags.side_effect = batch_add_tags_side_effect
        
        # Setup batch_remove_tags
        def batch_remove_tags_side_effect(names, tags):
            success_count = 0
            failed_names = []
            for name in names:
                found = False
                for search in self.test_searches:
                    if search.name == name:
                        search.tags = [t for t in search.tags if t not in tags]
                        success_count += 1
                        found = True
                        break
                if not found:
                    failed_names.append(name)
            return success_count, failed_names
        
        self.manager.batch_remove_tags.side_effect = batch_remove_tags_side_effect
    
    def test_favorite_functionality(self):
        """Test favorite functionality with mocks."""
        # Test adding searches to favorites
        self.manager.add_to_favorites("test1")
        self.manager.add_to_favorites("test3")
        
        # Verify searches are marked as favorites
        favorites = self.manager.list_favorites()
        self.assertEqual(len(favorites), 2)
        favorite_names = [s.name for s in favorites]
        self.assertIn("test1", favorite_names)
        self.assertIn("test3", favorite_names)
        
        # Test removing a search from favorites
        self.manager.remove_from_favorites("test1")
        
        # Verify it's removed
        favorites = self.manager.list_favorites()
        self.assertEqual(len(favorites), 1)
        favorite_names = [s.name for s in favorites]
        self.assertNotIn("test1", favorite_names)
        self.assertIn("test3", favorite_names)
        
        # Test batch operations
        # Add multiple to favorites
        success_count, failed_names = self.manager.batch_toggle_favorite(["test4", "test5"], True)
        
        # Verify correct counts
        self.assertEqual(success_count, 2)
        self.assertEqual(len(failed_names), 0)
        
        # Verify they're added
        favorites = self.manager.list_favorites()
        self.assertEqual(len(favorites), 3)
        favorite_names = [s.name for s in favorites]
        self.assertIn("test3", favorite_names)
        self.assertIn("test4", favorite_names)
        self.assertIn("test5", favorite_names)
        
        # Remove multiple from favorites
        success_count, failed_names = self.manager.batch_toggle_favorite(["test3", "test5"], False)
        
        # Verify correct counts
        self.assertEqual(success_count, 2)
        self.assertEqual(len(failed_names), 0)
        
        # Verify they're removed
        favorites = self.manager.list_favorites()
        self.assertEqual(len(favorites), 1)
        favorite_names = [s.name for s in favorites]
        self.assertNotIn("test3", favorite_names)
        self.assertIn("test4", favorite_names)
        self.assertNotIn("test5", favorite_names)
        
        # Test with non-existent search
        success_count, failed_names = self.manager.batch_toggle_favorite(["nonexistent"], True)
        self.assertEqual(success_count, 0)
        self.assertEqual(len(failed_names), 1)
        self.assertEqual(failed_names[0], "nonexistent")
    
    def test_batch_operations(self):
        """Test batch operations with mocks."""
        # Test batch delete
        success_count, failed_names = self.manager.batch_delete(["test1", "test2"])
        
        # Verify correct counts
        self.assertEqual(success_count, 2)
        self.assertEqual(len(failed_names), 0)
        
        # Verify searches are deleted
        searches = self.manager.list_searches()
        self.assertEqual(len(searches), 3)
        search_names = [s.name for s in searches]
        self.assertNotIn("test1", search_names)
        self.assertNotIn("test2", search_names)
        self.assertIn("test3", search_names)
        
        # Test batch categorize
        category = "important"
        success_count, failed_names = self.manager.batch_categorize(["test3", "test4"], category)
        
        # Verify correct counts
        self.assertEqual(success_count, 2)
        self.assertEqual(len(failed_names), 0)
        
        # Verify categories
        test3 = self.manager.get_search("test3")
        test4 = self.manager.get_search("test4")
        test5 = self.manager.get_search("test5")
        
        self.assertEqual(test3.category, category)
        self.assertEqual(test4.category, category)
        self.assertNotEqual(test5.category, category)
        
        # Test batch add tags
        new_tags = ["featured", "important"]
        success_count, failed_names = self.manager.batch_add_tags(["test3", "test4"], new_tags)
        
        # Verify correct counts
        self.assertEqual(success_count, 2)
        self.assertEqual(len(failed_names), 0)
        
        # Verify tags
        test3 = self.manager.get_search("test3")
        test4 = self.manager.get_search("test4")
        
        for tag in new_tags:
            self.assertIn(tag, test3.tags)
            self.assertIn(tag, test4.tags)
        
        # Test batch remove tags
        success_count, failed_names = self.manager.batch_remove_tags(["test5"], ["urgent"])
        
        # Verify correct counts
        self.assertEqual(success_count, 1)
        self.assertEqual(len(failed_names), 0)
        
        # Verify tag is removed
        test5 = self.manager.get_search("test5")
        self.assertNotIn("urgent", test5.tags)
        
        # Test with non-existent search
        success_count, failed_names = self.manager.batch_categorize(["nonexistent"], "category")
        self.assertEqual(success_count, 0)
        self.assertEqual(len(failed_names), 1)
        self.assertEqual(failed_names[0], "nonexistent")


if __name__ == "__main__":
    unittest.main() 