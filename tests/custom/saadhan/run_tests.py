"""
Test runner for Saadhan instruments
"""

import unittest
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# Import test modules
from test_proposal_manager import TestProposalManager
from test_file_manager import TestFileManager
from test_version_control import TestVersionControl
from test_template_management import TestTemplateManagement
from test_research import TestResearch
from test_report import TestReport

def run_tests():
    """Run all test cases"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestProposalManager))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestFileManager))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestVersionControl))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTemplateManagement))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestResearch))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestReport))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests()) 