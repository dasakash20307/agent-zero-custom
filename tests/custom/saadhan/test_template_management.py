"""Test cases for Template Management Instrument."""

import unittest
from pathlib import Path
from datetime import datetime
from tests.custom.saadhan.test_config import (
    TEST_ROOT,
    setup_test_environment,
    cleanup_test_environment
)
from instruments.custom.saadhan.template_management import (
    TemplateManager,
    TemplateScanner,
    Template,
    TemplateVariable
)

class TestTemplateManagement(unittest.TestCase):
    """Test cases for Template Management."""

    def setUp(self):
        """Set up test environment."""
        setup_test_environment()
        self.template_manager = TemplateManager(workspace_root=str(TEST_ROOT))
        self.template_scanner = TemplateScanner()

    def tearDown(self):
        """Clean up test environment."""
        cleanup_test_environment()

    def test_create_template(self):
        """Test template creation."""
        template = self.template_manager.create_template({
            'name': 'Test Template',
            'type': 'report',
            'content': '# [Title]\n## [Section1]\nContent here',
            'variables': ['Title', 'Section1']
        })
        
        self.assertEqual(template.name, 'Test Template')
        self.assertEqual(template.type, 'report')
        self.assertIn('[Title]', template.content)
        self.assertEqual(len(template.variables), 2)

    def test_scan_document(self):
        """Test document scanning."""
        test_doc = TEST_ROOT / "test_data" / "test_document.md"
        test_doc.parent.mkdir(parents=True, exist_ok=True)
        test_doc.write_text("""
# Test Document
## Section 1
Content for {variable1}
## Section 2
Content for {variable2}
""")
        
        doc_structure = self.template_scanner.scan_document(test_doc)
        self.assertEqual(len(doc_structure.sections), 2)
        self.assertEqual(len(doc_structure.variables), 2)

    def test_template_variable(self):
        """Test template variable handling."""
        variable = TemplateVariable(
            name="test_var",
            description="Test variable",
            type="string",
            required=True
        )
        
        self.assertEqual(variable.name, "test_var")
        self.assertEqual(variable.type, "string")
        self.assertTrue(variable.required)
        self.assertEqual(variable.default, "")

if __name__ == "__main__":
    unittest.main() 