"""
Partner Analyzer for Proposal Development Instrument
Handles partner evaluation and collaboration analysis
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class Partner:
    """Partner data structure"""
    id: str
    name: str
    type: str
    sector: str
    expertise: List[str]
    experience: Dict[str, List[str]]
    resources: Dict[str, float]
    location: str
    contact_info: Dict[str, str]
    past_collaborations: List[Dict]
    risk_assessment: Dict[str, str]
    status: str
    created_at: str
    updated_at: str

@dataclass
class Collaboration:
    """Collaboration data structure"""
    id: str
    proposal_id: str
    partner_id: str
    role: str
    responsibilities: List[str]
    resources_committed: Dict[str, float]
    timeline: Dict[str, str]
    deliverables: List[str]
    risks: List[Dict]
    status: str
    created_at: str
    updated_at: str

class PartnerAnalyzer:
    def __init__(self, workspace_root: str):
        """
        Initialize partner analyzer
        Args:
            workspace_root: Path to workspace root directory
        """
        self.workspace_root = workspace_root
        self.partners_dir = os.path.join(workspace_root, 'partners')
        self.collaborations_dir = os.path.join(workspace_root, 'collaborations')
        self._ensure_directories()

        # Standard partner types and sectors
        self.partner_types = {
            'ngo': 'Non-Governmental Organization',
            'government': 'Government Agency',
            'academic': 'Academic Institution',
            'private': 'Private Sector',
            'community': 'Community Organization'
        }

        self.sectors = {
            'agriculture': 'Agriculture and Rural Development',
            'education': 'Education and Training',
            'health': 'Health and Healthcare',
            'environment': 'Environment and Conservation',
            'technology': 'Technology and Innovation',
            'social': 'Social Development',
            'finance': 'Financial Services'
        }

    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.partners_dir, exist_ok=True)
        os.makedirs(self.collaborations_dir, exist_ok=True)

    def register_partner(self, partner_data: Dict) -> Partner:
        """
        Register a new partner
        Args:
            partner_data: Dictionary containing partner information
        Returns:
            Partner object
        """
        try:
            partner_id = f"PTR_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            partner = Partner(
                id=partner_id,
                name=partner_data['name'],
                type=partner_data['type'],
                sector=partner_data['sector'],
                expertise=partner_data['expertise'],
                experience=partner_data['experience'],
                resources=partner_data.get('resources', {}),
                location=partner_data['location'],
                contact_info=partner_data['contact_info'],
                past_collaborations=partner_data.get('past_collaborations', []),
                risk_assessment=self._assess_partner_risks(partner_data),
                status='active',
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )

            self._save_partner(partner)
            return partner

        except Exception as e:
            raise Exception(f"Failed to register partner: {str(e)}")

    def create_collaboration(self, proposal_id: str, collaboration_data: Dict) -> Collaboration:
        """
        Create a new collaboration
        Args:
            proposal_id: Associated proposal ID
            collaboration_data: Dictionary containing collaboration information
        Returns:
            Collaboration object
        """
        try:
            collaboration_id = f"COL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            collaboration = Collaboration(
                id=collaboration_id,
                proposal_id=proposal_id,
                partner_id=collaboration_data['partner_id'],
                role=collaboration_data['role'],
                responsibilities=collaboration_data['responsibilities'],
                resources_committed=collaboration_data.get('resources_committed', {}),
                timeline=collaboration_data['timeline'],
                deliverables=collaboration_data['deliverables'],
                risks=self._assess_collaboration_risks(collaboration_data),
                status='planned',
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )

            self._save_collaboration(collaboration)
            return collaboration

        except Exception as e:
            raise Exception(f"Failed to create collaboration: {str(e)}")

    def update_partner(self, partner_id: str, updates: Dict) -> Partner:
        """
        Update partner information
        Args:
            partner_id: Partner identifier
            updates: Dictionary containing updates
        Returns:
            Updated Partner object
        """
        partner = self.get_partner(partner_id)
        if partner is None:
            raise Exception("Partner not found")

        try:
            # Update partner attributes
            for key, value in updates.items():
                if hasattr(partner, key):
                    setattr(partner, key, value)

            # Reassess risks if relevant fields are updated
            risk_related_fields = {'expertise', 'experience', 'resources', 'past_collaborations'}
            if any(field in updates for field in risk_related_fields):
                partner.risk_assessment = self._assess_partner_risks(asdict(partner))

            partner.updated_at = datetime.now().isoformat()
            self._save_partner(partner)
            return partner

        except Exception as e:
            raise Exception(f"Failed to update partner: {str(e)}")

    def update_collaboration(self, collaboration_id: str, updates: Dict) -> Collaboration:
        """
        Update collaboration information
        Args:
            collaboration_id: Collaboration identifier
            updates: Dictionary containing updates
        Returns:
            Updated Collaboration object
        """
        collaboration = self.get_collaboration(collaboration_id)
        if collaboration is None:
            raise Exception("Collaboration not found")

        try:
            # Update collaboration attributes
            for key, value in updates.items():
                if hasattr(collaboration, key):
                    setattr(collaboration, key, value)

            # Reassess risks if relevant fields are updated
            if any(field in updates for field in ['responsibilities', 'resources_committed', 'timeline']):
                collaboration.risks = self._assess_collaboration_risks(asdict(collaboration))

            collaboration.updated_at = datetime.now().isoformat()
            self._save_collaboration(collaboration)
            return collaboration

        except Exception as e:
            raise Exception(f"Failed to update collaboration: {str(e)}")

    def get_partner(self, partner_id: str) -> Optional[Partner]:
        """
        Retrieve partner by ID
        Args:
            partner_id: Partner identifier
        Returns:
            Partner object if found, None otherwise
        """
        partner_file = os.path.join(self.partners_dir, f"{partner_id}.json")
        if not os.path.exists(partner_file):
            return None

        try:
            with open(partner_file, 'r') as f:
                data = json.load(f)
                return Partner(**data)
        except Exception as e:
            raise Exception(f"Failed to load partner: {str(e)}")

    def get_collaboration(self, collaboration_id: str) -> Optional[Collaboration]:
        """
        Retrieve collaboration by ID
        Args:
            collaboration_id: Collaboration identifier
        Returns:
            Collaboration object if found, None otherwise
        """
        collaboration_file = os.path.join(self.collaborations_dir, f"{collaboration_id}.json")
        if not os.path.exists(collaboration_file):
            return None

        try:
            with open(collaboration_file, 'r') as f:
                data = json.load(f)
                return Collaboration(**data)
        except Exception as e:
            raise Exception(f"Failed to load collaboration: {str(e)}")

    def _assess_partner_risks(self, partner_data: Dict) -> Dict[str, str]:
        """Assess risks associated with partner"""
        risks = {}

        # Assess expertise match
        expertise_coverage = len(partner_data['expertise']) / 5  # Assuming 5 is ideal
        risks['expertise_risk'] = 'low' if expertise_coverage >= 0.8 else 'medium' if expertise_coverage >= 0.5 else 'high'

        # Assess experience
        total_experience = sum(len(exp) for exp in partner_data['experience'].values())
        risks['experience_risk'] = 'low' if total_experience >= 10 else 'medium' if total_experience >= 5 else 'high'

        # Assess resource capacity
        resource_capacity = sum(partner_data.get('resources', {}).values())
        risks['resource_risk'] = 'low' if resource_capacity >= 1000000 else 'medium' if resource_capacity >= 500000 else 'high'

        # Assess past collaboration performance
        past_collaborations = partner_data.get('past_collaborations', [])
        successful_collaborations = len([c for c in past_collaborations if c.get('outcome') == 'successful'])
        collaboration_success_rate = successful_collaborations / len(past_collaborations) if past_collaborations else 0
        risks['collaboration_risk'] = 'low' if collaboration_success_rate >= 0.8 else 'medium' if collaboration_success_rate >= 0.5 else 'high'

        return risks

    def _assess_collaboration_risks(self, collaboration_data: Dict) -> List[Dict]:
        """Assess risks in collaboration"""
        risks = []

        # Assess timeline risks
        timeline = collaboration_data['timeline']
        if int(timeline['end_date'][:4]) - int(timeline['start_date'][:4]) > 2:
            risks.append({
                'type': 'timeline',
                'level': 'medium',
                'description': 'Long project duration increases complexity and risk'
            })

        # Assess resource commitment risks
        resources = collaboration_data.get('resources_committed', {})
        if sum(resources.values()) > 1000000:
            risks.append({
                'type': 'resource',
                'level': 'high',
                'description': 'High resource commitment requires careful monitoring'
            })

        # Assess responsibility risks
        responsibilities = collaboration_data['responsibilities']
        if len(responsibilities) > 5:
            risks.append({
                'type': 'responsibility',
                'level': 'medium',
                'description': 'Multiple responsibilities may impact delivery quality'
            })

        # Assess deliverable risks
        deliverables = collaboration_data['deliverables']
        if len(deliverables) > 10:
            risks.append({
                'type': 'deliverable',
                'level': 'high',
                'description': 'Large number of deliverables increases complexity'
            })

        return risks

    def _save_partner(self, partner: Partner):
        """Save partner data to file"""
        partner_file = os.path.join(self.partners_dir, f"{partner.id}.json")
        with open(partner_file, 'w') as f:
            json.dump(asdict(partner), f, indent=2)

    def _save_collaboration(self, collaboration: Collaboration):
        """Save collaboration data to file"""
        collaboration_file = os.path.join(self.collaborations_dir, f"{collaboration.id}.json")
        with open(collaboration_file, 'w') as f:
            json.dump(asdict(collaboration), f, indent=2)

    def analyze_partnership_potential(self, partner_id: str, proposal_requirements: Dict) -> Dict:
        """
        Analyze potential partnership fit
        Args:
            partner_id: Partner identifier
            proposal_requirements: Dictionary containing proposal requirements
        Returns:
            Dictionary containing analysis results
        """
        partner = self.get_partner(partner_id)
        if partner is None:
            raise Exception("Partner not found")

        # Calculate expertise match
        required_expertise = set(proposal_requirements.get('expertise', []))
        partner_expertise = set(partner.expertise)
        expertise_match = len(required_expertise.intersection(partner_expertise)) / len(required_expertise) if required_expertise else 0

        # Calculate sector alignment
        sector_match = 1 if partner.sector == proposal_requirements.get('sector') else 0

        # Calculate resource match
        required_resources = proposal_requirements.get('resources', {})
        resource_match = sum(
            min(partner.resources.get(resource, 0) / amount, 1)
            for resource, amount in required_resources.items()
        ) / len(required_resources) if required_resources else 0

        # Calculate risk score
        risk_levels = {'low': 1, 'medium': 2, 'high': 3}
        risk_score = sum(risk_levels[level] for level in partner.risk_assessment.values()) / len(partner.risk_assessment)

        # Calculate overall compatibility score
        compatibility_score = (
            expertise_match * 0.4 +
            sector_match * 0.2 +
            resource_match * 0.2 +
            (1 - (risk_score / 3)) * 0.2
        ) * 100

        return {
            'partner_id': partner.id,
            'partner_name': partner.name,
            'compatibility_score': compatibility_score,
            'analysis': {
                'expertise_match': {
                    'score': expertise_match * 100,
                    'matching_expertise': list(required_expertise.intersection(partner_expertise)),
                    'missing_expertise': list(required_expertise - partner_expertise)
                },
                'sector_alignment': {
                    'score': sector_match * 100,
                    'partner_sector': partner.sector,
                    'required_sector': proposal_requirements.get('sector')
                },
                'resource_capacity': {
                    'score': resource_match * 100,
                    'available_resources': partner.resources,
                    'required_resources': required_resources
                },
                'risk_assessment': {
                    'score': ((3 - risk_score) / 2) * 100,
                    'details': partner.risk_assessment
                }
            },
            'recommendation': self._generate_partnership_recommendation(compatibility_score)
        }

    def _generate_partnership_recommendation(self, compatibility_score: float) -> Dict:
        """Generate partnership recommendation based on compatibility score"""
        if compatibility_score >= 80:
            return {
                'status': 'highly_recommended',
                'message': 'Strong potential for successful partnership',
                'suggested_role': 'primary_partner'
            }
        elif compatibility_score >= 60:
            return {
                'status': 'recommended',
                'message': 'Good potential with some areas for attention',
                'suggested_role': 'supporting_partner'
            }
        elif compatibility_score >= 40:
            return {
                'status': 'conditional',
                'message': 'Partnership possible with risk mitigation measures',
                'suggested_role': 'specialized_contributor'
            }
        else:
            return {
                'status': 'not_recommended',
                'message': 'Significant gaps in compatibility',
                'suggested_role': 'none'
            } 