"""
File Management Instrument for Saadhan AI Assistant.
Provides file versioning, backup, and categorization capabilities.
"""

from .file_manager import FileManager
from .version_control import VersionControl, FileVersion

__all__ = ['FileManager', 'VersionControl', 'FileVersion']

__version__ = '0.1.0' 