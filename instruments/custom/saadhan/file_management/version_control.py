"""
Version Control module for managing file versions and change tracking.
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
import hashlib
import json
from dataclasses import dataclass, asdict

@dataclass
class ChangeSet:
    """Class for tracking changes between versions"""
    version_from: str
    version_to: str
    timestamp: str
    changes: List[Dict[str, str]]
    comment: Optional[str] = None

@dataclass
class FileVersion:
    """Class for tracking file versions"""
    version_id: str
    file_path: str
    timestamp: str
    hash: str
    comment: Optional[str] = None

class VersionControl:
    """Handles file versioning and version tracking."""
    
    def __init__(self, base_dir: Union[str, Path]):
        """
        Initialize version control
        Args:
            base_dir: Base directory for version control
        """
        self.base_dir = Path(base_dir)
        self.version_dir = self.base_dir / "_versions"
        self.version_db = self.version_dir / "version_db.json"
        self._ensure_directories()
        self._init_version_db()
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.version_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_version_db(self) -> None:
        """Initialize version database."""
        if not self.version_db.exists():
            with open(self.version_db, 'w') as f:
                json.dump({}, f)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def create_version(self, file_path: Union[str, Path], comment: Optional[str] = None) -> FileVersion:
        """
        Create a new version of the file
        Args:
            file_path: Path to the file
            comment: Optional comment about the version
        Returns:
            FileVersion object with version details
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        
        # Create version ID using timestamp
        timestamp = datetime.now().isoformat()
        version_id = f"v_{timestamp.replace(':', '_')}"
        
        # Create version object
        version = FileVersion(
            version_id=version_id,
            file_path=str(file_path.relative_to(self.base_dir)),
            timestamp=timestamp,
            hash=file_hash,
            comment=comment
        )
        
        # Save file version
        version_path = self.version_dir / version_id / file_path.name
        version_path.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(file_path, version_path)
        
        # Update version database
        with open(self.version_db, 'r') as f:
            version_data = json.load(f)
        
        if str(file_path) not in version_data:
            version_data[str(file_path)] = []
        
        version_data[str(file_path)].append(asdict(version))
        
        with open(self.version_db, 'w') as f:
            json.dump(version_data, f, indent=2)
        
        return version
    
    def get_versions(self, file_path: Union[str, Path]) -> List[FileVersion]:
        """
        Get list of file versions
        Args:
            file_path: Path to the file
        Returns:
            List of FileVersion objects
        """
        file_path = Path(file_path)
        
        with open(self.version_db, 'r') as f:
            version_data = json.load(f)
        
        if str(file_path) not in version_data:
            return []
        
        return [FileVersion(**v) for v in version_data[str(file_path)]]
    
    def get_version(self, version_id: str) -> Optional[FileVersion]:
        """Get specific version by ID."""
        db = self._load_version_db()
        for versions in db.values():
            for version in versions:
                if version['version_id'] == version_id:
                    return FileVersion(**version)
        return None
    
    def restore_version(self, file_path: Union[str, Path], version_id: str) -> None:
        """
        Restore file to specific version
        Args:
            file_path: Path to the file
            version_id: Version ID to restore
        """
        file_path = Path(file_path)
        
        with open(self.version_db, 'r') as f:
            version_data = json.load(f)
        
        if str(file_path) not in version_data:
            raise ValueError(f"No versions found for file: {file_path}")
        
        # Find version
        version = None
        for v in version_data[str(file_path)]:
            if v['version_id'] == version_id:
                version = v
                break
        
        if not version:
            raise ValueError(f"Version not found: {version_id}")
        
        # Restore version
        version_path = self.version_dir / version_id / Path(version['file_path']).name
        if not version_path.exists():
            raise FileNotFoundError(f"Version file not found: {version_path}")
        
        import shutil
        shutil.copy2(version_path, file_path)
    
    def compare_versions(self, version_id1: str, version_id2: str) -> Dict[str, Any]:
        """Compare two versions of a file."""
        v1 = self.get_version(version_id1)
        v2 = self.get_version(version_id2)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
            
        return {
            'version1': version_id1,
            'version2': version_id2,
            'timestamp1': v1.timestamp,
            'timestamp2': v2.timestamp,
            'hash1': v1.hash,
            'hash2': v2.hash,
            'same_content': v1.hash == v2.hash
        }
    
    def track_changes(self, file_path: str, from_version: str, to_version: str) -> ChangeSet:
        """
        Track changes between two versions
        Args:
            file_path: Path to the file
            from_version: Starting version ID
            to_version: Ending version ID
        Returns:
            ChangeSet object with change details
        """
        with open(self.version_db, 'r') as f:
            version_data = json.load(f)
        
        if file_path not in version_data:
            raise ValueError(f"No versions found for file: {file_path}")
        
        # Find versions
        versions = version_data[file_path]
        from_ver = None
        to_ver = None
        
        for ver in versions:
            if ver['version_id'] == from_version:
                from_ver = ver
            if ver['version_id'] == to_version:
                to_ver = ver
        
        if not from_ver or not to_ver:
            raise ValueError("Version not found")
        
        # Create change set
        changes = []
        if from_ver['hash'] != to_ver['hash']:
            changes.append({
                'type': 'modified',
                'from_hash': from_ver['hash'],
                'to_hash': to_ver['hash'],
                'timestamp': to_ver['timestamp']
            })
        
        return ChangeSet(
            version_from=from_version,
            version_to=to_version,
            timestamp=datetime.now().isoformat(),
            changes=changes,
            comment=to_ver.get('comment')
        )
    
    def get_version_history(self, file_path: str) -> List[FileVersion]:
        """
        Get version history for a file
        Args:
            file_path: Path to the file
        Returns:
            List of FileVersion objects
        """
        with open(self.version_db, 'r') as f:
            version_data = json.load(f)
        
        if file_path not in version_data:
            return []
        
        return [FileVersion(**v) for v in version_data[file_path]] 