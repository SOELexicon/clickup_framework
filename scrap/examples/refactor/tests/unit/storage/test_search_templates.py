"""
Unit tests for search template functionality in SavedSearchesManager.

This module tests the template-related methods in the SavedSearchesManager class, including:
- Creating search templates with variables
- Updating templates
- Extracting variables from template queries
- Substituting variables in queries
- Executing search templates
"""

import unittest
import tempfile
import os
from unittest.mock import patch

from refactor.storage.saved_searches import SavedSearchesManager, SavedSearch


class TestSearchTemplates(unittest.TestCase):
    """Test cases for template functionality in SavedSearchesManager."""
    
    def setUp(self):
        """Set up a temporary directory for test files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = self.temp_dir.name
        
        # Create a manager instance with the test storage directory
        self.manager = SavedSearchesManager(storage_dir=self.storage_dir)
    
    def tearDown(self):
        """Clean up temporary directory after tests."""
        self.temp_dir.cleanup()
    
    def test_create_template(self):
        """Test creating a search template with variables."""
        name = "test-template"
        query = "status == '${status}' and priority >= ${min_priority}"
        
        # Create the template
        template = self.manager.save_search(
            name=name,
            query=query,
            description="Test template",
            is_template=True
        )
        
        # Verify it was created as a template
        self.assertTrue(template.is_template)
        
        # Verify variables were extracted
        self.assertEqual(set(template.variables), {"status", "min_priority"})
        
        # Verify it was persisted
        template2 = self.manager.get_search(name)
        self.assertTrue(template2.is_template)
        self.assertEqual(set(template2.variables), {"status", "min_priority"})
    
    def test_create_template_with_explicit_variables(self):
        """Test creating a template with explicitly provided variables."""
        name = "explicit-var-template"
        query = "status == '${status}' and priority >= ${min_priority}"
        variables = ["status", "custom_var"]  # Deliberately different from what's in the query
        
        # Create the template with explicit variables
        template = self.manager.save_search(
            name=name,
            query=query,
            is_template=True,
            variables=variables
        )
        
        # Verify the explicit variables were used, not the extracted ones
        self.assertEqual(set(template.variables), set(variables))
    
    def test_variable_extraction(self):
        """Test extracting variables from a query string."""
        query = "name contains '${search_text}' and status in [${status1}, ${status2}] and ${other_field} > 0"
        
        # Create a temporary template to use the _extract_variables method
        template = SavedSearch("test", query, is_template=True)
        
        # Verify variables were correctly extracted
        expected_vars = {"search_text", "status1", "status2", "other_field"}
        self.assertEqual(set(template.variables), expected_vars)
    
    def test_update_template(self):
        """Test updating a search template."""
        # Create initial template
        name = "update-test"
        query = "status == '${status}'"
        
        template = self.manager.save_search(
            name=name,
            query=query,
            is_template=True
        )
        
        # Update the template with a new query
        new_query = "status == '${status}' and priority >= ${min_priority}"
        self.manager.update_search(
            name=name,
            query=new_query
        )
        
        # Verify template was updated and variables extracted from new query
        updated = self.manager.get_search(name)
        self.assertEqual(updated.query, new_query)
        self.assertEqual(set(updated.variables), {"status", "min_priority"})
    
    def test_convert_regular_search_to_template(self):
        """Test converting a regular search to a template."""
        # Create a regular search
        name = "convert-test"
        query = "status == 'in progress'"
        
        self.manager.save_search(
            name=name,
            query=query,
            is_template=False
        )
        
        # Convert to template
        template_query = "status == '${status}'"
        self.manager.update_search(
            name=name,
            query=template_query,
            is_template=True
        )
        
        # Verify it was converted to a template
        template = self.manager.get_search(name)
        self.assertTrue(template.is_template)
        self.assertEqual(template.query, template_query)
        self.assertEqual(template.variables, ["status"])
    
    def test_substitute_variables(self):
        """Test substituting variables in a template query."""
        # Create a template
        name = "substitute-test"
        query = "status == '${status}' and priority >= ${min_priority}"
        
        template = self.manager.save_search(
            name=name,
            query=query,
            is_template=True
        )
        
        # Substitute variables
        variables = {
            "status": "in progress",
            "min_priority": "3"
        }
        
        # Test the substitute_variables method directly
        result = template.substitute_variables(variables)
        
        # Verify variables were substituted
        expected = "status == 'in progress' and priority >= 3"
        self.assertEqual(result, expected)
    
    def test_execute_template(self):
        """Test executing a search template."""
        # Create a template
        name = "execute-test"
        query = "status == '${status}' and priority >= ${min_priority}"
        
        self.manager.save_search(
            name=name,
            query=query,
            is_template=True
        )
        
        # Execute the template
        variables = {
            "status": "in progress",
            "min_priority": "3"
        }
        
        result_query, used_vars = self.manager.execute_search_template(name, variables)
        
        # Verify the correct query was returned
        expected = "status == 'in progress' and priority >= 3"
        self.assertEqual(result_query, expected)
        
        # Verify the variables used were returned
        self.assertEqual(used_vars, variables)
    
    def test_execute_template_with_missing_variable(self):
        """Test that executing a template with missing variables raises an error."""
        # Create a template
        name = "missing-var-test"
        query = "status == '${status}' and priority >= ${min_priority}"
        
        self.manager.save_search(
            name=name,
            query=query,
            is_template=True
        )
        
        # Try to execute with missing variable
        variables = {
            "status": "in progress"
            # min_priority is missing
        }
        
        # Verify it raises the appropriate error
        with self.assertRaises(ValueError) as context:
            self.manager.execute_search_template(name, variables)
        
        self.assertIn("Missing value for template variable", str(context.exception))
        self.assertIn("min_priority", str(context.exception))
    
    def test_execute_non_template(self):
        """Test that executing a non-template raises an error."""
        # Create a regular search
        name = "not-a-template"
        query = "status == 'in progress'"
        
        self.manager.save_search(
            name=name,
            query=query,
            is_template=False
        )
        
        # Try to execute it as a template
        variables = {"some_var": "value"}
        
        # Verify it raises the appropriate error
        with self.assertRaises(ValueError) as context:
            self.manager.execute_search_template(name, variables)
        
        self.assertIn("is not a template", str(context.exception))
    
    def test_list_templates(self):
        """Test listing search templates."""
        # Create a mix of regular searches and templates
        self.manager.save_search(
            name="regular1",
            query="status == 'in progress'",
            is_template=False
        )
        
        self.manager.save_search(
            name="template1",
            query="status == '${status}'",
            is_template=True,
            category="templates"
        )
        
        self.manager.save_search(
            name="regular2",
            query="priority >= 3",
            is_template=False
        )
        
        self.manager.save_search(
            name="template2",
            query="priority >= ${min_priority}",
            is_template=True,
            category="filters"
        )
        
        # List templates
        templates = self.manager.list_templates()
        
        # Verify only templates are returned
        self.assertEqual(len(templates), 2)
        template_names = {t.name for t in templates}
        self.assertEqual(template_names, {"template1", "template2"})
        
        # Test filtering by category
        templates_in_category = self.manager.list_templates(category="templates")
        self.assertEqual(len(templates_in_category), 1)
        self.assertEqual(templates_in_category[0].name, "template1")


if __name__ == "__main__":
    unittest.main() 