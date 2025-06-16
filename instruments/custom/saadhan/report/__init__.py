"""
Report Generation Instrument for Saadhan AI Assistant.
Provides report creation, formatting, and data visualization capabilities.
"""

from .report_generator import ReportGenerator, Report, ReportSection
from .formatter import ReportFormatter
from .template import Template, TemplateSection, TemplateBuilder

__all__ = [
    'ReportGenerator',
    'Report',
    'ReportSection',
    'ReportFormatter',
    'Template',
    'TemplateSection',
    'TemplateBuilder'
]

__version__ = '0.1.0' 