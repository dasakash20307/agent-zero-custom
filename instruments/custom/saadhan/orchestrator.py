"""
Orchestrator module for integrating and managing all Saadhan AI Assistant instruments.
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import json
import logging
from dataclasses import dataclass

from .file_management.file_manager import FileManager
from .template_management.template_manager import TemplateManager
from .project_management.project_manager import ProjectManager
from .research.research_manager import ResearchManager
from .organization_identity.identity_manager import IdentityManager
from .user_analysis.pattern_analyzer import UserPatternAnalyzer
from .project_management.project_detector import ProjectDetector


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
        self.file_manager = FileManager(config.base_dir)
        self.template_manager = TemplateManager(str(config.base_dir))
        self.project_manager = ProjectManager(config.base_dir)
        self.research_manager = ResearchManager(config.base_dir)

        # Initialize organization identity components
        self.identity_manager = IdentityManager(str(config.base_dir))
        self.pattern_analyzer = UserPatternAnalyzer(str(config.base_dir))

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
            return {'error': str(e)}

    def process_interaction(self, user_id: str, content: str,
                            interaction_type: str = "general") -> None:
        """
        Process and analyze user interaction
        
        Args:
            user_id: User ID
            content: Interaction content
            interaction_type: Type of interaction (e.g., 'general',
                              'project', 'research')
        """
        try:
            # Analyze interaction pattern
            self.pattern_analyzer.analyze_task(
                user_id=user_id,
                task_type=interaction_type,
                task_content=content
            )
            
            # Update identity context if employee
            if self.identity_manager.is_employee(user_id):
                self.identity_manager.update_user_interaction(
                    user_id, interaction_type, content
                )
            
            self.logger.info(
                f"Processed interaction for user {user_id} "
                f"of type {interaction_type}"
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to process interaction for user {user_id}: {str(e)}"
            )
            self.handle_errors(e)

    def get_intelligent_suggestions(self, user_id: str) -> Dict[str, Any]:
        """
        Get intelligent suggestions based on user patterns
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary containing suggestions and preferences
        """
        try:
            # Get task suggestions
            task_suggestions = self.pattern_analyzer.suggest_tasks(user_id)
            
            # Get user preferences
            preferences = self.pattern_analyzer.get_user_preferences(user_id)
            
            # Get identity context if employee
            identity_context = {}
            if self.identity_manager.is_employee(user_id):
                employee_profile = self.identity_manager.get_employee_context(user_id)
                if employee_profile:
                    identity_context = employee_profile.__dict__
            
            current_time = datetime.now()
            
            # Combine all insights
            return {
                'task_suggestions': task_suggestions,
                'user_preferences': preferences,
                'identity_context': identity_context,
                'timestamp': current_time.isoformat()
            }
            
        except Exception as e:
            current_time = datetime.now()
            self.logger.error(
                f"Failed to get suggestions for user {user_id}: {str(e)}"
            )
            return {
                'error': str(e),
                'timestamp': current_time.isoformat()
            }
    
    def update_user_privacy(self, user_id: str, settings: Dict[str, bool]) -> None:
        """
        Update user privacy settings
        
        Args:
            user_id: User ID
            settings: Dictionary of privacy settings
        """
        try:
            # Update privacy settings
            self.pattern_analyzer.update_privacy_settings(user_id, settings)
            
            self.logger.info(f"Updated privacy settings for user {user_id}")
            
        except Exception as e:
            self.logger.error(
                f"Failed to update privacy settings for user {user_id}: {str(e)}"
            )
            self.handle_errors(e)

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
                'generated_at': datetime.now().isoformat()
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
        timestamp = datetime.now().isoformat()
        
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

    def get_greeting(self, employee_id: Optional[str] = None) -> str:
        """
        Get appropriate greeting
        Args:
            employee_id: Employee ID (optional)
        Returns:
            Greeting string
        """
        if employee_id:
            return self.identity_manager.get_greeting(employee_id)
        return "Greetings Superior"

    def add_employee(self, name: str, designation: str, department: str) -> Dict[str, Any]:
        """
        Add a new employee to the system
        Args:
            name: Employee name
            designation: Employee's designation
            department: Employee's department
        Returns:
            Dictionary containing employee ID
        """
        try:
            employee = self.identity_manager.add_employee(name, designation, department)
            self.logger.info(f"Added employee {name} with ID {employee.id}")
            return {'employee_id': employee.id}
        except Exception as e:
            self.logger.error(f"Failed to add employee: {str(e)}")
            return {'error': str(e)}

    def add_user(self, name: str) -> Dict[str, Any]:
        """
        Add a new user to the system
        Args:
            name: User's name
        Returns:
            Dictionary containing user ID
        """
        try:
            user = self.identity_manager.add_user(name)
            self.logger.info(f"Added user {name} with ID {user.id}")
            return {'user_id': user.id}
        except Exception as e:
            self.logger.error(f"Failed to add user: {str(e)}")
            return {'error': str(e)}


class TaskOrchestrator:
    """
    Handles task orchestration and delegation
    """
    
    def __init__(self, workspace_root: Union[str, Path]):
        self.workspace_root = Path(workspace_root)
        self.file_manager = FileManager(self.workspace_root)
        self.project_manager = ProjectManager(self.workspace_root)
        self.project_detector = ProjectDetector(str(self.workspace_root))
        self.template_manager = TemplateManager(str(self.workspace_root))
        
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
            objectives: List of task objectives
            deadline: Task deadline (ISO format datetime)
            priority: Task priority
        Returns:
            Created TaskDefinition object
        """
        task_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        updated_at = datetime.now().isoformat()
        
        metrics = self.evaluate_task(description, objectives)
        complexity = self._determine_complexity(metrics)
        
        task = TaskDefinition(
            id=task_id,
            title=title,
            description=description,
            complexity=complexity,
            priority=priority,
            deadline=deadline,
            metrics=metrics,
            status='pending',
            parent_id=None,
            created_at=created_at,
            updated_at=updated_at
        )
        self.tasks[task_id] = task
        return task
    
    def create_subtask(self, parent_id: str, title: str, description: str,
                       objectives: List[str], deadline: str) -> TaskDefinition:
        """
        Create a subtask for an existing task
        Args:
            parent_id: ID of the parent task
            title: Subtask title
            description: Subtask description
            objectives: List of subtask objectives
            deadline: Subtask deadline (ISO format datetime)
        Returns:
            Created TaskDefinition object
        """
        parent_task = self.get_task(parent_id)
        if not parent_task:
            raise ValueError(f"Parent task {parent_id} not found")
        
        subtask = self.create_task(title, description, objectives, deadline)
        subtask.parent_id = parent_id
        
        if parent_id not in self.task_dependencies:
            self.task_dependencies[parent_id] = []
        self.task_dependencies[parent_id].append(subtask.id)
        
        return subtask
    
    def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        """
        Get a task by ID
        Args:
            task_id: Task ID
        Returns:
            TaskDefinition object if found, None otherwise
        """
        return self.tasks.get(task_id)
    
    def list_tasks(self, status: Optional[str] = None) -> List[TaskDefinition]:
        """
        List all tasks, optionally filtered by status
        Args:
            status: Optional status filter
        Returns:
            List of TaskDefinition objects
        """
        if status:
            return [task for task in self.tasks.values() if task.status == status]
        return list(self.tasks.values())
    
    def update_task_status(self, task_id: str, status: str) -> TaskDefinition:
        """
        Update task status
        Args:
            task_id: Task ID
            status: New status
        Returns:
            Updated TaskDefinition object
        Raises:
            ValueError: If task not found
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        task.status = status
        task.updated_at = datetime.now().isoformat()
        return task
    
    def get_dependent_tasks(self, task_id: str) -> List[TaskDefinition]:
        """
        Get tasks that depend on the given task
        Args:
            task_id: Task ID
        Returns:
            List of TaskDefinition objects
        """
        dependent_ids = self.task_dependencies.get(task_id, [])
        return [self.tasks[dep_id] for dep_id in dependent_ids if dep_id in self.tasks]

    def get_task_chain(self, task_id: str) -> List[TaskDefinition]:
        """
        Get the entire chain of parent tasks for a given task
        Args:
            task_id: Task ID
        Returns:
            List of TaskDefinition objects in the chain
            (from oldest parent to current)
        """
        chain = []
        current_task = self.get_task(task_id)
        while current_task:
            chain.insert(0, current_task)  # Add to the beginning to maintain order
            if current_task.parent_id:
                current_task = self.get_task(current_task.parent_id)
            else:
                break
        return chain

    def _determine_complexity(self, metrics: TaskMetrics) -> str:
        """
        Determine task complexity based on metrics
        Args:
            metrics: TaskMetrics object
        Returns:
            str: Complexity level ('low', 'medium', 'high')
        """
        if metrics.context_size > 10 or metrics.memory_usage > 1000 or metrics.processing_time > 60:
            return 'high'
        elif metrics.context_size > 5 or metrics.memory_usage > 500 or metrics.processing_time > 30:
            return 'medium'
        else:
            return 'low'