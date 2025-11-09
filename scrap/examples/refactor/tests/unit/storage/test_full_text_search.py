"""
Test full-text search functionality.

This module tests the FullTextSearchIndex and FullTextSearchManager
classes to ensure that the full-text search functionality works correctly.
"""

import os
import json
import tempfile
import unittest
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock, patch
import re

from refactor.storage.full_text_search import FullTextSearchIndex, FullTextSearchManager, TaskJsonRepository
from refactor.core.entities.task_entity import TaskEntity, TaskStatus, TaskPriority


class TestFullTextSearchIndex(unittest.TestCase):
    """Test cases for the FullTextSearchIndex class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for the index
        self.temp_dir = tempfile.mkdtemp()
        
        # Create an index with the temporary directory
        self.index = FullTextSearchIndex(self.temp_dir)
        
        # Test tasks
        self.tasks = [
            {
                "id": "task1",
                "name": "Implement full-text search",
                "description": "Implement a robust full-text search feature for tasks",
                "status": "in progress",
                "priority": 2,
                "tags": ["search", "feature"],
                "comments": [
                    {"text": "Started working on this", "author": "Alice"},
                    {"text": "Using inverted index for efficient searching", "author": "Bob"}
                ],
                "updated_at": "2023-01-01T00:00:00"
            },
            {
                "id": "task2",
                "name": "Fix bug in task management",
                "description": "There's a bug when updating task status",
                "status": "to do",
                "priority": 1,
                "tags": ["bug", "high-priority"],
                "comments": [
                    {"text": "This is critical", "author": "Charlie"}
                ],
                "updated_at": "2023-01-02T00:00:00"
            },
            {
                "id": "task3",
                "name": "Improve UI design",
                "description": "Make the UI more user-friendly",
                "status": "to do",
                "priority": 3,
                "tags": ["UI", "enhancement"],
                "comments": [],
                "updated_at": "2023-01-03T00:00:00"
            }
        ]
    
    def tearDown(self):
        """Clean up after the test."""
        # Remove the index file if it exists
        index_path = os.path.join(self.temp_dir, "full_text_index.json")
        if os.path.exists(index_path):
            os.remove(index_path)
        
        # Remove the temporary directory
        os.rmdir(self.temp_dir)
    
    def test_tokenize(self):
        """Test the tokenization of text."""
        text = "Hello, world! This is a test."
        tokens = self.index._tokenize(text)
        
        # Expected tokens (without stop words)
        expected = [
            ("hello", 0),
            ("world", 1),
            ("test", 4)
        ]
        
        self.assertEqual(tokens, expected)
    
    def test_extract_text_from_field(self):
        """Test extraction of text from different field types."""
        task = self.tasks[0]
        
        # Test extraction from string field
        name_text = self.index._extract_text_from_field(task, "name")
        self.assertEqual(name_text, "Implement full-text search")
        
        # Test extraction from tags list
        tags_text = self.index._extract_text_from_field(task, "tags")
        self.assertEqual(tags_text, "search feature")
        
        # Test extraction from comments list
        comments_text = self.index._extract_text_from_field(task, "comments")
        self.assertIn("Started working on this", comments_text)
        self.assertIn("Using inverted index for efficient searching", comments_text)
    
    def test_index_task(self):
        """Test indexing a single task."""
        # Index a task
        self.index.index_task(self.tasks[0])
        
        # Check that the task was indexed
        self.assertEqual(self.index.document_count, 1)
        self.assertIn("task1", self.index.indexed_tasks)
        
        # Check that specific terms were indexed
        self.assertIn("implement", self.index.inverted_index)
        self.assertIn("search", self.index.inverted_index)
        self.assertIn("feature", self.index.inverted_index)
        
        # Check that term frequencies were calculated
        self.assertIn("implement", self.index.document_term_counts["task1"]["name"])
        self.assertIn("search", self.index.document_term_counts["task1"]["tags"])
    
    def test_index_tasks(self):
        """Test indexing multiple tasks."""
        # Index multiple tasks
        self.index.index_tasks(self.tasks)
        
        # Check that all tasks were indexed
        self.assertEqual(self.index.document_count, 3)
        for task in self.tasks:
            self.assertIn(task["id"], self.index.indexed_tasks)
    
    def test_remove_task(self):
        """Test removing a task from the index."""
        # Index tasks
        self.index.index_tasks(self.tasks)
        
        # Remove a task
        self.index.remove_task("task1")
        
        # Check that the task was removed
        self.assertEqual(self.index.document_count, 2)
        self.assertNotIn("task1", self.index.indexed_tasks)
        
        # Check that task1's terms were removed from the inverted index
        for term in ["implement", "full-text", "search"]:
            if term in self.index.inverted_index:
                self.assertNotIn("task1", self.index.inverted_index[term])
    
    def test_search(self):
        """Test searching for tasks."""
        # Index tasks
        self.index.index_tasks(self.tasks)
        
        # Search for "search"
        results = self.index.search("search")
        
        # Check that task1 is in the results
        self.assertTrue(any(task_id == "task1" for task_id, _ in results))
        
        # Search for "bug"
        results = self.index.search("bug")
        
        # Check that task2 is in the results
        self.assertTrue(any(task_id == "task2" for task_id, _ in results))
        
        # Search for "UI design"
        results = self.index.search("UI design")
        
        # Check that task3 is in the results
        self.assertTrue(any(task_id == "task3" for task_id, _ in results))
    
    def test_search_with_fields(self):
        """Test searching in specific fields."""
        # Index tasks
        self.index.index_tasks(self.tasks)
        
        # Search for "search" in name field
        results = self.index.search("search", fields=["name"])
        
        # Check that task1 is in the results
        self.assertTrue(any(task_id == "task1" for task_id, _ in results))
        
        # Search for "critical" in comments field
        results = self.index.search("critical", fields=["comments"])
        
        # Check that task2 is in the results
        self.assertTrue(any(task_id == "task2" for task_id, _ in results))
    
    def test_save_and_load_index(self):
        """Test saving and loading the index."""
        # Index tasks
        self.index.index_tasks(self.tasks)
        
        # Save the index
        self.index._save_index()
        
        # Create a new index and load from disk
        new_index = FullTextSearchIndex(self.temp_dir)
        
        # Check that the indexes match
        self.assertEqual(new_index.document_count, self.index.document_count)
        for task_id in self.index.indexed_tasks:
            self.assertIn(task_id, new_index.indexed_tasks)

    def test_highlight_field(self):
        """Test highlighting matched terms in text."""
        # Test basic highlighting
        text = "This is a sample text with important keywords"
        highlighted = self.index.highlight_field(text, ["sample", "keywords"])
        
        # Assert that the terms are highlighted with ANSI color codes
        self.assertIn("\033[1;31msample\033[0m", highlighted)
        self.assertIn("\033[1;31mkeywords\033[0m", highlighted)
        
        # Test case insensitivity
        text = "This is a SAMPLE text"
        highlighted = self.index.highlight_field(text, ["sample"])
        self.assertIn("\033[1;31mSAMPLE\033[0m", highlighted)
        
        # Test whole word matching
        text = "example sample examples"
        highlighted = self.index.highlight_field(text, ["sample"])
        self.assertEqual("example \033[1;31msample\033[0m examples", highlighted)
        
        # Test empty query or text
        self.assertEqual(self.index.highlight_field("", ["term"]), "")
        self.assertEqual(self.index.highlight_field("text", []), "text")

    def test_extract_context(self):
        """Test extracting context around matched terms."""
        # Test basic context extraction
        text = "This is a very long text with multiple paragraphs. " * 10
        text += "Here is an important keyword that should be found. "
        text += "This is more text that follows the keyword. " * 10
        
        context = self.index.extract_context(text, ["important", "keyword"], context_size=20)
        
        # Context should contain both terms with some surrounding text
        self.assertIn("important", context)
        self.assertIn("keyword", context)
        # Context should be shorter than original text
        self.assertLess(len(context), len(text))
        
        # Test context extraction with no matches
        text = "This text doesn't contain any matches."
        context = self.index.extract_context(text, ["nonexistent"], context_size=10)
        # Should return beginning of text or whole text if short
        self.assertEqual(context, text)
        
        # Test context merging with overlapping matches
        text = "First keyword is close to second keyword in this text."
        context = self.index.extract_context(text, ["first", "second"], context_size=10)
        # Both matches should be in same context due to proximity
        self.assertIn("First", context)
        self.assertIn("second", context)
        self.assertLessEqual(len(context.split("...")), 3)  # At most one split with ellipsis

    def test_search_with_highlighting(self):
        """Test search with highlighting feature."""
        # Create a task repository and search manager
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a repository with test data
            repo_file = os.path.join(tmpdir, "tasks.json")
            repo = TaskJsonRepository(repo_file)
            
            # Add sample tasks
            task1 = {
                "id": "task1",
                "name": "Important task with keywords",
                "description": "This is a detailed description with important information.",
                "status": "to do",
                "tags": ["important", "keyword"],
                "comments": [{"text": "This comment mentions keywords and is important."}]
            }
            
            task2 = {
                "id": "task2",
                "name": "Another task",
                "description": "This description does not have relevant terms.",
                "status": "in progress",
                "tags": ["other"],
                "comments": []
            }
            
            repo.save_task(task1)
            repo.save_task(task2)
            
            # Create the search manager and build index
            search_manager = FullTextSearchManager(repo, os.path.join(tmpdir, "index"))
            search_manager.rebuild_index()
            
            # Search with highlighting
            results = search_manager.search("important keywords", highlight=True)
            
            # Verify results
            self.assertGreater(len(results), 0)
            self.assertIn("task", results[0])
            self.assertIn("score", results[0])
            self.assertIn("highlighted_fields", results[0])
            
            # Check that highlighting was applied
            highlighted_fields = results[0]["highlighted_fields"]
            self.assertIn("name", highlighted_fields)
            self.assertIn("\033[1;31m", highlighted_fields["name"])  # Contains ANSI color codes

    def test_regex_search(self):
        """Test searching using regular expressions."""
        # Index the test tasks
        self.index.index_tasks(self.tasks)
        
        # Search for tasks with regex pattern "^Implement.*search$"
        results = self.index.regex_search("^Implement.*search$")
        
        # Check that task1 is in the results (matches "Implement full-text search")
        self.assertTrue(any(task_id == "task1" for task_id, _ in results))
        
        # Task2 and task3 should not match
        self.assertFalse(any(task_id == "task2" for task_id, _ in results))
        self.assertFalse(any(task_id == "task3" for task_id, _ in results))
        
        # Search for "bug.*status" - should match task2's description
        results = self.index.regex_search("bug.*status")
        self.assertTrue(any(task_id == "task2" for task_id, _ in results))
        
        # Search for "UI|user-friendly" - should match task3
        results = self.index.regex_search("UI|user-friendly")
        self.assertTrue(any(task_id == "task3" for task_id, _ in results))
        
        # Test with specific fields
        results = self.index.regex_search("critical", fields=["comments"])
        self.assertTrue(any(task_id == "task2" for task_id, _ in results))
        
        # Test with invalid regex
        with self.assertLogs(level='ERROR'):
            results = self.index.regex_search("(unclosed[parenthesis")
            self.assertEqual(len(results), 0)
    
    def test_levenshtein_distance(self):
        """Test the Levenshtein distance calculation."""
        # Test exact match
        self.assertEqual(self.index._levenshtein_distance("test", "test"), 0)
        
        # Test one character different
        self.assertEqual(self.index._levenshtein_distance("test", "text"), 1)
        
        # Test one character extra
        self.assertEqual(self.index._levenshtein_distance("test", "tests"), 1)
        
        # Test one character missing
        self.assertEqual(self.index._levenshtein_distance("test", "tes"), 1)
        
        # Test completely different strings
        self.assertEqual(self.index._levenshtein_distance("test", "exam"), 4)
        
        # Test empty strings
        self.assertEqual(self.index._levenshtein_distance("", ""), 0)
        self.assertEqual(self.index._levenshtein_distance("test", ""), 4)
        self.assertEqual(self.index._levenshtein_distance("", "test"), 4)
    
    def test_fuzzy_search(self):
        """Test searching with fuzzy matching."""
        # Index the test tasks
        self.index.index_tasks(self.tasks)
        
        # Search for "implment" (misspelled "implement")
        results = self.index.fuzzy_search("implment", max_distance=2)
        
        # Check that task1 is in the results (contains "implement" which is similar)
        self.assertTrue(any(task_id == "task1" for task_id, _ in results))
        
        # Search for "serch" (misspelled "search")
        results = self.index.fuzzy_search("serch", max_distance=1)
        self.assertTrue(any(task_id == "task1" for task_id, _ in results))
        
        # Search for "uzer-frendly" (misspelled "user-friendly")
        results = self.index.fuzzy_search("uzer-frendly", max_distance=3)
        self.assertTrue(any(task_id == "task3" for task_id, _ in results))
        
        # Test with specific fields
        results = self.index.fuzzy_search("critikal", max_distance=2, fields=["comments"])
        self.assertTrue(any(task_id == "task2" for task_id, _ in results))
        
        # Test with max_distance=0 (should work like exact search)
        results = self.index.fuzzy_search("bug", max_distance=0)
        self.assertTrue(any(task_id == "task2" for task_id, _ in results))
        
        # Test with non-matching query
        results = self.index.fuzzy_search("xyzabc", max_distance=2)
        self.assertEqual(len(results), 0)


class TestFullTextSearchManager(unittest.TestCase):
    """Test cases for the FullTextSearchManager class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a mock task repository
        self.task_repository = MagicMock()
        
        # Create a temporary directory for the index
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a search manager with the mock repository
        self.search_manager = FullTextSearchManager(self.task_repository, self.temp_dir)
        
        # Test tasks
        self.tasks = [
            TaskEntity(
                entity_id="task1",
                name="Implement full-text search",
                description="Implement a robust full-text search feature for tasks",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                tags=["search", "feature"]
            ),
            TaskEntity(
                entity_id="task2",
                name="Fix bug in task management",
                description="There's a bug when updating task status",
                status=TaskStatus.TO_DO,
                priority=TaskPriority.URGENT,
                tags=["bug", "high-priority"]
            ),
            TaskEntity(
                entity_id="task3",
                name="Improve UI design",
                description="Make the UI more user-friendly",
                status=TaskStatus.TO_DO,
                priority=TaskPriority.NORMAL,
                tags=["UI", "enhancement"]
            )
        ]
        
        # Add comments to tasks
        self.tasks[0].add_comment("Started working on this", "Alice")
        self.tasks[0].add_comment("Using inverted index for efficient searching", "Bob")
        self.tasks[1].add_comment("This is critical", "Charlie")
    
    def tearDown(self):
        """Clean up after the test."""
        # Remove the index file if it exists
        index_path = os.path.join(self.temp_dir, "full_text_index.json")
        if os.path.exists(index_path):
            os.remove(index_path)
        
        # Remove the temporary directory
        os.rmdir(self.temp_dir)
    
    def test_index_task(self):
        """Test indexing a task by ID."""
        # Set up the repository mock to return a task
        self.task_repository.get_by_id.return_value = self.tasks[0]
        
        # Index the task
        self.search_manager.index_task("task1")
        
        # Check that the repository was called
        self.task_repository.get_by_id.assert_called_once_with("task1")
        
        # Check that the task was indexed (indirectly)
        self.assertEqual(self.search_manager.index.document_count, 1)
    
    def test_rebuild_index(self):
        """Test rebuilding the index."""
        # Set up the repository mock to return all tasks
        self.task_repository.get_all.return_value = self.tasks
        
        # Rebuild the index
        self.search_manager.rebuild_index()
        
        # Check that the repository was called
        self.task_repository.get_all.assert_called_once()
        
        # Check that all tasks were indexed
        self.assertEqual(self.search_manager.index.document_count, 3)
    
    def test_search(self):
        """Test searching for tasks."""
        # Create a temporary index with test data
        with patch.object(self.search_manager.index, "search") as mock_search:
            # Set up the mock to return task IDs
            mock_search.return_value = [("task1", 0.8), ("task3", 0.5)]
            
            # Set up the repository mock to return tasks
            self.task_repository.get_by_id.side_effect = lambda task_id: next(
                (task for task in self.tasks if task.id == task_id), None
            )
            
            # Search for tasks
            results = self.search_manager.search("search")
            
            # Check that the search was called with the right parameters
            mock_search.assert_called_once_with("search", None, 50)
            
            # Check that the repository was called for each task
            self.assertEqual(self.task_repository.get_by_id.call_count, 2)
            
            # Check that the results match the expected tasks
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0].id, "task1")
            self.assertEqual(results[1].id, "task3")
    
    def test_update_task(self):
        """Test updating a task in the index."""
        # Set up the repository mock to return a task
        self.task_repository.get_by_id.return_value = self.tasks[0]
        
        # Update the task
        self.search_manager.update_task("task1")
        
        # Check that the repository was called
        self.task_repository.get_by_id.assert_called_once_with("task1")
        
        # Check that the task was indexed
        self.assertEqual(self.search_manager.index.document_count, 1)
    
    def test_remove_task(self):
        """Test removing a task from the index."""
        # First index a task
        with patch.object(self.search_manager.index, "index_task"):
            self.task_repository.get_by_id.return_value = self.tasks[0]
            self.search_manager.index_task("task1")
        
        # Then remove it
        with patch.object(self.search_manager.index, "remove_task") as mock_remove:
            self.search_manager.remove_task("task1")
            
            # Check that the index's remove_task was called
            mock_remove.assert_called_once_with("task1")

    def test_regex_search(self):
        """Test regex search in the manager."""
        # Create a temporary index with test data
        with patch.object(self.search_manager.search_index, "regex_search") as mock_search:
            # Set up the mock to return task IDs
            mock_search.return_value = [("task1", 0.8), ("task3", 0.5)]
            
            # Set up the repository mock to return tasks
            self.task_repository.get_task.side_effect = lambda task_id: next(
                (task for task in self.tasks if task.id == task_id), None
            )
            
            # Search for tasks with regex
            results = self.search_manager.regex_search("^Implement.*")
            
            # Check that the search was called with the right parameters
            mock_search.assert_called_once_with("^Implement.*", None, 10)
            
            # Check that the repository was called for each task
            self.assertEqual(self.task_repository.get_task.call_count, 2)
            
            # Check that the results contain the expected tasks
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["task"].id, "task1")
            self.assertEqual(results[1]["task"].id, "task3")
            
            # Test with highlighting
            mock_search.reset_mock()
            self.task_repository.get_task.reset_mock()
            
            # Set up repository to return dictionary version of tasks
            self.task_repository.get_task.side_effect = lambda task_id: next(
                (task.to_dict() for task in self.tasks if task.id == task_id), None
            )
            
            results = self.search_manager.regex_search("^Implement.*", highlight=True)
            
            # Check that highlighted fields were extracted
            self.assertGreaterEqual(len(results), 1)
            # There may or may not be highlighted fields depending on the regex match
    
    def test_highlight_regex_matches(self):
        """Test highlighting of regex matches."""
        # Test basic regex highlighting
        text = "This is a test for regex matching"
        regex = re.compile(r"test|regex")
        highlighted = self.search_manager._highlight_regex_matches(text, regex)
        
        # Check that "test" and "regex" are highlighted
        self.assertIn("\033[1;31mtest\033[0m", highlighted)
        self.assertIn("\033[1;31mregex\033[0m", highlighted)
        
        # Test with no matches
        regex = re.compile(r"nonexistent")
        highlighted = self.search_manager._highlight_regex_matches(text, regex)
        self.assertEqual(highlighted, text)
        
        # Test with empty text
        self.assertEqual(self.search_manager._highlight_regex_matches("", regex), "")
    
    def test_fuzzy_search(self):
        """Test fuzzy search in the manager."""
        # Create a temporary index with test data
        with patch.object(self.search_manager.search_index, "fuzzy_search") as mock_search:
            # Set up the mock to return task IDs
            mock_search.return_value = [("task1", 0.8), ("task2", 0.5)]
            
            # Set up the repository mock to return tasks
            self.task_repository.get_task.side_effect = lambda task_id: next(
                (task for task in self.tasks if task.id == task_id), None
            )
            
            # Search for tasks with fuzzy matching
            results = self.search_manager.fuzzy_search("implment", max_distance=2)
            
            # Check that the search was called with the right parameters
            mock_search.assert_called_once_with("implment", None, 2, 10)
            
            # Check that the repository was called for each task
            self.assertEqual(self.task_repository.get_task.call_count, 2)
            
            # Check that the results match the expected tasks
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["task"].id, "task1")
            self.assertEqual(results[1]["task"].id, "task2")
            
            # Test with highlighting
            mock_search.reset_mock()
            self.task_repository.get_task.reset_mock()
            
            # Set up repository to return dictionary version of tasks
            self.task_repository.get_task.side_effect = lambda task_id: next(
                (task.to_dict() for task in self.tasks if task.id == task_id), None
            )
            
            results = self.search_manager.fuzzy_search("implment", max_distance=2, highlight=True)
            
            # Check that the results were returned
            self.assertGreaterEqual(len(results), 1)
            # There may or may not be highlighted fields depending on the fuzzy matches
    
    def test_highlight_fuzzy_matches(self):
        """Test highlighting of fuzzy matches."""
        # Test basic fuzzy matching highlighting
        text = "This is a test for fuzzy matching"
        tokens = text.split()
        query_terms = ["tast", "fuzy"] # Misspelled versions of "test" and "fuzzy"
        
        highlighted = self.search_manager._highlight_fuzzy_matches(text, tokens, query_terms, 1)
        
        # Check that "test" and "fuzzy" are highlighted (they match within distance 1)
        self.assertIn("\033[1;31mtest\033[0m", highlighted)
        self.assertIn("\033[1;31mfuzzy\033[0m", highlighted)
        
        # Test with no matches
        highlighted = self.search_manager._highlight_fuzzy_matches(text, tokens, ["xyz", "abc"], 1)
        self.assertEqual(highlighted, text)
        
        # Test with empty text or tokens
        self.assertEqual(self.search_manager._highlight_fuzzy_matches("", [], query_terms, 1), "")
        self.assertEqual(self.search_manager._highlight_fuzzy_matches(text, [], query_terms, 1), text)


if __name__ == "__main__":
    unittest.main() 