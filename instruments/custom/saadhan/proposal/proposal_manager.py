"""
Proposal Manager for Proposal Development Instrument
Handles proposal creation, tracking, and lifecycle management
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from ..template_management import TemplateManager

@dataclass
class BudgetItem:
    """Class representing a budget item."""
    name: str
    amount: float
    category: str
    description: str

@dataclass
class Partner:
    """Class representing a partner organization."""
    name: str
    role: str
    expertise: List[str]

@dataclass
class Proposal:
    """Class representing a proposal."""
    id: str
    title: str
    description: str
    objectives: List[str]
    methodology: str
    timeline: Dict[str, str]
    budget_items: List[BudgetItem]
    partners: List[Partner]
    created_at: str
    submitted: bool = False
    submit_to: Optional[str] = None
    submission_notes: Optional[str] = None

class ProposalManager:
    """Manages proposal development and tracking."""
    
    def __init__(self, workspace_root: Union[str, Path]):
        """
        Initialize proposal manager
        Args:
            workspace_root: Path to workspace root directory
        """
        self.workspace_root = Path(workspace_root)
        self.proposals_dir = self.workspace_root / "proposals"
        self.proposals_dir.mkdir(parents=True, exist_ok=True)

    def create_proposal(self, title: str, description: str, objectives: List[str],
                       methodology: str = "", timeline: Optional[Dict[str, str]] = None,
                       budget_items: Optional[List[Dict]] = None,
                       partners: Optional[List[Dict]] = None) -> Proposal:
        """
        Create a new proposal
        Args:
            title: Proposal title
            description: Proposal description
            objectives: List of objectives
            methodology: Project methodology
            timeline: Project timeline
            budget_items: List of budget items
            partners: List of partners
        Returns:
            Created proposal
        """
        # Generate proposal ID
        proposal_id = f"p_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create proposal object
        proposal = Proposal(
            id=proposal_id,
            title=title,
            description=description,
            objectives=objectives,
            methodology=methodology,
            timeline=timeline or {},
            budget_items=[
                BudgetItem(**item) for item in (budget_items or [])
            ],
            partners=[
                Partner(**partner) for partner in (partners or [])
            ],
            created_at=datetime.now().isoformat()
        )
        
        # Save proposal
        self._save_proposal(proposal)
        
        return proposal

    def update_proposal(self, proposal_id: str, **updates) -> Proposal:
        """
        Update an existing proposal
        Args:
            proposal_id: ID of proposal to update
            **updates: Keyword arguments containing updates
        Returns:
            Updated proposal
        """
        proposal = self._load_proposal(proposal_id)
        
        # Update fields
        for field, value in updates.items():
            if hasattr(proposal, field):
                if field == 'budget_items' and value is not None:
                    value = [BudgetItem(**item) for item in value]
                elif field == 'partners' and value is not None:
                    value = [Partner(**partner) for partner in value]
                setattr(proposal, field, value)
        
        # Save updated proposal
        self._save_proposal(proposal)
        
        return proposal

    def submit_proposal(self, proposal_id: str, submit_to: str, submission_notes: str) -> Proposal:
        """
        Submit a proposal
        Args:
            proposal_id: ID of proposal to submit
            submit_to: Organization to submit to
            submission_notes: Notes about submission
        Returns:
            Submitted proposal
        """
        proposal = self._load_proposal(proposal_id)
        
        # Update submission details
        proposal.submitted = True
        proposal.submit_to = submit_to
        proposal.submission_notes = submission_notes
        
        # Save updated proposal
        self._save_proposal(proposal)
        
        return proposal

    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """
        Retrieve proposal by ID
        Args:
            proposal_id: Proposal identifier
        Returns:
            Proposal object if found, None otherwise
        """
        proposal_file = self.proposals_dir / f"{proposal_id}.json"
        if not proposal_file.exists():
            return None

        try:
            with open(proposal_file, 'r') as f:
                data = json.load(f)
                return Proposal(**data)
        except Exception as e:
            raise Exception(f"Failed to load proposal: {str(e)}")

    def list_proposals(self, status: str = None) -> List[Proposal]:
        """
        List all proposals, optionally filtered by status
        Args:
            status: Proposal status filter
        Returns:
            List of Proposal objects
        """
        proposals = []
        for filename in os.listdir(self.proposals_dir):
            if filename.endswith('.json'):
                proposal = self.get_proposal(filename[:-5])
                if proposal and (not status or proposal.status == status):
                    proposals.append(proposal)
        return proposals

    def get_proposal_versions(self, proposal_id: str) -> List[Dict]:
        """
        Get version history of a proposal
        Args:
            proposal_id: Proposal identifier
        Returns:
            List of version information
        """
        version_dir = self.workspace_root / "proposal_versions" / proposal_id
        if not version_dir.exists():
            return []

        versions = []
        for filename in os.listdir(version_dir):
            if filename.endswith('.json'):
                with open(version_dir / filename, 'r') as f:
                    data = json.load(f)
                    versions.append({
                        'version': data['version'],
                        'updated_at': data['updated_at'],
                        'author': data['author']
                    })

        return sorted(versions, key=lambda x: float(x['version']))

    def get_submission_history(self, proposal_id: str) -> List[Dict]:
        """
        Get submission history of a proposal
        Args:
            proposal_id: Proposal identifier
        Returns:
            List of submission records
        """
        submissions = []
        for filename in os.listdir(self.workspace_root / "proposal_submissions"):
            if filename.endswith('.json'):
                with open(self.workspace_root / "proposal_submissions" / filename, 'r') as f:
                    submission = json.load(f)
                    if submission['proposal_id'] == proposal_id:
                        submissions.append(submission)

        return sorted(submissions, key=lambda x: x['submission_date'])

    def _save_proposal(self, proposal: Proposal):
        """Save proposal to file."""
        file_path = self.proposals_dir / f"{proposal.id}.json"
        with open(file_path, 'w') as f:
            json.dump(asdict(proposal), f, indent=2)

    def _load_proposal(self, proposal_id: str) -> Proposal:
        """Load proposal from file."""
        file_path = self.proposals_dir / f"{proposal_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Proposal not found: {proposal_id}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert budget items and partners back to objects
        data['budget_items'] = [BudgetItem(**item) for item in data.get('budget_items', [])]
        data['partners'] = [Partner(**partner) for partner in data.get('partners', [])]
        
        return Proposal(**data)

    def generate_summary(self, proposal_id: str) -> Dict:
        """
        Generate proposal summary
        Args:
            proposal_id: Proposal identifier
        Returns:
            Dictionary containing summary information
        """
        proposal = self.get_proposal(proposal_id)
        if proposal is None:
            raise Exception("Proposal not found")

        return {
            'id': proposal.id,
            'title': proposal.title,
            'type': proposal.type,
            'status': proposal.status,
            'version': proposal.version,
            'budget': proposal.budget,
            'duration': proposal.duration,
            'beneficiaries': sum(proposal.target_beneficiaries.values()),
            'partner_count': len(proposal.partners),
            'activity_count': len(proposal.activities),
            'milestone_count': len(proposal.milestones),
            'risk_count': len(proposal.risks),
            'created_at': proposal.created_at,
            'updated_at': proposal.updated_at,
            'submitted_at': proposal.submitted_at
        } 