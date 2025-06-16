"""Test configuration for Saadhan instruments."""

import os
import tempfile
from pathlib import Path
from datetime import datetime

# Test directories
TEST_ROOT = Path(__file__).parent
TEST_DATA_DIR = TEST_ROOT / "test_data"
TEST_TEMP_DIR = Path(tempfile.gettempdir()) / "saadhan_tests"

# Create test directories if they don't exist
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Test file paths
TEST_PROPOSAL_FILE = TEST_DATA_DIR / "test_proposal.md"
TEST_REPORT_FILE = TEST_DATA_DIR / "test_report.md"
TEST_TEMPLATE_FILE = TEST_DATA_DIR / "test_template.md"

# Test proposal data
TEST_PROPOSAL_DATA = {
    'title': "Test Proposal",
    'description': "A test proposal for unit testing",
    'objectives': ["Test objective 1", "Test objective 2"],
    'methodology': "Test methodology description",
    'timeline': {
        "Phase 1": "Planning",
        "Phase 2": "Implementation"
    },
    'budget_items': [
        {
            'name': "Equipment",
            'amount': 5000.0,
            'category': "Capital",
            'description': "Test equipment"
        },
        {
            'name': "Training",
            'amount': 2000.0,
            'category': "Program",
            'description': "Staff training"
        }
    ],
    'partners': [
        {
            'name': "Test Partner",
            'role': "Technical Support",
            'expertise': ["IT", "Training"]
        }
    ]
}

TEST_REPORT_DATA = {
    "title": "Test Report",
    "sections": ["Introduction", "Methods", "Results"],
    "content": {
        "Introduction": "Test introduction content",
        "Methods": "Test methods content",
        "Results": "Test results content"
    }
}

# Test configurations
TEST_CONFIG = {
    "max_file_size": 1024 * 1024,  # 1MB
    "supported_formats": ["md", "txt", "html"],
    "temp_dir": TEST_TEMP_DIR,
    "backup_enabled": True
}

def setup_test_environment():
    """Set up the test environment with necessary files and directories."""
    # Create test directories
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (TEST_DATA_DIR / "file_manager").mkdir(parents=True, exist_ok=True)
    (TEST_DATA_DIR / "templates").mkdir(parents=True, exist_ok=True)
    (TEST_DATA_DIR / "research").mkdir(parents=True, exist_ok=True)
    (TEST_DATA_DIR / "reports").mkdir(parents=True, exist_ok=True)
    
    # Create test files with content
    TEST_PROPOSAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEST_PROPOSAL_FILE.write_text("# Test Proposal\n\nTest content")
    
    TEST_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEST_REPORT_FILE.write_text("# Test Report\n\nTest content")
    
    TEST_TEMPLATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEST_TEMPLATE_FILE.write_text("# Test Template\n\nTest content")

def cleanup_test_environment():
    """Clean up the test environment."""
    # Remove test files
    if TEST_DATA_DIR.exists():
        for file in TEST_DATA_DIR.glob("**/*"):
            if file.is_file():
                try:
                    file.unlink()
                except (PermissionError, FileNotFoundError):
                    pass
        for dir_path in reversed(list(TEST_DATA_DIR.glob("**/*"))):
            if dir_path.is_dir():
                try:
                    dir_path.rmdir()
                except (PermissionError, FileNotFoundError):
                    pass
        try:
            TEST_DATA_DIR.rmdir()
        except (PermissionError, FileNotFoundError):
            pass
    
    if TEST_TEMP_DIR.exists():
        for file in TEST_TEMP_DIR.glob("**/*"):
            if file.is_file():
                try:
                    file.unlink()
                except (PermissionError, FileNotFoundError):
                    pass
        for dir_path in reversed(list(TEST_TEMP_DIR.glob("**/*"))):
            if dir_path.is_dir():
                try:
                    dir_path.rmdir()
                except (PermissionError, FileNotFoundError):
                    pass
        try:
            TEST_TEMP_DIR.rmdir()
        except (PermissionError, FileNotFoundError):
            pass 