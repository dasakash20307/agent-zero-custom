"""
Enhanced Pattern Analyzer for automated background analysis of user interaction patterns.
"""
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, TypedDict, TypeVar, Sequence, cast
from collections import Counter, defaultdict
import re
from dataclasses import dataclass
import numpy as np
from scipy.stats import mode
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import logging

T = TypeVar('T', bound=Dict[str, Any])

@dataclass
class TaskContext:
    """Task context information"""
    dependencies: List[str]
    resources: List[str]
    priority: int
    time_constraints: Dict[str, str]
    related_tasks: List[str]

@dataclass
class ProjectContext:
    """Project context information"""
    phase: str
    goals: List[str]
    team: List[str]
    constraints: Dict[str, Any]
    timeline: Dict[str, str]

@dataclass
class UserContext:
    """User context information"""
    role: str
    expertise_level: str
    preferences: Dict[str, Any]
    communication_style: str
    task_history: Sequence[Dict[str, Any]]

class Pattern(Dict[str, Any]):
    """Pattern data structure"""
    def __init__(self, timestamp: str, task_type: str, content: str,
                 task_context: Dict[str, Any], project_context: Dict[str, Any],
                 user_context: Dict[str, Any]):
        super().__init__()
        self.update({
            "timestamp": timestamp,
            "task_type": task_type,
            "content": content,
            "task_context": task_context,
            "project_context": project_context,
            "user_context": user_context
        })

class Analysis(TypedDict):
    """Analysis data structure"""
    time_patterns: Dict[str, Any]
    task_patterns: Dict[str, Any]
    last_analyzed: str

class UserData(TypedDict):
    """User data structure"""
    patterns: List[Pattern]
    analysis: Analysis

