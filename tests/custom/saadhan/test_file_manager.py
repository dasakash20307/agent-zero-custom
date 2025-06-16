"""Test cases for the File Management Instrument."""

import unittest
import json
from pathlib import Path
from datetime import datetime
from tests.custom.saadhan.test_file_manager_config import (
    TEST_FILES,
    TEST_CONTENT,
    setup_test_environment,
    cleanup_test_environment,
    TEST_TEMP_DIR
)
from instruments.custom.saadhan import FileManager

class TestFileManager(unittest.TestCase):
    """Test cases for FileManager."""

    def setUp(self):
        """Set up test environment."""
        setup_test_environment()
        self.workspace_root = str(Path(__file__).parent)
        self.file_manager = FileManager(base_dir=self.workspace_root)

    def tearDown(self):
        """Clean up test environment."""
        cleanup_test_environment()

    def test_read_file(self):
        """Test file reading functionality."""
        # Read markdown file
        content = self.file_manager.read_file(TEST_FILES['document'])
        self.assertEqual(content, TEST_CONTENT['document'])
        
        # Read JSON file
        content = self.file_manager.read_file(TEST_FILES['config'])
        config_data = json.loads(content)
        self.assertEqual(config_data['version'], '1.0')
        self.assertTrue(config_data['settings']['backup_enabled'])

    def test_write_file(self):
        """Test file writing functionality."""
        test_file = TEST_TEMP_DIR / "write_test.txt"
        test_content = "Test content for writing"
        
        # Write file
        self.file_manager.write_file(test_file, test_content)
        
        # Verify content
        self.assertTrue(test_file.exists())
        self.assertEqual(test_file.read_text(), test_content)

    def test_copy_file(self):
        """Test file copying functionality."""
        source_file = TEST_FILES['document']
        target_file = TEST_TEMP_DIR / "copied_document.md"
        
        # Copy file
        self.file_manager.copy_file(source_file, target_file)
        
        # Verify copy
        self.assertTrue(target_file.exists())
        self.assertEqual(target_file.read_text(), TEST_CONTENT['document'])

    def test_move_file(self):
        """Test file moving functionality."""
        source_file = TEST_TEMP_DIR / "move_test.txt"
        source_file.write_text("Test content for moving")
        target_file = TEST_TEMP_DIR / "moved_file.txt"
        
        # Move file
        self.file_manager.move_file(source_file, target_file)
        
        # Verify move
        self.assertFalse(source_file.exists())
        self.assertTrue(target_file.exists())
        self.assertEqual(target_file.read_text(), "Test content for moving")

    def test_delete_file(self):
        """Test file deletion functionality."""
        test_file = TEST_TEMP_DIR / "delete_test.txt"
        test_file.write_text("Test content for deletion")
        
        # Delete file
        self.file_manager.delete_file(test_file)
        
        # Verify deletion
        self.assertFalse(test_file.exists())

    def test_create_backup(self):
        """Test file backup functionality."""
        source_file = TEST_FILES['document']
        backup_file = self.file_manager.create_backup(source_file)
        
        # Verify backup
        self.assertTrue(backup_file.exists())
        self.assertEqual(backup_file.read_text(), TEST_CONTENT['document'])
        
        # Verify backup naming
        self.assertIn(datetime.now().strftime('%Y%m%d'), str(backup_file))

    def test_list_files(self):
        """Test file listing functionality."""
        # List all test files
        files = self.file_manager.list_files(TEST_FILES['document'].parent)
        
        # Verify all test files are listed
        for test_file in TEST_FILES.values():
            self.assertIn(test_file.name, [f.name for f in files])

    def test_search_files(self):
        """Test file search functionality."""
        # Search for markdown files
        md_files = self.file_manager.search_files(
            TEST_FILES['document'].parent,
            pattern="*.md"
        )
        
        # Verify markdown files are found
        self.assertIn(TEST_FILES['document'].name, [f.name for f in md_files])
        self.assertIn(TEST_FILES['template'].name, [f.name for f in md_files])

if __name__ == "__main__":
    unittest.main() 