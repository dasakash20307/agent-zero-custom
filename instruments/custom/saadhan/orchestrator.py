"""
Orchestrator module for integrating and managing all Saadhan AI Assistant instruments.
"""
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import json
import datetime
import logging
from dataclasses import dataclass
import uuid
from datetime import datetime, timedelta

from .file_management import FileManager
from .template_management import TemplateManager
from .project_management import ProjectManager, ProjectDetector
from .research import ResearchManager

@dataclass
class WorkspaceConfig:
    """Configuration for workspace."""
    base_dir: Path
    backup_dir: Optional[Path] = None
    version_dir: Optional[Path] = None
    template_dir: Optional[Path] = None
    project_dir: Optional[Path] = None
    research_dir: Optional[Path] = None

@dataclass
class TaskMetrics:
    """Task evaluation metrics"""
    context_size: int  # Estimated context window size needed
    memory_usage: int  # Estimated memory requirement in MB
    processing_time: int  # Estimated processing time in minutes
    api_calls: int  # Estimated number of API calls
    dependencies: List[str]  # List of dependent task IDs
    
@dataclass
class TaskDefinition:
    """Task definition structure"""
    id: str
    title: str
    description: str
    complexity: str  # 'low', 'medium', 'high'
    priority: int  # 1-5, 5 being highest
    deadline: str  # ISO format datetime
    metrics: TaskMetrics
    status: str  # 'pending', 'in_progress', 'completed', 'failed'
    parent_id: Optional[str]  # Parent task ID if this is a subtask
    created_at: str
    updated_at: str

