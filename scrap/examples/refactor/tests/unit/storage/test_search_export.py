"""
Unit tests for the SearchExportController class.
"""

import os
import unittest
import tempfile
import shutil
import json
from typing import Dict, List, Any

from refactor.storage.saved_searches import SavedSearchesManager, SavedSearch
from refactor.storage.export_controller import SearchExportController
from refactor.common.json_utils import NewlineEncoderDecoder


class TestSearchExportController(unittest.TestCase):
    """Test case for the SearchExportController class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        # Create a SavedSearchesManager with the test directory
        self.manager = SavedSearchesManager(storage_dir=self.test_dir)
        # Create the export controller
        self.controller = SearchExportController(manager=self.manager)
        
        # Create test searches with different properties
        self.manager.save_search("test1", "status == 'complete'", category="status", tags=["complete"])
        self.manager.save_search("test2", "priority >= 3", category="priority", tags=["high"])
        self.manager.save_search("test3", "tags contains 'urgent'", category="tags", tags=["urgent"])
        self.manager.save_search("test4", "assignee == 'me'", category="assignee", tags=["personal"])
        self.manager.save_search("test5", "due_date < today()", category="date", tags=["urgent"])
        
        # Create a template
        self.manager.save_template(
            "template1", 
            "status == '${status}'", 
            variables=["status"],
            category="templates",
            tags=["template", "status"]
        )
        
        # Mark some searches as favorites
        self.manager.add_to_favorites("test1")
        self.manager.add_to_favorites("test3")
        self.manager.add_to_favorites("template1")
        
    def tearDown(self):
        """Clean up test fixtures after each test method."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)
    
    def test_export_all_searches(self):
        """Test exporting all searches."""
        # Export all searches
        json_data = self.controller.export_searches(include_templates=True)
        
        # Parse the exported data
        export_data = NewlineEncoderDecoder.decode(json_data)
        
        # Verify the export contains all searches
        self.assertEqual(export_data["count"], 6)
        
        # Check if all search names are present
        search_names = [s["name"] for s in export_data["searches"]]
        expected_names = ["test1", "test2", "test3", "test4", "test5", "template1"]
        for name in expected_names:
            self.assertIn(name, search_names)
    
    def test_export_favorites_only(self):
        """Test exporting only favorite searches."""
        # Export only favorites
        json_data = self.controller.export_searches(favorites_only=True, include_templates=True)
        
        # Parse the exported data
        export_data = NewlineEncoderDecoder.decode(json_data)
        
        # Verify the export contains only favorites
        self.assertEqual(export_data["count"], 3)
        
        # Check if only favorite search names are present
        search_names = [s["name"] for s in export_data["searches"]]
        expected_names = ["test1", "test3", "template1"]
        unexpected_names = ["test2", "test4", "test5"]
        
        for name in expected_names:
            self.assertIn(name, search_names)
        
        for name in unexpected_names:
            self.assertNotIn(name, search_names)
        
        # Verify favorite flag is preserved in export
        for search in export_data["searches"]:
            self.assertTrue(search["is_favorite"])
    
    def test_export_to_file(self):
        """Test exporting searches to a file."""
        # Create a temporary file path
        fd, output_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)  # Close the file descriptor
        
        try:
            # Export to file
            self.controller.export_searches(
                output_path=output_path,
                favorites_only=True,
                include_templates=True
            )
            
            # Read the file
            with open(output_path, 'r') as f:
                file_data = f.read()
            
            # Parse the file data
            export_data = NewlineEncoderDecoder.decode(file_data)
            
            # Verify file contains the correct data
            self.assertEqual(export_data["count"], 3)
            search_names = [s["name"] for s in export_data["searches"]]
            expected_names = ["test1", "test3", "template1"]
            for name in expected_names:
                self.assertIn(name, search_names)
        finally:
            # Clean up
            os.unlink(output_path)
    
    def test_export_favorites_no_templates(self):
        """Test exporting favorites without templates."""
        # Export favorites without templates
        json_data = self.controller.export_searches(
            favorites_only=True,
            include_templates=False
        )
        
        # Parse the exported data
        export_data = NewlineEncoderDecoder.decode(json_data)
        
        # Verify the export contains only non-template favorites
        self.assertEqual(export_data["count"], 2)
        
        # Check if only non-template favorite search names are present
        search_names = [s["name"] for s in export_data["searches"]]
        expected_names = ["test1", "test3"]
        self.assertIn("test1", search_names)
        self.assertIn("test3", search_names)
        self.assertNotIn("template1", search_names)
    
    def test_export_templates_only(self):
        """Test exporting only templates."""
        # Export only templates
        json_data = self.controller.export_searches(templates_only=True)
        
        # Parse the exported data
        export_data = NewlineEncoderDecoder.decode(json_data)
        
        # Verify the export contains only templates
        self.assertEqual(export_data["count"], 1)
        
        # Check if only template names are present
        search_names = [s["name"] for s in export_data["searches"]]
        self.assertIn("template1", search_names)
        self.assertNotIn("test1", search_names)
        self.assertNotIn("test2", search_names)
    
    def test_export_favorite_templates_only(self):
        """Test exporting only favorite templates."""
        # Export only favorite templates
        json_data = self.controller.export_searches(
            favorites_only=True,
            templates_only=True
        )
        
        # Parse the exported data
        export_data = NewlineEncoderDecoder.decode(json_data)
        
        # Verify the export contains only favorite templates
        self.assertEqual(export_data["count"], 1)
        
        # Check if only favorite template names are present
        search_names = [s["name"] for s in export_data["searches"]]
        self.assertIn("template1", search_names)
        self.assertNotIn("test1", search_names)
        self.assertNotIn("test3", search_names)
    
    def test_export_with_category_filter(self):
        """Test exporting with category filter."""
        # Export searches in "tags" category
        json_data = self.controller.export_searches(category="tags")
        
        # Parse the exported data
        export_data = NewlineEncoderDecoder.decode(json_data)
        
        # Verify the export contains only searches in "tags" category
        self.assertEqual(export_data["count"], 1)
        
        # Check if only searches in "tags" category are present
        search_names = [s["name"] for s in export_data["searches"]]
        self.assertIn("test3", search_names)
        self.assertNotIn("test1", search_names)
        self.assertNotIn("test2", search_names)
    
    def test_export_with_tag_filter(self):
        """Test exporting with tag filter."""
        # Export searches with "urgent" tag
        json_data = self.controller.export_searches(tag="urgent")
        
        # Parse the exported data
        export_data = NewlineEncoderDecoder.decode(json_data)
        
        # Verify the export contains only searches with "urgent" tag
        self.assertEqual(export_data["count"], 2)
        
        # Check if only searches with "urgent" tag are present
        search_names = [s["name"] for s in export_data["searches"]]
        self.assertIn("test3", search_names)
        self.assertIn("test5", search_names)
        self.assertNotIn("test1", search_names)
        self.assertNotIn("test2", search_names)
    
    def test_export_favorite_with_tag_filter(self):
        """Test exporting favorites with tag filter."""
        # Export favorite searches with "urgent" tag
        json_data = self.controller.export_searches(
            favorites_only=True,
            tag="urgent"
        )
        
        # Parse the exported data
        export_data = NewlineEncoderDecoder.decode(json_data)
        
        # Verify the export contains only favorite searches with "urgent" tag
        self.assertEqual(export_data["count"], 1)
        
        # Check if only favorite searches with "urgent" tag are present
        search_names = [s["name"] for s in export_data["searches"]]
        self.assertIn("test3", search_names)
        self.assertNotIn("test1", search_names)
        self.assertNotIn("test5", search_names)
        

if __name__ == "__main__":
    unittest.main() 