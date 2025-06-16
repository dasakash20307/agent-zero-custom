"""
Saadhan AI Assistant - Custom Instruments for Dilasa Janvikas Pratishthan.
"""
from .orchestrator import Orchestrator, WorkspaceConfig
from .file_management import FileManager
from .template_management import TemplateManager
from .project_management import ProjectManager
from .research import ResearchManager
from .proposal import ProposalManager

__all__ = [
    'Orchestrator',
    'WorkspaceConfig',
    'FileManager',
    'TemplateManager',
    'ProjectManager',
    'ResearchManager',
    'ProposalManager'
]

__version__ = '0.1.0' 