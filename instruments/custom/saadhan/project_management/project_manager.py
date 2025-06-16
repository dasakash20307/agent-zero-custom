"""
Project Management module for handling project operations and tracking.
"""
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, cast
import json
import datetime
from dataclasses import dataclass, asdict
import uuid

from ..file_management import FileManager, VersionControl
from ..template_management import TemplateManager

@dataclass
class ProjectActivity:
    """Class representing a project activity"""
    id: str
    title: str
    description: str
    status: str
    start_date: str
    end_date: str
    progress: float
    resources: List[str]
    dependencies: List[str]
    created_at: str
    updated_at: str

@dataclass
class Beneficiary:
    """Class representing a project beneficiary"""
    id: str
    name: str
    type: str
    contact: str
    benefits: List[str]
    metrics: Dict[str, Any]

@dataclass
class Project:
    """Class representing a project"""
    id: str
    title: str
    description: str
    status: str
    start_date: str
    end_date: str
    progress: float
    activities: List[ProjectActivity]
    beneficiaries: List[Beneficiary]
    budget: Dict[str, float]
    team: List[str]
    documents: List[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str

class ProjectManager:
    """Handles project operations and management"""
    
    def __init__(self, workspace_root: Union[str, Path]):
        self.workspace_root = Path(workspace_root)
        self.projects_dir = self.workspace_root / "knowledge/custom/dilasa/projects"
        self.file_manager = FileManager(str(workspace_root))
        self.version_control = VersionControl(str(workspace_root))
        self.template_manager = TemplateManager(str(workspace_root))
        
        # Create projects directory if not exists
        self.projects_dir.mkdir(parents=True, exist_ok=True)
    
    def create_project(self, title: str, description: str, start_date: str,
                      end_date: str, metadata: Optional[Dict[str, Any]] = None) -> Project:
        """
        Create a new project
        Args:
            title: Project title
            description: Project description
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            metadata: Additional metadata
        Returns:
            Created Project object
        """
        # Generate project ID
        project_id = str(uuid.uuid4())
        
        # Create timestamp
        timestamp = datetime.datetime.now().isoformat()
        
        # Create project object
        project = Project(
            id=project_id,
            title=title,
            description=description,
            status='planned',
            start_date=start_date,
            end_date=end_date,
            progress=0.0,
            activities=[],
            beneficiaries=[],
            budget={},
            team=[],
            documents=[],
            metadata=metadata or {},
            created_at=timestamp,
            updated_at=timestamp
        )
        
        # Save project
        self._save_project(project)
        
        # Create version
        self.version_control.create_version(
            self._get_project_path(project_id),
            comment=f"Created project: {title}"
        )
        
        return project
    
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> Project:
        """
        Update an existing project
        Args:
            project_id: Project ID
            updates: Dictionary of updates
        Returns:
            Updated Project object
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        # Update fields
        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        # Update timestamp
        project.updated_at = datetime.datetime.now().isoformat()
        
        # Save project
        self._save_project(project)
        
        # Create version
        self.version_control.create_version(
            self._get_project_path(project_id),
            comment=f"Updated project: {project.title}"
        )
        
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a project by ID
        Args:
            project_id: Project ID
        Returns:
            Project object if found, None otherwise
        """
        project_path = self._get_project_path(project_id)
        if not project_path.exists():
            return None
        
        with open(project_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Convert activities and beneficiaries
            activities = [ProjectActivity(**a) for a in data.pop('activities', [])]
            beneficiaries = [Beneficiary(**b) for b in data.pop('beneficiaries', [])]
            
            # Create project object
            return Project(
                **data,
                activities=activities,
                beneficiaries=beneficiaries
            )
    
    def list_projects(self, status: Optional[str] = None) -> List[Project]:
        """
        List all projects, optionally filtered by status
        Args:
            status: Optional status filter
        Returns:
            List of Project objects
        """
        projects = []
        for project_file in self.projects_dir.glob('*.json'):
            project = self.get_project(project_file.stem)
            if project and (not status or project.status == status):
                projects.append(project)
        return projects
    
    def add_activity(self, project_id: str, title: str, description: str,
                    start_date: str, end_date: str, dependencies: Optional[List[str]] = None) -> ProjectActivity:
        """
        Add an activity to a project
        Args:
            project_id: Project ID
            title: Activity title
            description: Activity description
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            dependencies: List of dependent activity IDs
        Returns:
            Created ProjectActivity object
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        # Create activity
        activity = ProjectActivity(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            status='planned',
            start_date=start_date,
            end_date=end_date,
            progress=0.0,
            resources=[],
            dependencies=dependencies or [],
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat()
        )
        
        # Add to project
        project.activities.append(activity)
        
        # Update project
        self.update_project(project_id, {'activities': project.activities})
        
        return activity
    
    def add_beneficiary(self, project_id: str, name: str, type: str,
                       contact: str, benefits: List[str]) -> Beneficiary:
        """
        Add a beneficiary to a project
        Args:
            project_id: Project ID
            name: Beneficiary name
            type: Beneficiary type
            contact: Contact information
            benefits: List of benefits
        Returns:
            Created Beneficiary object
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        # Create beneficiary
        beneficiary = Beneficiary(
            id=str(uuid.uuid4()),
            name=name,
            type=type,
            contact=contact,
            benefits=benefits,
            metrics={}
        )
        
        # Add to project
        project.beneficiaries.append(beneficiary)
        
        # Update project
        self.update_project(project_id, {'beneficiaries': project.beneficiaries})
        
        return beneficiary
    
    def update_progress(self, project_id: str, activity_id: Optional[str] = None,
                       progress: float = 0.0) -> float:
        """
        Update project or activity progress
        Args:
            project_id: Project ID
            activity_id: Optional activity ID
            progress: New progress value (0-100)
        Returns:
            Updated progress value
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        if activity_id:
            # Update activity progress
            for activity in project.activities:
                if activity.id == activity_id:
                    activity.progress = progress
                    activity.updated_at = datetime.datetime.now().isoformat()
                    break
            
            # Calculate overall project progress
            if project.activities:
                project.progress = sum(a.progress for a in project.activities) / len(project.activities)
            
            # Update project
            self.update_project(project_id, {
                'activities': project.activities,
                'progress': project.progress
            })
            
            return progress
        else:
            # Update project progress directly
            project.progress = progress
            self.update_project(project_id, {'progress': progress})
            return progress
    
    def generate_report(self, project_id: str) -> Dict[str, Any]:
        """
        Generate project status report
        Args:
            project_id: Project ID
        Returns:
            Dictionary containing report data
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        # Prepare report data
        report_data = {
            'project_id': project.id,
            'title': project.title,
            'description': project.description,
            'status': project.status,
            'progress': f"{project.progress:.1f}%",
            'duration': {
                'start': project.start_date,
                'end': project.end_date
            },
            'activities': [
                {
                    'title': a.title,
                    'status': a.status,
                    'progress': f"{a.progress:.1f}%",
                    'period': f"{a.start_date} to {a.end_date}"
                }
                for a in project.activities
            ],
            'beneficiaries': [
                {
                    'name': b.name,
                    'type': b.type,
                    'benefits': b.benefits
                }
                for b in project.beneficiaries
            ],
            'budget': project.budget,
            'team': project.team,
            'last_updated': project.updated_at
        }
        
        # Get report template
        template_name = 'project_report'
        template = self.template_manager.get_template(template_name)
        if not template:
            return report_data
        
        # Render template with data
        rendered = self.template_manager.render_template(template_name, report_data)
        return cast(Dict[str, Any], rendered)
    
    def _save_project(self, project: Project) -> None:
        """Save project to file"""
        project_path = self._get_project_path(project.id)
        project_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(project_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(project), f, indent=2)
    
    def _get_project_path(self, project_id: str) -> Path:
        """Get path for project file"""
        return self.projects_dir / f"{project_id}.json" 