"""
Checklist Index Mapping Manager

Provides index-to-UUID mapping for checklists and checklist items, allowing users
to reference checklists by simple numeric indices (1, 2, 3) instead of UUIDs.

The mapping file structure:
{
    "task_id": {
        "checklists": {
            "1": "checklist_uuid_1",
            "2": "checklist_uuid_2"
        },
        "items": {
            "checklist_uuid_1": {
                "1": "item_uuid_1",
                "2": "item_uuid_2"
            }
        }
    }
}
"""

import json
import os
import time
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# fcntl is Unix-only, not available on Windows
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False


class ChecklistMappingManager:
    """
    Manages index-to-UUID mappings for checklists and checklist items.

    This manager provides:
    - Simple numeric indices for checklists and items
    - Persistent JSON storage
    - Thread-safe file operations with locking
    - Automatic index generation and reindexing
    - Validation and cleanup of mappings
    """

    DEFAULT_MAPPING_FILE = os.path.expanduser("~/.clickup_checklist_mappings.json")
    LOCK_TIMEOUT = 5  # seconds

    def __init__(self, mapping_file: Optional[str] = None):
        """
        Initialize the mapping manager.

        Args:
            mapping_file: Path to mapping file (defaults to ~/.clickup_checklist_mappings.json)
        """
        self.mapping_file = mapping_file or self.DEFAULT_MAPPING_FILE
        self._mappings: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load mappings from JSON file with file locking."""
        if not os.path.exists(self.mapping_file):
            self._mappings = {}
            return

        try:
            with open(self.mapping_file, 'r') as f:
                # Acquire shared lock for reading (Unix only)
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    content = f.read()
                    self._mappings = json.loads(content) if content else {}

                    # Validate structure
                    if not isinstance(self._mappings, dict):
                        self._mappings = {}
                finally:
                    if HAS_FCNTL:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (json.JSONDecodeError, IOError) as e:
            # If file is corrupted, start fresh
            self._mappings = {}
            print(f"Warning: Could not load checklist mapping file: {e}")

    def _save(self) -> None:
        """Save mappings to JSON file with file locking."""
        # Ensure parent directory exists
        parent_dir = Path(self.mapping_file).parent
        parent_dir.mkdir(parents=True, exist_ok=True)

        if HAS_FCNTL:
            # Unix: Use file locking
            lock_acquired = False
            start_time = time.time()

            while not lock_acquired and (time.time() - start_time) < self.LOCK_TIMEOUT:
                try:
                    # Open in write mode, create if doesn't exist
                    with open(self.mapping_file, 'w') as f:
                        # Acquire exclusive lock for writing
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        lock_acquired = True
                        try:
                            json.dump(self._mappings, f, indent=2)
                        finally:
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except BlockingIOError:
                    # Lock held by another process, wait and retry
                    time.sleep(0.1)

            if not lock_acquired:
                raise RuntimeError(f"Could not acquire lock on {self.mapping_file} after {self.LOCK_TIMEOUT}s")
        else:
            # Windows: No file locking, just write directly
            with open(self.mapping_file, 'w') as f:
                json.dump(self._mappings, f, indent=2)

        # Set file permissions to user-only (0600)
        try:
            os.chmod(self.mapping_file, 0o600)
        except OSError:
            # On Windows, chmod may not work as expected
            pass

    def _ensure_task_structure(self, task_id: str) -> None:
        """Ensure task mapping structure exists."""
        if task_id not in self._mappings:
            self._mappings[task_id] = {
                'checklists': {},
                'items': {}
            }
        elif not isinstance(self._mappings[task_id], dict):
            self._mappings[task_id] = {
                'checklists': {},
                'items': {}
            }
        else:
            if 'checklists' not in self._mappings[task_id]:
                self._mappings[task_id]['checklists'] = {}
            if 'items' not in self._mappings[task_id]:
                self._mappings[task_id]['items'] = {}

    def get_checklist_uuid(self, task_id: str, index: int) -> Optional[str]:
        """
        Get checklist UUID by index.

        Args:
            task_id: Task ID
            index: Numeric index (1, 2, 3...)

        Returns:
            Checklist UUID or None if not found
        """
        if task_id not in self._mappings:
            return None

        checklists = self._mappings[task_id].get('checklists', {})
        return checklists.get(str(index))

    def get_item_uuid(self, task_id: str, checklist_id: str, index: int) -> Optional[str]:
        """
        Get checklist item UUID by index.

        Args:
            task_id: Task ID
            checklist_id: Checklist UUID
            index: Numeric index (1, 2, 3...)

        Returns:
            Item UUID or None if not found
        """
        if task_id not in self._mappings:
            return None

        items = self._mappings[task_id].get('items', {})
        checklist_items = items.get(checklist_id, {})
        return checklist_items.get(str(index))

    def get_checklist_index(self, task_id: str, checklist_uuid: str) -> Optional[int]:
        """
        Get checklist index by UUID (reverse lookup).

        Args:
            task_id: Task ID
            checklist_uuid: Checklist UUID

        Returns:
            Numeric index or None if not found
        """
        if task_id not in self._mappings:
            return None

        checklists = self._mappings[task_id].get('checklists', {})
        for index, uuid in checklists.items():
            if uuid == checklist_uuid:
                return int(index)

        return None

    def get_item_index(self, task_id: str, checklist_id: str, item_uuid: str) -> Optional[int]:
        """
        Get item index by UUID (reverse lookup).

        Args:
            task_id: Task ID
            checklist_id: Checklist UUID
            item_uuid: Item UUID

        Returns:
            Numeric index or None if not found
        """
        if task_id not in self._mappings:
            return None

        items = self._mappings[task_id].get('items', {})
        checklist_items = items.get(checklist_id, {})

        for index, uuid in checklist_items.items():
            if uuid == item_uuid:
                return int(index)

        return None

    def set_checklist_mapping(self, task_id: str, index: int, checklist_uuid: str) -> None:
        """
        Set checklist index-to-UUID mapping.

        Args:
            task_id: Task ID
            index: Numeric index (1, 2, 3...)
            checklist_uuid: Checklist UUID
        """
        self._ensure_task_structure(task_id)
        self._mappings[task_id]['checklists'][str(index)] = checklist_uuid
        self._save()

    def set_item_mapping(self, task_id: str, checklist_id: str, index: int, item_uuid: str) -> None:
        """
        Set item index-to-UUID mapping.

        Args:
            task_id: Task ID
            checklist_id: Checklist UUID
            index: Numeric index (1, 2, 3...)
            item_uuid: Item UUID
        """
        self._ensure_task_structure(task_id)

        if checklist_id not in self._mappings[task_id]['items']:
            self._mappings[task_id]['items'][checklist_id] = {}

        self._mappings[task_id]['items'][checklist_id][str(index)] = item_uuid
        self._save()

    def get_next_checklist_index(self, task_id: str) -> int:
        """
        Get the next available index for a task's checklists.

        Args:
            task_id: Task ID

        Returns:
            Next available index (1-based)
        """
        if task_id not in self._mappings:
            return 1

        checklists = self._mappings[task_id].get('checklists', {})
        if not checklists:
            return 1

        # Find the maximum index and add 1
        max_index = max(int(idx) for idx in checklists.keys())
        return max_index + 1

    def get_next_item_index(self, task_id: str, checklist_id: str) -> int:
        """
        Get the next available index for a checklist's items.

        Args:
            task_id: Task ID
            checklist_id: Checklist UUID

        Returns:
            Next available index (1-based)
        """
        if task_id not in self._mappings:
            return 1

        items = self._mappings[task_id].get('items', {})
        checklist_items = items.get(checklist_id, {})

        if not checklist_items:
            return 1

        # Find the maximum index and add 1
        max_index = max(int(idx) for idx in checklist_items.keys())
        return max_index + 1

    def update_mappings_from_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """
        Update mappings from task data, ensuring all checklists and items are mapped.

        This syncs the mapping with actual ClickUp data, handling cases where
        the mapping might be out of sync.

        Args:
            task_id: Task ID
            task_data: Task data from API (should include 'checklists' field)
        """
        checklists = task_data.get('checklists', [])
        if not checklists:
            return

        self._ensure_task_structure(task_id)

        # Build reverse lookup for existing mappings
        existing_checklist_uuids = set(self._mappings[task_id]['checklists'].values())

        # Map all checklists
        for checklist in checklists:
            checklist_uuid = checklist.get('id')
            if not checklist_uuid:
                continue

            # Check if already mapped
            existing_index = self.get_checklist_index(task_id, checklist_uuid)

            if existing_index is None:
                # Not mapped yet, assign next available index
                next_index = self.get_next_checklist_index(task_id)
                self._mappings[task_id]['checklists'][str(next_index)] = checklist_uuid

                # Also map items in this checklist
                items = checklist.get('items', [])
                if checklist_uuid not in self._mappings[task_id]['items']:
                    self._mappings[task_id]['items'][checklist_uuid] = {}

                for item in items:
                    item_uuid = item.get('id')
                    if not item_uuid:
                        continue

                    # Check if item already mapped
                    existing_item_index = self.get_item_index(task_id, checklist_uuid, item_uuid)
                    if existing_item_index is None:
                        next_item_index = self.get_next_item_index(task_id, checklist_uuid)
                        self._mappings[task_id]['items'][checklist_uuid][str(next_item_index)] = item_uuid
            else:
                # Checklist already mapped, just ensure items are mapped
                items = checklist.get('items', [])
                if checklist_uuid not in self._mappings[task_id]['items']:
                    self._mappings[task_id]['items'][checklist_uuid] = {}

                for item in items:
                    item_uuid = item.get('id')
                    if not item_uuid:
                        continue

                    existing_item_index = self.get_item_index(task_id, checklist_uuid, item_uuid)
                    if existing_item_index is None:
                        next_item_index = self.get_next_item_index(task_id, checklist_uuid)
                        self._mappings[task_id]['items'][checklist_uuid][str(next_item_index)] = item_uuid

        self._save()

    def cleanup_mappings(self, task_id: str, task_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Clean up mappings by removing deleted checklists and items.

        Args:
            task_id: Task ID
            task_data: Optional task data to validate against. If None, only removes task if empty.
        """
        if task_id not in self._mappings:
            return

        if task_data is None:
            # No task data provided, just clean up empty task mappings
            task_mapping = self._mappings[task_id]
            if not task_mapping.get('checklists') and not task_mapping.get('items'):
                del self._mappings[task_id]
                self._save()
            return

        checklists = task_data.get('checklists', [])
        valid_checklist_uuids = {cl.get('id') for cl in checklists if cl.get('id')}
        valid_item_uuids_by_checklist = {}

        for checklist in checklists:
            checklist_uuid = checklist.get('id')
            if not checklist_uuid:
                continue

            items = checklist.get('items', [])
            valid_item_uuids_by_checklist[checklist_uuid] = {
                item.get('id') for item in items if item.get('id')
            }

        # Remove invalid checklist mappings
        checklists_to_remove = []
        for index, uuid in list(self._mappings[task_id]['checklists'].items()):
            if uuid not in valid_checklist_uuids:
                checklists_to_remove.append(index)

        for index in checklists_to_remove:
            del self._mappings[task_id]['checklists'][index]

        # Remove invalid item mappings
        items_mapping = self._mappings[task_id].get('items', {})

        # Remove items for deleted checklists
        for checklist_uuid in list(items_mapping.keys()):
            if checklist_uuid not in valid_checklist_uuids:
                del items_mapping[checklist_uuid]
                continue

            # Remove deleted items within valid checklists
            valid_items = valid_item_uuids_by_checklist.get(checklist_uuid, set())
            items_to_remove = []

            for index, item_uuid in list(items_mapping[checklist_uuid].items()):
                if item_uuid not in valid_items:
                    items_to_remove.append(index)

            for index in items_to_remove:
                del items_mapping[checklist_uuid][index]

        # Optionally reindex to maintain sequential indices
        self._reindex_checklists(task_id)
        self._reindex_items(task_id)

        self._save()

    def _reindex_checklists(self, task_id: str) -> None:
        """
        Reindex checklists to maintain sequential indices (1, 2, 3...).

        Args:
            task_id: Task ID
        """
        if task_id not in self._mappings:
            return

        checklists = self._mappings[task_id].get('checklists', {})
        if not checklists:
            return

        # Sort by current index and reassign sequentially
        sorted_items = sorted(checklists.items(), key=lambda x: int(x[0]))
        new_checklists = {}

        for new_index, (old_index, uuid) in enumerate(sorted_items, start=1):
            new_checklists[str(new_index)] = uuid

        self._mappings[task_id]['checklists'] = new_checklists

    def _reindex_items(self, task_id: str) -> None:
        """
        Reindex items within each checklist to maintain sequential indices.

        Args:
            task_id: Task ID
        """
        if task_id not in self._mappings:
            return

        items = self._mappings[task_id].get('items', {})

        for checklist_id in items:
            checklist_items = items[checklist_id]
            if not checklist_items:
                continue

            # Sort by current index and reassign sequentially
            sorted_items = sorted(checklist_items.items(), key=lambda x: int(x[0]))
            new_items = {}

            for new_index, (old_index, uuid) in enumerate(sorted_items, start=1):
                new_items[str(new_index)] = uuid

            items[checklist_id] = new_items

    def remove_checklist_mapping(self, task_id: str, checklist_uuid: str) -> None:
        """
        Remove a checklist and all its items from mapping.

        Args:
            task_id: Task ID
            checklist_uuid: Checklist UUID to remove
        """
        if task_id not in self._mappings:
            return

        # Remove checklist mapping
        checklists = self._mappings[task_id].get('checklists', {})
        index_to_remove = None

        for index, uuid in checklists.items():
            if uuid == checklist_uuid:
                index_to_remove = index
                break

        if index_to_remove:
            del self._mappings[task_id]['checklists'][index_to_remove]

        # Remove all items for this checklist
        items = self._mappings[task_id].get('items', {})
        if checklist_uuid in items:
            del items[checklist_uuid]

        # Reindex
        self._reindex_checklists(task_id)

        self._save()

    def remove_item_mapping(self, task_id: str, checklist_id: str, item_uuid: str) -> None:
        """
        Remove an item from mapping.

        Args:
            task_id: Task ID
            checklist_id: Checklist UUID
            item_uuid: Item UUID to remove
        """
        if task_id not in self._mappings:
            return

        items = self._mappings[task_id].get('items', {})
        checklist_items = items.get(checklist_id, {})

        index_to_remove = None
        for index, uuid in checklist_items.items():
            if uuid == item_uuid:
                index_to_remove = index
                break

        if index_to_remove:
            del checklist_items[index_to_remove]

        # Reindex items for this checklist
        if checklist_id in items:
            checklist_items = items[checklist_id]
            if checklist_items:
                sorted_items = sorted(checklist_items.items(), key=lambda x: int(x[0]))
                new_items = {}
                for new_index, (old_index, uuid) in enumerate(sorted_items, start=1):
                    new_items[str(new_index)] = uuid
                items[checklist_id] = new_items

        self._save()

    def get_all_mappings(self, task_id: str) -> Dict[str, Any]:
        """
        Get all mappings for a task.

        Args:
            task_id: Task ID

        Returns:
            Dictionary with checklists and items mappings
        """
        if task_id not in self._mappings:
            return {'checklists': {}, 'items': {}}

        return self._mappings[task_id].copy()


def get_mapping_manager() -> ChecklistMappingManager:
    """
    Get a ChecklistMappingManager instance (singleton pattern).

    Returns:
        ChecklistMappingManager instance
    """
    if not hasattr(get_mapping_manager, '_instance'):
        get_mapping_manager._instance = ChecklistMappingManager()
    return get_mapping_manager._instance
