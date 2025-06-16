"""Test configuration for File Management Instrument."""

import os
import tempfile
from pathlib import Path

# Test directories
TEST_ROOT = Path(tempfile.gettempdir()) / "saadhan_tests"
TEST_DATA_DIR = TEST_ROOT / "test_data" / "file_manager"
TEST_TEMP_DIR = TEST_ROOT / "temp"

# Test file paths
TEST_FILES = {
    'document': TEST_DATA_DIR / "test_document.md",
    'template': TEST_DATA_DIR / "test_template.md",
    'config': TEST_DATA_DIR / "test_config.json",
}

# Test content
TEST_CONTENT = {
    'document': """# Test Document
This is a test document for file management testing.
## Section 1
Test content for section 1.
## Section 2
Test content for section 2.""",
    
    'template': """# [Title]
## Overview
[Overview content]
## Details
[Details content]""",
    
    'config': """{
    "version": "1.0",
    "settings": {
        "backup_enabled": true,
        "max_versions": 5
    }
}"""
}

def setup_test_environment():
    """Set up the test environment with necessary files and directories."""
    # Create test directories
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create test files with content
    for file_type, file_path in TEST_FILES.items():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(TEST_CONTENT[file_type])

def cleanup_test_environment():
    """Clean up the test environment."""
    # Remove test files
    if TEST_ROOT.exists():
        for file in TEST_ROOT.glob("**/*"):
            if file.is_file():
                try:
                    file.unlink()
                except (PermissionError, FileNotFoundError):
                    pass
        for dir_path in reversed(list(TEST_ROOT.glob("**/*"))):
            if dir_path.is_dir():
                try:
                    dir_path.rmdir()
                except (PermissionError, FileNotFoundError):
                    pass
        try:
            TEST_ROOT.rmdir()
        except (PermissionError, FileNotFoundError):
            pass 