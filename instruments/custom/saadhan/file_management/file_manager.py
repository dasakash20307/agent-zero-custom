"""
File Manager for File Management Instrument
Handles file operations, backups, and version control
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Union, Optional

class FileManager:
    """Manages file operations and version control."""
    
    def __init__(self, base_dir: Union[str, Path]):
        """
        Initialize file manager
        Args:
            base_dir: Base directory for file operations
        """
        self.base_dir = Path(base_dir)
        self.backup_dir = self.base_dir / "backups"
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def read_file(self, file_path: Union[str, Path]) -> str:
        """
        Read file content
        Args:
            file_path: Path to the file
        Returns:
            str: File content as string
        Raises:
            FileNotFoundError: If file does not exist
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.read_text()

    def write_file(self, file_path: Union[str, Path], content: str) -> None:
        """
        Write content to file
        Args:
            file_path: Path to the file
            content: Content to write
        Returns:
            None
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

    def copy_file(self, source: Union[str, Path], target: Union[str, Path]):
        """
        Copy file from source to target
        Args:
            source: Source file path
            target: Target file path
        """
        source = Path(source)
        target = Path(target)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    def move_file(self, source: Union[str, Path], target: Union[str, Path]):
        """
        Move file from source to target
        Args:
            source: Source file path
            target: Target file path
        """
        source = Path(source)
        target = Path(target)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, target)

    def delete_file(self, file_path: Union[str, Path]):
        """
        Delete file
        Args:
            file_path: Path to the file
        """
        file_path = Path(file_path)
        if file_path.exists():
            file_path.unlink()

    def create_backup(self, file_path: Union[str, Path]) -> Path:
        """
        Create backup of a file
        Args:
            file_path: Path to the file
        Returns:
            Path to backup file
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        # Create backup
        self.copy_file(file_path, backup_path)
        return backup_path

    def list_files(self, directory: Union[str, Path]) -> List[Path]:
        """
        List files in directory
        Args:
            directory: Directory to list
        Returns:
            List[Path]: List of file paths
        Raises:
            NotADirectoryError: If directory does not exist
        """
        directory = Path(directory)
        if not directory.exists():
            raise NotADirectoryError(f"Directory not found: {directory}")
        return list(directory.glob("*"))

    def search_files(self, directory: Union[str, Path], pattern: str) -> List[Path]:
        """
        Search files matching pattern in directory
        Args:
            directory: Directory to search in
            pattern: Search pattern (e.g. "*.txt")
        Returns:
            List[Path]: List of matching file paths
        Raises:
            NotADirectoryError: If directory does not exist
        """
        directory = Path(directory)
        if not directory.exists():
            raise NotADirectoryError(f"Directory not found: {directory}")
        return list(directory.glob(pattern)) 