class Orchestrator:
    """Manages and coordinates all instruments"""
    
    def __init__(self, config: WorkspaceConfig):
        """
        Initialize orchestrator
        Args:
            config: Workspace configuration
        """
        self.config = config
        self._ensure_directories()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize instruments
        self.file_manager = FileManager(str(config.base_dir))
        self.template_manager = TemplateManager(str(config.base_dir))
        self.project_manager = ProjectManager(str(config.base_dir))
        self.research_manager = ResearchManager(str(config.base_dir))
        self.project_detector = ProjectDetector(str(config.base_dir))
        
        self.logger.info("Orchestrator initialized successfully")
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        for directory in [
            self.config.base_dir,
            self.config.backup_dir,
            self.config.version_dir,
            self.config.template_dir,
            self.config.project_dir,
            self.config.research_dir
        ]:
            if directory:
                directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger("saadhan.orchestrator")
        self.logger.setLevel(logging.INFO)
        
        # Create handlers
        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(
            self.config.base_dir / "logs" / "orchestrator.log"
        )
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def initialize_workspace(self) -> bool:
        """
        Initialize workspace structure
        Returns:
            bool indicating success
        """
        try:
            # Create organization profile
            org_profile = {
                'name': 'Dilasa Janvikas Pratishthan',
                'description': 'Non-profit organization focused on community development',
                'domains': [
                    'Watershed Development',
                    'Sustainable Agriculture',
                    'Community Empowerment',
                    'Rural Development'
                ],
                'established': '1994',
                'location': 'Maharashtra, India'
            }
            
            profile_path = self.config.base_dir / "knowledge" / "organization" / "profile.json"
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(org_profile, f, indent=2)
            
            self.logger.info("Workspace initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize workspace: {str(e)}")
            return False
    
    def create_project(self, title: str, description: str,
                      start_date: str, end_date: str,
                      objectives: List[str], methodology: str) -> Dict[str, Any]:
        """
        Create a new project with associated research
        Args:
            title: Project title
            description: Project description
            start_date: Start date
            end_date: End date
            objectives: Project objectives
            methodology: Project methodology
        Returns:
            Dictionary containing project and research IDs
        """
        try:
            # Create project
            project = self.project_manager.create_project(
                title=title,
                description=description,
                start_date=start_date,
                end_date=end_date
            )
            
            # Create associated research
            research = self.research_manager.create_research(
                title=f"Research: {title}",
                description=description,
                objectives=objectives,
                methodology=methodology
            )
            
            # Link project and research
            self.project_manager.update_project(
                project.id,
                {'metadata': {'research_id': research.id}}
            )
            
            self.research_manager.update_research(
                research.id,
                {'metadata': {'project_id': project.id}}
            )
            
            self.logger.info(
                f"Created project '{title}' with ID {project.id} "
                f"and research ID {research.id}"
            )
            
            return {
                'project_id': project.id,
                'research_id': research.id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create project: {str(e)}")
            raise
    
    def generate_report(self, project_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive project report
        Args:
            project_id: Project ID
        Returns:
            Dictionary containing report data
        """
        try:
            # Get project data
            project = self.project_manager.get_project(project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")
            
            # Get associated research
            research_id = project.metadata.get('research_id')
            research_data = None
            if research_id:
                research = self.research_manager.get_research(research_id)
                if research:
                    research_data = self.research_manager.generate_report(research_id)
            
            # Generate project report
            project_data = self.project_manager.generate_report(project_id)
            
            # Combine reports
            report = {
                'project': project_data,
                'research': research_data,
                'generated_at': datetime.datetime.now().isoformat()
            }
            
            self.logger.info(f"Generated report for project {project_id}")
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {str(e)}")
            raise
    
    def handle_errors(self, error: Exception) -> Dict[str, Any]:
        """
        Handle and log errors
        Args:
            error: Exception object
        Returns:
            Dictionary containing error details
        """
        error_id = str(hash(str(error)))
        timestamp = datetime.datetime.now().isoformat()
        
        error_data = {
            'error_id': error_id,
            'timestamp': timestamp,
            'type': type(error).__name__,
            'message': str(error),
            'details': getattr(error, 'details', None)
        }
        
        # Log error
        self.logger.error(
            f"Error {error_id}: {type(error).__name__} - {str(error)}"
        )
        
        # Save error details
        error_path = self.config.base_dir / "logs" / "errors" / f"{error_id}.json"
        error_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(error_path, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2)
        
        return error_data

class TaskOrchestrator:
    """Handles task orchestration and delegation"""
    
    def __init__(self, workspace_root: Union[str, Path]):
        self.workspace_root = Path(workspace_root)
        self.file_manager = FileManager(str(workspace_root))
        self.project_manager = ProjectManager(workspace_root)
        self.project_detector = ProjectDetector(str(workspace_root))
        self.template_manager = TemplateManager(str(workspace_root))
        
        # Initialize task storage
        self.tasks: Dict[str, TaskDefinition] = {}
        self.task_dependencies: Dict[str, List[str]] = {}
        
    def evaluate_task(self, description: str, objectives: List[str]) -> TaskMetrics:
        """
        Evaluate task complexity and requirements
        Args:
            description: Task description
            objectives: List of objectives
        Returns:
            TaskMetrics object
        """
        # Estimate context size based on description and objectives length
        total_chars = len(description) + sum(len(obj) for obj in objectives)
        context_size = total_chars // 500  # Rough estimate: 500 chars per context window
        
        # Estimate memory based on context size
        memory_usage = context_size * 100  # 100MB per context window
        
        # Estimate processing time based on objectives
        processing_time = len(objectives) * 5  # 5 minutes per objective
        
        # Estimate API calls based on objectives
        api_calls = len(objectives) * 2  # 2 API calls per objective
        
        return TaskMetrics(
            context_size=context_size,
            memory_usage=memory_usage,
            processing_time=processing_time,
            api_calls=api_calls,
            dependencies=[]
        )
    
    def create_task(self, title: str, description: str, objectives: List[str],
                    deadline: str, priority: int = 3) -> TaskDefinition:
        """
        Create a new task
        Args:
            title: Task title
            description: Task description
            objectives: List of objectives
            deadline: Deadline in ISO format
            priority: Priority level (1-5)
        Returns:
            Created TaskDefinition
        """
        # Evaluate task requirements
        metrics = self.evaluate_task(description, objectives)
        
        # Determine complexity based on metrics
        complexity = self._determine_complexity(metrics)
        
        # Create task
        task = TaskDefinition(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            complexity=complexity,
            priority=priority,
            deadline=deadline,
            metrics=metrics,
            status='pending',
            parent_id=None,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Store task
        self.tasks[task.id] = task
        
        return task
    
    def create_subtask(self, parent_id: str, title: str, description: str,
                      objectives: List[str], deadline: str) -> TaskDefinition:
        """Create a subtask under a parent task"""
        parent_task = self.tasks.get(parent_id)
        if not parent_task:
            raise ValueError(f"Parent task not found: {parent_id}")
        
        # Create subtask with parent reference
        subtask = self.create_task(title, description, objectives, deadline)
        subtask.parent_id = parent_id
        
        # Update task
        self.tasks[subtask.id] = subtask
        
        # Update dependencies
        if parent_id not in self.task_dependencies:
            self.task_dependencies[parent_id] = []
        self.task_dependencies[parent_id].append(subtask.id)
        
        return subtask
    
    def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, status: Optional[str] = None) -> List[TaskDefinition]:
        """List all tasks, optionally filtered by status"""
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks
    
    def update_task_status(self, task_id: str, status: str) -> TaskDefinition:
        """Update task status"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        task.status = status
        task.updated_at = datetime.now().isoformat()
        
        return task
    
    def get_dependent_tasks(self, task_id: str) -> List[TaskDefinition]:
        """Get list of tasks that depend on the given task"""
        dependent_ids = self.task_dependencies.get(task_id, [])
        return [self.tasks[tid] for tid in dependent_ids if tid in self.tasks]
    
    def get_task_chain(self, task_id: str) -> List[TaskDefinition]:
        """Get chain of tasks from root to the given task"""
        task = self.tasks.get(task_id)
        if not task:
            return []
        
        chain = [task]
        while task.parent_id:
            parent = self.tasks.get(task.parent_id)
            if parent:
                chain.insert(0, parent)
                task = parent
            else:
                break
        
        return chain
    
    def _determine_complexity(self, metrics: TaskMetrics) -> str:
        """Determine task complexity based on metrics"""
        # Score different aspects
        context_score = 1 if metrics.context_size <= 2 else 2 if metrics.context_size <= 5 else 3
        memory_score = 1 if metrics.memory_usage <= 200 else 2 if metrics.memory_usage <= 500 else 3
        time_score = 1 if metrics.processing_time <= 15 else 2 if metrics.processing_time <= 30 else 3
        api_score = 1 if metrics.api_calls <= 5 else 2 if metrics.api_calls <= 10 else 3
        dependency_score = 1 if len(metrics.dependencies) <= 2 else 2 if len(metrics.dependencies) <= 5 else 3
        
        # Calculate average score
        avg_score = (context_score + memory_score + time_score + api_score + dependency_score) / 5
        
        # Map to complexity levels
        if avg_score <= 1.5:
            return 'low'
        elif avg_score <= 2.5:
            return 'medium'
        else:
            return 'high' 