class PatternRecognizer:
    """Advanced pattern recognition system"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def find_time_patterns(self, timestamps: Sequence[str]) -> Dict[str, Any]:
        """Find patterns in timestamp data"""
        hours = [datetime.fromisoformat(ts).hour for ts in timestamps]
        days = [datetime.fromisoformat(ts).weekday() for ts in timestamps]
        
        # Find peak hours
        peak_hours = mode(hours).mode.tolist()
        
        # Find day patterns
        day_distribution = Counter(days)
        
        # Find time clusters
        hour_array = np.array(hours).reshape(-1, 1)
        scaled_hours = self.scaler.fit_transform(hour_array)
        clusters = DBSCAN(eps=0.3, min_samples=2).fit(scaled_hours)
        
        return {
            "peak_hours": peak_hours,
            "day_distribution": dict(day_distribution),
            "time_clusters": len(set(clusters.labels_))
        }
    
    def find_task_patterns(self, tasks: Sequence[T]) -> Dict[str, Any]:
        """Find patterns in task data"""
        task_types = Counter(t["task_type"] for t in tasks)
        
        # Analyze task sequences
        sequences = self._extract_sequences(tasks)
        common_sequences = Counter(
            tuple(seq) for seq in sequences
        ).most_common(3)
        
        # Find task dependencies
        dependencies = self._extract_dependencies(tasks)
        
        return {
            "common_types": dict(task_types),
            "common_sequences": common_sequences,
            "dependencies": dependencies
        }
    
    def _extract_sequences(self, tasks: Sequence[T]) -> List[List[str]]:
        """Extract task sequences"""
        sequences = []
        current_seq = []
        
        for task in tasks:
            if not current_seq:
                current_seq.append(task["task_type"])
            else:
                time_diff = (
                    datetime.fromisoformat(task["timestamp"]) -
                    datetime.fromisoformat(tasks[len(current_seq)-1]["timestamp"])
                ).total_seconds()
                
                if time_diff < 3600:  # Tasks within 1 hour
                    current_seq.append(task["task_type"])
                else:
                    if len(current_seq) > 1:
                        sequences.append(current_seq)
                    current_seq = [task["task_type"]]
        
        if len(current_seq) > 1:
            sequences.append(current_seq)
            
        return sequences
    
    def _extract_dependencies(self, tasks: Sequence[T]) -> Dict[str, List[str]]:
        """Extract task dependencies"""
        dependencies = defaultdict(list)
        
        for i, task in enumerate(tasks[:-1]):
            next_task = tasks[i+1]
            time_diff = (
                datetime.fromisoformat(next_task["timestamp"]) -
                datetime.fromisoformat(task["timestamp"])
            ).total_seconds()
            
            if time_diff < 300:  # Tasks within 5 minutes
                dependencies[task["task_type"]].append(next_task["task_type"])
        
        return dict(dependencies)

class ContextExtractor:
    """Advanced context extraction system"""
    
    def extract_task_context(self, content: str) -> TaskContext:
        """Extract task context from content"""
        # Extract dependencies
        dependencies = re.findall(r"depends on|requires|after|following: ([^.]*)", content)
        
        # Extract resources
        resources = re.findall(r"using|with|requires: ([^.]*)", content)
        
        # Extract priority
        priority_match = re.search(r"priority:?\s*(\d+)", content)
        priority = int(priority_match.group(1)) if priority_match else 3
        
        # Extract time constraints
        time_constraints = {}
        deadline_match = re.search(r"deadline:?\s*([^.]*)", content)
        if deadline_match:
            time_constraints["deadline"] = deadline_match.group(1)
        
        # Extract related tasks
        related = re.findall(r"related to|similar to|like: ([^.]*)", content)
        
        return TaskContext(
            dependencies=dependencies,
            resources=resources,
            priority=priority,
            time_constraints=time_constraints,
            related_tasks=related
        )
    
    def extract_project_context(self, content: str) -> ProjectContext:
        """Extract project context from content"""
        # Extract phase
        phase_match = re.search(r"phase:?\s*([^.]*)", content)
        phase = phase_match.group(1) if phase_match else "unknown"
        
        # Extract goals
        goals = re.findall(r"goal|objective|aim: ([^.]*)", content)
        
        # Extract team
        team = re.findall(r"team|member|assigned to: ([^.]*)", content)
        
        # Extract constraints
        constraints = {}
        budget_match = re.search(r"budget:?\s*([^.]*)", content)
        if budget_match:
            constraints["budget"] = budget_match.group(1)
        
        # Extract timeline
        timeline = {}
        start_match = re.search(r"starts?:?\s*([^.]*)", content)
        if start_match:
            timeline["start"] = start_match.group(1)
        end_match = re.search(r"ends?:?\s*([^.]*)", content)
        if end_match:
            timeline["end"] = end_match.group(1)
        
        return ProjectContext(
            phase=phase,
            goals=goals,
            team=team,
            constraints=constraints,
            timeline=timeline
        )
    
    def extract_user_context(self, content: str, history: Sequence[Dict[str, Any]]) -> UserContext:
        """Extract user context from content and history"""
        # Extract role
        role_match = re.search(r"role|position|as a: ([^.]*)", content)
        role = role_match.group(1) if role_match else "unknown"
        
        # Determine expertise level from history
        task_complexity = [t.get("complexity", "medium") for t in history]
        expertise_level = mode(task_complexity).mode[0] if task_complexity else "medium"
        
        # Extract preferences from history
        preferences = {
            "preferred_time": mode([
                datetime.fromisoformat(t["timestamp"]).hour 
                for t in history
            ]).mode[0] if history else None,
            "preferred_tasks": Counter(
                t["task_type"] for t in history
            ).most_common(3) if history else []
        }
        
        # Analyze communication style
        communication_style = self._analyze_communication_style(content)
        
        return UserContext(
            role=role,
            expertise_level=expertise_level,
            preferences=preferences,
            communication_style=communication_style,
            task_history=history
        )
    
    def _analyze_communication_style(self, content: str) -> str:
        """Analyze communication style from content"""
        # Add communication style analysis logic
        # For now return default
        return "professional"

class UserPatternAnalyzer:
    """Analyzes and manages user interaction patterns automatically in background"""
    
    def __init__(self, workspace_root: str):
        """Initialize the pattern analyzer
        
        Args:
            workspace_root: Root directory of the workspace
        """
        self.workspace_root = Path(workspace_root)
        self.pattern_db = self.workspace_root / "knowledge/custom/dilasa/users/patterns.json"
        
        # Initialize components
        self.pattern_recognizer = PatternRecognizer()
        self.context_extractor = ContextExtractor()
        
        # Create directory if it doesn't exist
        self.pattern_db.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty database if it doesn't exist
        if not self.pattern_db.exists():
            self._save_data({})
            
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def analyze_task(self, user_id: str, task_type: str, task_content: str) -> None:
        """Silently analyze and store user task patterns in background
        
        Args:
            user_id: User ID
            task_type: Type of task
            task_content: Task content
        """
        try:
            # Extract context
            task_context = self.context_extractor.extract_task_context(task_content)
            project_context = self.context_extractor.extract_project_context(task_content)
            
            pattern = Pattern(
                timestamp=datetime.now().isoformat(),
                task_type=task_type,
                content=task_content,
                task_context=task_context.__dict__,
                project_context=project_context.__dict__,
                user_context={}  # Will be updated below
            )
            
            data = self._load_data()
            if user_id not in data:
                data[user_id] = {"patterns": [], "analysis": {
                    "time_patterns": {},
                    "task_patterns": {},
                    "last_analyzed": datetime.now().isoformat()
                }}
            
            data[user_id]["patterns"].append(pattern)
            
            # Extract user context with updated history
            user_context = self.context_extractor.extract_user_context(
                task_content, cast(List[Dict[str, Any]], data[user_id]["patterns"])
            )
            pattern["user_context"] = user_context.__dict__
            
            self._save_data(data)
            
            # Trigger background pattern analysis
            self._analyze_patterns_background(user_id)
        except Exception as e:
            # Silently log error without affecting user experience
            self.logger.error(f"Background analysis failed: {str(e)}")
    
    def suggest_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get intelligent task suggestions based on pattern analysis
        
        Args:
            user_id: User ID
            
        Returns:
            List of task suggestions
        """
        try:
            data = self._load_data()
            if user_id not in data or not data[user_id]["patterns"]:
                return []
            
            patterns = data[user_id]["patterns"]
            
            # Find time patterns
            time_patterns = self.pattern_recognizer.find_time_patterns([
                p["timestamp"] for p in patterns
            ])
            
            # Find task patterns
            task_patterns = self.pattern_recognizer.find_task_patterns(
                cast(List[Dict[str, Any]], patterns)
            )
            
            # Generate context-aware suggestions
            suggestions = []
            for task_type, frequency in task_patterns["common_types"].items():
                relevant_patterns = [
                    p for p in patterns 
                    if p["task_type"] == task_type
                ][-3:]
                
                contexts = [
                    {
                        "task": p["task_context"],
                        "project": p["project_context"],
                        "user": p["user_context"]
                    }
                    for p in relevant_patterns
                ]
                
                suggestions.append({
                    "task_type": task_type,
                    "frequency": frequency,
                    "time_patterns": time_patterns,
                    "task_patterns": task_patterns,
                    "contexts": contexts
                })
            
            return suggestions
        except Exception as e:
            self.logger.error(f"Failed to generate suggestions: {str(e)}")
            return []
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get automatically analyzed user preferences
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of user preferences
        """
        try:
            data = self._load_data()
            if user_id not in data or not data[user_id]["patterns"]:
                return {}
            
            patterns = data[user_id]["patterns"]
            
            # Analyze time patterns
            time_patterns = self.pattern_recognizer.find_time_patterns([
                p["timestamp"] for p in patterns
            ])
            
            # Analyze task patterns
            task_patterns = self.pattern_recognizer.find_task_patterns(
                cast(List[Dict[str, Any]], patterns)
            )
            
            # Get latest user context
            latest_context = patterns[-1]["user_context"]
            
            return {
                "time_patterns": time_patterns,
                "task_patterns": task_patterns,
                "user_context": latest_context,
                "total_interactions": len(patterns)
            }
        except Exception as e:
            self.logger.error(f"Failed to get preferences: {str(e)}")
            return {}
    
    def update_privacy_settings(self, user_id: str, settings: Dict[str, bool]) -> None:
        """Update user privacy settings.
        
        This is a placeholder for future implementation.
        """
        self.logger.info(
            f"Privacy settings update requested for user {user_id}: {settings} (placeholder)"
        )
    
    def _analyze_patterns_background(self, user_id: str) -> None:
        """Analyze patterns in background without blocking"""
        try:
            data = self._load_data()
            if user_id not in data:
                return
            
            patterns = data[user_id]["patterns"]
            
            # Analyze time patterns
            time_patterns = self.pattern_recognizer.find_time_patterns([
                p["timestamp"] for p in patterns
            ])
            
            # Analyze task patterns
            task_patterns = self.pattern_recognizer.find_task_patterns(
                cast(List[Dict[str, Any]], patterns)
            )
            
            # Store analysis results
            data[user_id]["analysis"] = {
                "time_patterns": time_patterns,
                "task_patterns": task_patterns,
                "last_analyzed": datetime.now().isoformat()
            }
            
            self._save_data(data)
        except Exception as e:
            self.logger.error(f"Background analysis failed: {str(e)}")
    
    def _load_data(self) -> Dict[str, UserData]:
        """Load pattern data from JSON file"""
        try:
            with open(self.pattern_db, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_data(self, data: Dict[str, UserData]) -> None:
        """Save pattern data to JSON file"""
        with open(self.pattern_db, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2) 