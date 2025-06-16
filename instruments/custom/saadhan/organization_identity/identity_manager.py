"""
Identity Manager for handling Dilasa organization profiles and interactions.
"""
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any

@dataclass
class EmployeeProfile:
    """Class representing a Dilasa employee profile"""
    id: str
    name: str
    designation: str
    department: str
    interaction_patterns: List[str]
    last_interaction: str
    preferred_greeting: str

@dataclass
class UserProfile:
    """Class representing a user profile"""
    id: str
    name: str
    interaction_history: List[Dict[str, Any]]
    task_patterns: List[Dict[str, Any]]
    preferences: Dict[str, Any]
    last_interaction: str

class IdentityManager:
    """Manages Dilasa organization identities and interactions"""
    
    def __init__(self, workspace_root: str):
        """Initialize the identity manager
        
        Args:
            workspace_root: Root directory of the workspace
        """
        self.workspace_root = Path(workspace_root)
        self.employees_db = self.workspace_root / "knowledge/custom/dilasa/organization/employees.json"
        self.users_db = self.workspace_root / "knowledge/custom/dilasa/organization/users.json"
        
        # Create directories if they don't exist
        self.employees_db.parent.mkdir(parents=True, exist_ok=True)
        self.users_db.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty databases if they don't exist
        if not self.employees_db.exists():
            self._save_data(self.employees_db, {})
        if not self.users_db.exists():
            self._save_data(self.users_db, {})
    
    def add_employee(self, name: str, designation: str, department: str) -> EmployeeProfile:
        """Add a new employee profile
        
        Args:
            name: Employee name
            designation: Job designation
            department: Department name
            
        Returns:
            Created EmployeeProfile object
        """
        employee = EmployeeProfile(
            id=str(uuid.uuid4()),
            name=name,
            designation=designation,
            department=department,
            interaction_patterns=[],
            last_interaction=datetime.now().isoformat(),
            preferred_greeting=f"Mr./Ms. {name}"
        )
        self._save_employee(employee)
        return employee
    
    def add_user(self, name: str) -> UserProfile:
        """Add a new user profile
        
        Args:
            name: User name
            
        Returns:
            Created UserProfile object
        """
        user = UserProfile(
            id=str(uuid.uuid4()),
            name=name,
            interaction_history=[],
            task_patterns=[],
            preferences={},
            last_interaction=datetime.now().isoformat()
        )
        self._save_user(user)
        return user
    
    def update_interaction_pattern(self, employee_id: str, pattern: str) -> None:
        """Update employee interaction pattern
        
        Args:
            employee_id: Employee ID
            pattern: New interaction pattern
        """
        employee = self._load_employee(employee_id)
        if employee:
            employee.interaction_patterns.append(pattern)
            employee.last_interaction = datetime.now().isoformat()
            self._save_employee(employee)
    
    def update_user_interaction(self, user_id: str, interaction_type: str, 
                              content: str) -> None:
        """Update user interaction history
        
        Args:
            user_id: User ID
            interaction_type: Type of interaction
            content: Interaction content
        """
        user = self._load_user(user_id)
        if user:
            interaction = {
                "type": interaction_type,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            user.interaction_history.append(interaction)
            user.last_interaction = datetime.now().isoformat()
            self._save_user(user)
    
    def get_greeting(self, employee_id: str) -> str:
        """Get appropriate greeting for an employee
        
        Args:
            employee_id: Employee ID
            
        Returns:
            Greeting string
        """
        employee = self._load_employee(employee_id)
        if employee:
            return f"Greetings {employee.preferred_greeting}"
        return "Greetings Superior"
    
    def _load_employee(self, employee_id: str) -> Optional[EmployeeProfile]:
        """Load employee profile from database"""
        data = self._load_data(self.employees_db)
        if employee_id in data:
            return EmployeeProfile(**data[employee_id])
        return None
    
    def _load_user(self, user_id: str) -> Optional[UserProfile]:
        """Load user profile from database"""
        data = self._load_data(self.users_db)
        if user_id in data:
            return UserProfile(**data[user_id])
        return None
    
    def _save_employee(self, employee: EmployeeProfile) -> None:
        """Save employee profile to database"""
        data = self._load_data(self.employees_db)
        data[employee.id] = asdict(employee)
        self._save_data(self.employees_db, data)
    
    def _save_user(self, user: UserProfile) -> None:
        """Save user profile to database"""
        data = self._load_data(self.users_db)
        data[user.id] = asdict(user)
        self._save_data(self.users_db, data)
    
    def _load_data(self, file_path: Path) -> Dict:
        """Load data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_data(self, file_path: Path, data: Dict) -> None:
        """Save data to JSON file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def is_employee(self, user_id: str) -> bool:
        """Check if a user is an employee"""
        return self._load_employee(user_id) is not None

    def get_employee_context(self, employee_id: str) -> Optional[EmployeeProfile]:
        """Get employee profile by ID"""
        return self._load_employee(employee_id) 