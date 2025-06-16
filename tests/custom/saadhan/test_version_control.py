"""Test cases for Version Control functionality."""

import unittest
from pathlib import Path
from datetime import datetime
from tests.custom.saadhan.test_file_manager_config import (
    TEST_FILES,
    TEST_CONTENT,
    setup_test_environment,
    cleanup_test_environment,
    TEST_TEMP_DIR,
    TEST_ROOT
)
from instruments.custom.saadhan.file_management import VersionControl

class TestVersionControl(unittest.TestCase):
    """Test cases for VersionControl."""

    def setUp(self):
        """Set up test environment."""
        setup_test_environment()
        self.version_control = VersionControl(base_dir=TEST_ROOT)

    def tearDown(self):
        """Clean up test environment."""
        cleanup_test_environment()

    def test_create_version(self):
        """Test version creation."""
        test_file = TEST_FILES['document']
        
        # Create version
        version = self.version_control.create_version(
            test_file,
            comment="Initial version"
        )
        
        # Verify version
        self.assertIsNotNone(version.version_id)
        self.assertEqual(version.comment, "Initial version")
        self.assertTrue(version.timestamp)
        self.assertTrue(version.hash)

    def test_get_versions(self):
        """Test retrieving versions."""
        test_file = TEST_FILES['document']
        
        # Create multiple versions
        version1 = self.version_control.create_version(test_file, "First version")
        version2 = self.version_control.create_version(test_file, "Second version")
        
        # Get versions
        versions = self.version_control.get_versions(test_file)
        
        # Verify versions
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].comment, "First version")
        self.assertEqual(versions[1].comment, "Second version")

    def test_restore_version(self):
        """Test version restoration."""
        test_file = TEST_FILES['document']
        
        # Create initial version
        initial_version = self.version_control.create_version(test_file, "Initial version")
        initial_content = test_file.read_text()
        
        # Modify file
        modified_content = "Modified content"
        test_file.write_text(modified_content)
        
        # Create another version
        modified_version = self.version_control.create_version(test_file, "Modified version")
        
        # Restore initial version
        self.version_control.restore_version(test_file, initial_version.version_id)
        
        # Verify restoration
        restored_content = test_file.read_text()
        self.assertEqual(restored_content, initial_content)

if __name__ == "__main__":
    unittest.main() 