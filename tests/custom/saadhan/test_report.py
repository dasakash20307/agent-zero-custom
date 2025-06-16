"""Test cases for Report Generation Instrument."""

import unittest
from pathlib import Path
from datetime import datetime
from tests.custom.saadhan.test_config import (
    TEST_ROOT,
    setup_test_environment,
    cleanup_test_environment
)
from instruments.custom.saadhan.report import (
    ReportGenerator,
    Report,
    ReportSection,
    Template,
    TemplateSection
)

class TestReport(unittest.TestCase):
    """Test cases for Report Generation."""

    def setUp(self):
        """Set up test environment."""
        setup_test_environment()
        self.report_generator = ReportGenerator(base_dir=str(TEST_ROOT))

    def tearDown(self):
        """Clean up test environment."""
        cleanup_test_environment()

    def test_create_section(self):
        """Test report section creation."""
        section = self.report_generator.create_section(
            title="Test Section",
            content="Test content",
            data={
                'values': [10, 20, 30],
                'labels': ['A', 'B', 'C']
            }
        )
        
        self.assertEqual(section.title, "Test Section")
        self.assertEqual(section.content, "Test content")
        self.assertIsNotNone(section.data)
        if section.data:  # Check if data exists before accessing
            self.assertEqual(section.data['values'], [10, 20, 30])

    def test_create_report(self):
        """Test report creation."""
        sections = [
            self.report_generator.create_section(
                title="Section 1",
                content="Content 1"
            ),
            self.report_generator.create_section(
                title="Section 2",
                content="Content 2"
            )
        ]
        
        report = self.report_generator.create_report(
            title="Test Report",
            sections=sections,
            metadata={'author': 'Test Author'}
        )
        
        self.assertEqual(report.title, "Test Report")
        self.assertEqual(len(report.sections), 2)
        self.assertEqual(report.metadata['author'], "Test Author")

    def test_format_report(self):
        """Test report formatting."""
        sections = [
            self.report_generator.create_section(
                title="Section 1",
                content="Content 1"
            )
        ]
        
        report = self.report_generator.create_report(
            title="Test Report",
            sections=sections
        )
        
        # Format as markdown
        markdown = self.report_generator.format_report(report, 'markdown')
        self.assertIn("# Test Report", markdown)
        self.assertIn("## Section 1", markdown)
        self.assertIn("Content 1", markdown)
        
        # Format as HTML
        html = self.report_generator.format_report(report, 'html')
        self.assertIn("<h1>Test Report</h1>", html)
        self.assertIn("Section 1", html)
        self.assertIn("Content 1", html)

    def test_save_report(self):
        """Test report saving."""
        sections = [
            self.report_generator.create_section(
                title="Section 1",
                content="Content 1"
            )
        ]
        
        report = self.report_generator.create_report(
            title="Test Report",
            sections=sections
        )
        
        output_path = TEST_ROOT / "test_data" / "test_report.md"
        saved_path = self.report_generator.save_report(
            report=report,
            output_path=output_path,
            output_format='markdown'
        )
        
        self.assertTrue(saved_path.exists())
        content = saved_path.read_text()
        self.assertIn("# Test Report", content)
        self.assertIn("## Section 1", content)
        self.assertIn("Content 1", content)

if __name__ == "__main__":
    unittest.main() 