"""Research Manager module for managing research projects."""

import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, TypedDict
from dataclasses import dataclass, asdict, field

from ..file_management.file_manager import FileManager

class ResearchSource(TypedDict):
    """Research source type."""
    title: str
    url: str
    type: str
    description: str
    added_at: str

class ResearchFinding(TypedDict):
    """Research finding type."""
    title: str
    description: str
    evidence: str
    added_at: str

@dataclass
class Research:
    """Research project data class."""
    id: str
    title: str
    description: str
    objectives: List[str]
    methodology: str
    sources: List[ResearchSource]
    findings: List[ResearchFinding]
    created_at: str
    status: str = 'planned'
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    updated_at: Optional[str] = None

class ResearchManager:
    """Manager class for research projects."""
    
    def __init__(self, base_dir: Path):
        """Initialize research manager."""
        self.base_dir = Path(base_dir)
        self.research_dir = self.base_dir / "research"
        self.file_manager = FileManager(base_dir)
        self.research_dir.mkdir(parents=True, exist_ok=True)

    def create_research(self, title: str, description: str, objectives: List[str], methodology: str) -> Research:
        """Create a new research project."""
        research_id = str(uuid.uuid4())
        research_dir = self.research_dir / research_id
        research_dir.mkdir(parents=True, exist_ok=True)

        current_time = datetime.utcnow().isoformat()
        research = Research(
            id=research_id,
            title=title,
            description=description,
            objectives=objectives,
            methodology=methodology,
            sources=[],
            findings=[],
            created_at=current_time,
            status='planned',
            start_date=current_time,
            end_date=None,
            metadata={},
            updated_at=current_time
        )

        # Save research metadata
        metadata_file = research_dir / "metadata.json"
        self.file_manager.write_file(
            metadata_file,
            json.dumps(asdict(research), indent=2)
        )

        # Create version control
        version_file = research_dir / "version.json"
        self.file_manager.write_file(
            version_file,
            json.dumps({
                "version": "1.0.0",
                "created_at": current_time
            }, indent=2)
        )

        return research

    def add_source(self, research_id: str, title: str, url: str, source_type: str, description: str) -> ResearchSource:
        """Add a source to research project."""
        research = self._load_research(research_id)
        
        source: ResearchSource = {
            'title': title,
            'url': url,
            'type': source_type,
            'description': description,
            'added_at': datetime.utcnow().isoformat()
        }
        
        research.sources.append(source)
        self._save_research(research)
        
        return source

    def add_finding(self, research_id: str, title: str, description: str, evidence: str) -> ResearchFinding:
        """Add a finding to research project."""
        research = self._load_research(research_id)
        
        finding: ResearchFinding = {
            'title': title,
            'description': description,
            'evidence': evidence,
            'added_at': datetime.utcnow().isoformat()
        }
        
        research.findings.append(finding)
        self._save_research(research)
        
        return finding

    def _load_research(self, research_id: str) -> Research:
        """Load research from file."""
        metadata_file = self.research_dir / research_id / "metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"Research {research_id} not found")
            
        data = json.loads(self.file_manager.read_file(metadata_file))
        return Research(**data)

    def _save_research(self, research: Research) -> None:
        """Save research to file."""
        metadata_file = self.research_dir / research.id / "metadata.json"
        self.file_manager.write_file(
            metadata_file,
            json.dumps(asdict(research), indent=2)
        )

    def update_research(self, research_id: str, updates: Dict[str, Any]) -> Research:
        """
        Update an existing research project
        Args:
            research_id: Research ID
            updates: Dictionary of updates
        Returns:
            Updated Research object
        """
        research = self.get_research(research_id)
        if not research:
            raise ValueError(f"Research not found: {research_id}")
        
        # Update fields
        for key, value in updates.items():
            if hasattr(research, key):
                setattr(research, key, value)
        
        # Update timestamp
        research.updated_at = datetime.datetime.now().isoformat()
        
        # Save research
        self._save_research(research)
        
        # Create version
        self.file_manager.version_control(
            self._get_research_path(research_id),
            comment=f"Updated research: {research.title}"
        )
        
        return research
    
    def get_research(self, research_id: str) -> Optional[Research]:
        """
        Get a research project by ID
        Args:
            research_id: Research ID
        Returns:
            Research object if found, None otherwise
        """
        research_path = self._get_research_path(research_id)
        if not research_path.exists():
            return None
        
        with open(research_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Convert sources and findings
            sources = [ResearchSource(**s) for s in data.pop('sources', [])]
            findings = [ResearchFinding(**f) for f in data.pop('findings', [])]
            
            # Create research object
            return Research(
                **data,
                sources=sources,
                findings=findings
            )
    
    def list_research(self, status: Optional[str] = None) -> List[Research]:
        """
        List all research projects, optionally filtered by status
        Args:
            status: Optional status filter
        Returns:
            List of Research objects
        """
        research_list = []
        for research_file in self.research_dir.glob('*.json'):
            research = self.get_research(research_file.stem)
            if research and (not status or research.status == status):
                research_list.append(research)
        return research_list
    
    def generate_report(self, research_id: str) -> Dict[str, Any]:
        """
        Generate research report
        Args:
            research_id: Research ID
        Returns:
            Dictionary containing report data
        """
        research = self.get_research(research_id)
        if not research:
            raise ValueError(f"Research not found: {research_id}")
        
        # Prepare report data
        report_data = {
            'research_id': research.id,
            'title': research.title,
            'description': research.description,
            'status': research.status,
            'duration': {
                'start': research.start_date,
                'end': research.end_date or 'Ongoing'
            },
            'objectives': research.objectives,
            'methodology': research.methodology,
            'sources': [
                {
                    'title': s['title'],
                    'type': s['type'],
                    'url': s['url']
                }
                for s in research.sources
            ],
            'findings': [
                {
                    'title': f['title'],
                    'description': f['description'],
                    'evidence': f['evidence']
                }
                for f in research.findings
            ],
            'last_updated': research.updated_at
        }
        
        return report_data
    
    def analyze_sources(self, research_id: str) -> Dict[str, Any]:
        """
        Analyze research sources
        Args:
            research_id: Research ID
        Returns:
            Dictionary containing analysis results
        """
        research = self.get_research(research_id)
        if not research:
            raise ValueError(f"Research not found: {research_id}")
        
        # Analyze sources
        source_types = {}
        authors = set()
        earliest_date = None
        latest_date = None
        
        for source in research.sources:
            # Count source types
            source_types[source['type']] = source_types.get(source['type'], 0) + 1
            
            # Collect unique authors
            authors.update(source['authors'] or [])
            
            # Track date range
            if source['added_at']:
                date = datetime.datetime.fromisoformat(source['added_at'])
                if not earliest_date or date < earliest_date:
                    earliest_date = date
                if not latest_date or date > latest_date:
                    latest_date = date
        
        return {
            'total_sources': len(research.sources),
            'source_types': source_types,
            'unique_authors': len(authors),
            'date_range': {
                'earliest': earliest_date,
                'latest': latest_date
            }
        }
    
    def _get_research_path(self, research_id: str) -> Path:
        """Get path for research file"""
        return self.research_dir / f"{research_id}.json" 