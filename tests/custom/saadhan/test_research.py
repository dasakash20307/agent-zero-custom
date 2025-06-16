"""Test cases for Research Instrument."""

import unittest
from pathlib import Path
from datetime import datetime
from tests.custom.saadhan.test_config import (
    TEST_ROOT,
    setup_test_environment,
    cleanup_test_environment
)
from instruments.custom.saadhan.research import (
    ResearchManager,
    Research,
    ResearchSource,
    ResearchFinding
)
from instruments.custom.saadhan.research.analysis_engine import AnalysisEngine

class TestResearch(unittest.TestCase):
    """Test cases for Research Instrument."""

    def setUp(self):
        """Set up test environment."""
        setup_test_environment()
        self.research_manager = ResearchManager(base_dir=TEST_ROOT)
        self.analysis_engine = AnalysisEngine(workspace_root=str(TEST_ROOT))

    def tearDown(self):
        """Clean up test environment."""
        cleanup_test_environment()

    def test_create_research(self):
        """Test research project creation."""
        research = self.research_manager.create_research(
            title="Test Research",
            description="Test research description",
            objectives=["Objective 1", "Objective 2"],
            methodology="Test methodology"
        )
        
        self.assertEqual(research.title, "Test Research")
        self.assertEqual(research.description, "Test research description")
        self.assertEqual(len(research.objectives), 2)
        self.assertEqual(research.methodology, "Test methodology")
        self.assertEqual(research.status, "planned")
        self.assertEqual(len(research.sources), 0)
        self.assertEqual(len(research.findings), 0)

    def test_add_source(self):
        """Test adding research source."""
        research = self.research_manager.create_research(
            title="Test Research",
            description="Test research description",
            objectives=["Objective 1"],
            methodology="Test methodology"
        )
        
        source = self.research_manager.add_source(
            research_id=research.id,
            title="Test Source",
            url="https://example.com",
            source_type="website",
            description="Test source description"
        )
        
        self.assertEqual(source['title'], "Test Source")
        self.assertEqual(source['url'], "https://example.com")
        self.assertEqual(source['type'], "website")
        self.assertEqual(source['description'], "Test source description")
        self.assertTrue('added_at' in source)

    def test_add_finding(self):
        """Test adding research finding."""
        research = self.research_manager.create_research(
            title="Test Research",
            description="Test research description",
            objectives=["Objective 1"],
            methodology="Test methodology"
        )
        
        finding = self.research_manager.add_finding(
            research_id=research.id,
            title="Test Finding",
            description="Test finding description",
            evidence="Test evidence"
        )
        
        self.assertEqual(finding['title'], "Test Finding")
        self.assertEqual(finding['description'], "Test finding description")
        self.assertEqual(finding['evidence'], "Test evidence")
        self.assertTrue('added_at' in finding)

    def test_analyze_survey_data(self):
        """Test survey data analysis."""
        survey_data = {
            'questions': [
                {'id': 'q1', 'text': 'Question 1'},
                {'id': 'q2', 'text': 'Question 2'}
            ],
            'responses': [
                {'data': {'q1': 'Yes', 'q2': 'No'}},
                {'data': {'q1': 'No', 'q2': 'Yes'}}
            ]
        }
        
        analysis_params = {
            'title': 'Survey Analysis',
            'description': 'Test survey analysis',
            'analyst': 'test_user'
        }
        
        result = self.analysis_engine.analyze_survey_data(survey_data, analysis_params)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.title, 'Survey Analysis')
        self.assertEqual(result.data_source, 'survey')
        self.assertEqual(result.method, 'statistical_analysis')
        self.assertTrue('response_count' in result.results)
        self.assertTrue('completion_rate' in result.results)
        self.assertTrue('question_analysis' in result.results)

if __name__ == "__main__":
    unittest.main() 