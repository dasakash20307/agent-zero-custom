"""
Project Detector for Project Management Instrument
Handles project type detection and context analysis
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ProjectContext:
    """Project context data structure"""
    project_type: str
    domain: str
    requirements: List[str]
    stakeholders: List[str]
    estimated_duration: str
    complexity_level: str
    risk_level: str

class ProjectDetector:
    def __init__(self, knowledge_base_path: str):
        """
        Initialize project detector
        Args:
            knowledge_base_path: Path to knowledge base directory
        """
        self.knowledge_base_path = knowledge_base_path
        self.domains_file = os.path.join(knowledge_base_path, 'organization/domains.md')
        self.project_types = {
            'rural_development': {
                'keywords': ['village', 'rural', 'agriculture', 'watershed', 'infrastructure'],
                'complexity': 'high',
                'typical_duration': '2-3 years'
            },
            'livelihood': {
                'keywords': ['skill', 'training', 'enterprise', 'income', 'employment'],
                'complexity': 'medium',
                'typical_duration': '1-2 years'
            },
            'environmental': {
                'keywords': ['conservation', 'climate', 'sustainable', 'green', 'environment'],
                'complexity': 'high',
                'typical_duration': '2-3 years'
            },
            'social_development': {
                'keywords': ['education', 'health', 'community', 'social', 'awareness'],
                'complexity': 'medium',
                'typical_duration': '1-2 years'
            }
        }

    def detect_project_type(self, description: str, objectives: List[str]) -> str:
        """
        Detect project type based on description and objectives
        Args:
            description: Project description
            objectives: List of project objectives
        Returns:
            Detected project type
        """
        text = description.lower() + ' ' + ' '.join(objectives).lower()
        scores = {ptype: 0 for ptype in self.project_types}

        # Score each project type based on keyword matches
        for ptype, info in self.project_types.items():
            for keyword in info['keywords']:
                if keyword in text:
                    scores[ptype] += 1

        # Return the project type with highest score
        return max(scores.items(), key=lambda x: x[1])[0]

    def analyze_context(self, description: str, objectives: List[str]) -> ProjectContext:
        """
        Analyze project context and requirements
        Args:
            description: Project description
            objectives: List of project objectives
        Returns:
            ProjectContext object
        """
        project_type = self.detect_project_type(description, objectives)
        type_info = self.project_types[project_type]

        # Determine domain based on project type
        domain = self._determine_domain(project_type)

        # Analyze requirements
        requirements = self._analyze_requirements(project_type, objectives)

        # Identify stakeholders
        stakeholders = self._identify_stakeholders(description, objectives)

        # Assess complexity and risk
        complexity = type_info['complexity']
        risk_level = self._assess_risk_level(description, objectives)

        return ProjectContext(
            project_type=project_type,
            domain=domain,
            requirements=requirements,
            stakeholders=stakeholders,
            estimated_duration=type_info['typical_duration'],
            complexity_level=complexity,
            risk_level=risk_level
        )

    def _determine_domain(self, project_type: str) -> str:
        """Map project type to specific domain"""
        domain_mapping = {
            'rural_development': 'Rural Development',
            'livelihood': 'Livelihood Programs',
            'environmental': 'Environmental Conservation',
            'social_development': 'Social Development'
        }
        return domain_mapping.get(project_type, 'General')

    def _analyze_requirements(self, project_type: str, objectives: List[str]) -> List[str]:
        """Analyze and determine project requirements"""
        common_reqs = ['Project team', 'Budget allocation', 'Timeline']
        type_specific_reqs = {
            'rural_development': [
                'Land survey',
                'Resource mapping',
                'Community consultation'
            ],
            'livelihood': [
                'Skills assessment',
                'Market analysis',
                'Training facilities'
            ],
            'environmental': [
                'Environmental impact assessment',
                'Conservation plan',
                'Sustainability analysis'
            ],
            'social_development': [
                'Community needs assessment',
                'Stakeholder mapping',
                'Impact evaluation framework'
            ]
        }
        return common_reqs + type_specific_reqs.get(project_type, [])

    def _identify_stakeholders(self, description: str, objectives: List[str]) -> List[str]:
        """Identify project stakeholders"""
        common_stakeholders = ['Project Team', 'Community Members', 'Local Government']
        text = description.lower() + ' ' + ' '.join(objectives).lower()

        additional_stakeholders = []
        stakeholder_keywords = {
            'farmer': 'Farmers',
            'women': 'Women Groups',
            'youth': 'Youth Groups',
            'student': 'Students',
            'teacher': 'Teachers',
            'business': 'Local Businesses'
        }

        for keyword, stakeholder in stakeholder_keywords.items():
            if keyword in text:
                additional_stakeholders.append(stakeholder)

        return list(set(common_stakeholders + additional_stakeholders))

    def _assess_risk_level(self, description: str, objectives: List[str]) -> str:
        """Assess project risk level"""
        text = description.lower() + ' ' + ' '.join(objectives).lower()
        
        high_risk_keywords = ['complex', 'challenging', 'uncertain', 'dependent']
        medium_risk_keywords = ['coordination', 'multiple', 'stakeholder']
        
        high_risk_count = sum(1 for word in high_risk_keywords if word in text)
        medium_risk_count = sum(1 for word in medium_risk_keywords if word in text)

        if high_risk_count >= 2:
            return 'High'
        elif high_risk_count == 1 or medium_risk_count >= 2:
            return 'Medium'
        else:
            return 'Low' 