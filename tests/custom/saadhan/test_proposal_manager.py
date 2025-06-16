"""Test cases for the Proposal Development Instrument."""

import unittest
from pathlib import Path
from datetime import datetime
from tests.custom.saadhan.test_file_manager_config import (
    TEST_ROOT,
    setup_test_environment,
    cleanup_test_environment
)
from instruments.custom.saadhan import ProposalManager

class TestProposalManager(unittest.TestCase):
    """Test cases for ProposalManager."""

    def setUp(self):
        """Set up test environment."""
        setup_test_environment()
        self.proposal_manager = ProposalManager(workspace_root=TEST_ROOT)

    def tearDown(self):
        """Clean up test environment."""
        cleanup_test_environment()

    def test_create_proposal(self):
        """Test proposal creation."""
        proposal = self.proposal_manager.create_proposal(
            title="Test Proposal",
            description="A test proposal for unit testing",
            objectives=["Test objective 1", "Test objective 2"],
            methodology="Test methodology description",
            timeline={
                "Phase 1": "Planning",
                "Phase 2": "Implementation"
            },
            budget_items=[
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
            partners=[
                {
                    'name': "Test Partner",
                    'role': "Technical Support",
                    'expertise': ["IT", "Training"]
                }
            ]
        )
        
        self.assertEqual(proposal.title, "Test Proposal")
        self.assertEqual(len(proposal.objectives), 2)
        self.assertEqual(len(proposal.budget_items), 2)
        self.assertEqual(len(proposal.partners), 1)

    def test_update_proposal(self):
        """Test proposal update."""
        # Create initial proposal
        proposal = self.proposal_manager.create_proposal(
            title="Test Proposal",
            description="Initial description",
            objectives=["Initial objective"]
        )
        
        # Update proposal
        updated_proposal = self.proposal_manager.update_proposal(
            proposal.id,
            description="Updated description",
            objectives=["Updated objective"]
        )
        
        self.assertEqual(updated_proposal.description, "Updated description")
        self.assertEqual(updated_proposal.objectives[0], "Updated objective")

    def test_submit_proposal(self):
        """Test proposal submission."""
        # Create proposal
        proposal = self.proposal_manager.create_proposal(
            title="Test Proposal",
            description="Test description",
            objectives=["Test objective"]
        )
        
        # Submit proposal
        submitted_proposal = self.proposal_manager.submit_proposal(
            proposal.id,
            submit_to="Test Organization",
            submission_notes="Test submission"
        )
        
        self.assertTrue(submitted_proposal.submitted)
        self.assertEqual(submitted_proposal.submit_to, "Test Organization")
        self.assertEqual(submitted_proposal.submission_notes, "Test submission")

if __name__ == "__main__":
    unittest.main() 