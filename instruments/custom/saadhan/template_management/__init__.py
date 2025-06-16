"""
Template Management Instrument for Saadhan AI Assistant.
"""
from .template_manager import (
    TemplateManager,
    Template,
    TemplateVariable
)
from .template_scanner import (
    TemplateScanner,
    DocumentStructure
)

__all__ = [
    'TemplateManager',
    'Template',
    'TemplateVariable',
    'TemplateScanner',
    'DocumentStructure'
]

__version__ = '0.1.0' 