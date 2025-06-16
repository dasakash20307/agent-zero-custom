"""
Report Generator module for creating, formatting and exporting reports.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Type, cast
from typing_extensions import Protocol
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
from datetime import datetime
import json

from instruments.custom.saadhan.template_management.template_manager import TemplateManager
from instruments.custom.saadhan.file_management.file_manager import FileManager
from instruments.custom.saadhan.report.formatter import ReportFormatter
from instruments.custom.saadhan.report.template import Template, TemplateSection
from instruments.custom.saadhan.report.template_scanner import TemplateScanner, DocumentStructure

# Define protocol for document handling
class DocxDocument(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> 'DocxDocument': ...
    def add_heading(self, text: str, level: int) -> Any: ...
    def add_paragraph(self, text: str) -> Any: ...
    def add_picture(self, path: str) -> Any: ...
    def save(self, path: str) -> None: ...

# Type alias
DocumentType = Type[DocxDocument]

@dataclass
class ReportSection:
    """Represents a section in a report"""
    title: str
    content: str
    data: Optional[Dict[str, Any]] = None
    charts: Optional[List[str]] = None

@dataclass
class Report:
    """Represents a complete report"""
    title: str
    sections: List[ReportSection]
    metadata: Dict[str, Any]
    template_id: Optional[str] = None
    created_at: str = datetime.now().isoformat()

class ReportGenerator:
    """Main class for generating reports"""
    
    def __init__(self, base_dir: Union[str, Path], template_manager: Optional[TemplateManager] = None):
        """Initialize the report generator."""
        self.base_dir = Path(base_dir)
        self.reports_dir = self.base_dir / "reports"
        self.charts_dir = self.reports_dir / "charts"
        self.template_manager = template_manager
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        for directory in [self.reports_dir, self.charts_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def create_section(self, title: str, content: str, data: Optional[Dict[str, Any]] = None) -> ReportSection:
        """Create a report section."""
        charts = []
        if data:
            charts = self._generate_charts(data, title)
        
        return ReportSection(
            title=title,
            content=content,
            data=data,
            charts=charts
        )

    def _generate_charts(self, data: Dict[str, Any], section_title: str) -> List[str]:
        """Generate charts from data."""
        charts = []
        
        # Convert data to DataFrame if it's not already
        if not isinstance(data, pd.DataFrame):
            df = pd.DataFrame(data)
        else:
            df = data

        # Generate appropriate charts based on data types
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        if numeric_cols:
            # Bar chart for numeric columns
            plt.figure(figsize=(10, 6))
            for col in numeric_cols:
                plt.bar(df.index, df[col], label=col)
            plt.title(f"{section_title} - Numeric Data")
            plt.legend()
            plt.tight_layout()
            
            chart_path = self.charts_dir / f"{section_title.lower().replace(' ', '_')}_bar.png"
            plt.savefig(chart_path)
            plt.close()
            charts.append(str(chart_path))

            # Line chart if there's a time-based index
            if isinstance(df.index, pd.DatetimeIndex):
                plt.figure(figsize=(10, 6))
                for col in numeric_cols:
                    plt.plot(df.index, df[col], label=col)
                plt.title(f"{section_title} - Time Series")
                plt.legend()
                plt.tight_layout()
                
                chart_path = self.charts_dir / f"{section_title.lower().replace(' ', '_')}_line.png"
                plt.savefig(chart_path)
                plt.close()
                charts.append(str(chart_path))

        return charts

    def create_report(self, title: str, sections: List[ReportSection], 
                     metadata: Optional[Dict[str, Any]] = None,
                     template_id: Optional[str] = None) -> Report:
        """Create a complete report."""
        if metadata is None:
            metadata = {}
        
        metadata.update({
            'generated_at': datetime.now().isoformat(),
            'generator': 'Saadhan AI Assistant'
        })

        return Report(
            title=title,
            sections=sections,
            metadata=metadata,
            template_id=template_id
        )

    def format_report(self, report: Report, output_format: str = 'markdown') -> str:
        """Format the report in the specified format."""
        if report.template_id and self.template_manager:
            # Use template if available
            template_content = self.template_manager.get_template(report.template_id)
            if template_content and isinstance(template_content, str):
                return self._apply_template(report, template_content)

        # Default formatting if no template or template manager
        if output_format.lower() == 'markdown':
            return self._format_markdown(report)
        elif output_format.lower() == 'html':
            return self._format_html(report)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _format_markdown(self, report: Report) -> str:
        """Format report as markdown."""
        lines = [
            f"# {report.title}",
            "",
            "## Metadata",
            "```json",
            json.dumps(report.metadata, indent=2),
            "```",
            ""
        ]

        for section in report.sections:
            lines.extend([
                f"## {section.title}",
                "",
                section.content,
                ""
            ])

            if section.charts:
                lines.extend([
                    "### Charts",
                    "",
                    *[f"![{section.title} Chart]({chart})" for chart in section.charts],
                    ""
                ])

        return "\n".join(lines)

    def _format_html(self, report: Report) -> str:
        """Format report as HTML."""
        lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{report.title}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "img { max-width: 100%; height: auto; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{report.title}</h1>",
            "",
            "<h2>Metadata</h2>",
            "<pre>",
            json.dumps(report.metadata, indent=2),
            "</pre>"
        ]

        for section in report.sections:
            lines.extend([
                f"<h2>{section.title}</h2>",
                f"<div>{section.content}</div>"
            ])

            if section.charts:
                lines.extend([
                    "<h3>Charts</h3>",
                    *[f'<img src="{chart}" alt="{section.title} Chart">' for chart in section.charts]
                ])

        lines.extend([
            "</body>",
            "</html>"
        ])

        return "\n".join(lines)

    def _apply_template(self, report: Report, template: str) -> str:
        """Apply a template to the report."""
        # Basic template variable replacement
        content = template
        
        # Replace metadata variables
        for key, value in report.metadata.items():
            content = content.replace(f"{{metadata.{key}}}", str(value))
        
        # Replace title
        content = content.replace("{title}", report.title)
        
        # Replace sections
        for i, section in enumerate(report.sections):
            content = content.replace(f"{{section{i+1}.title}}", section.title)
            content = content.replace(f"{{section{i+1}.content}}", section.content)
            
            if section.charts:
                charts_md = "\n".join([f"![{section.title} Chart]({chart})" for chart in section.charts])
                content = content.replace(f"{{section{i+1}.charts}}", charts_md)
        
        return content

    def save_report(self, report: Report, output_path: Union[str, Path], output_format: str = 'markdown') -> Path:
        """Save the report to a file."""
        output_path = Path(output_path)
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Format and save report
        content = self.format_report(report, output_format)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path

    def scan_and_store_template(self, file_path: Union[str, Path], template_name: str, category: str) -> Template:
        """Scan a document and store it as a template"""
        doc_structure = self.template_scanner.scan_document(file_path)
        return self.template_scanner.create_template(doc_structure, template_name, category)
    
    def find_similar_templates(self, file_path: Union[str, Path], category: str = None) -> List[Template]:
        """Find templates similar to the given document"""
        doc_structure = self.template_scanner.scan_document(file_path)
        return self.template_scanner.get_similar_templates(doc_structure, category)
    
    def _populate_content(self, template: str, data: Dict[str, Any]) -> str:
        """Populate template with data"""
        content = template
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in content:
                content = content.replace(placeholder, str(value))
        return content
    
    def export_report(self, report: Report, format: str, output_path: str) -> str:
        """Export report to specified format"""
        if format == "docx":
            return self._export_docx(report, output_path)
        elif format == "pdf":
            return self._export_pdf(report, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_docx(self, report: Report, output_path: str) -> str:
        """Export report to DOCX format"""
        if self.Document is None:
            raise ImportError("python-docx package is required for DOCX export")
            
        try:
            doc = self.Document()
        except Exception as e:
            raise ImportError(f"Failed to create DOCX document: {str(e)}")
            
        # Add title with formatting
        title_format = self.formatter.format_text(report.title, 'title')
        doc.add_heading(title_format['text'], 0)
        
        # Add sections
        for section in report.sections:
            # Add section title with formatting
            section_title_format = self.formatter.format_text(section.title, 'section_title')
            doc.add_heading(section_title_format['text'], 1)
            
            # Add content with formatting
            content_format = self.formatter.format_text(section.content, 'body_text')
            doc.add_paragraph(content_format['text'])
            
            # Add visualizations
            for viz in section.visualizations:
                doc.add_picture(viz["path"])
                doc.add_paragraph(viz["title"])
        
        # Save document
        full_path = f"{output_path}.docx"
        doc.save(full_path)
        return full_path
    
    def _export_pdf(self, report: Report, output_path: str) -> str:
        """Export report to PDF format"""
        full_path = f"{output_path}.pdf"
        c = canvas.Canvas(full_path, pagesize=letter)
        page_width, page_height = letter
        
        # Add title with formatting
        title_format = self.formatter.format_text(report.title, 'title')
        c.setFont(title_format['font'], title_format['size'])
        c.drawString(72, 800, title_format['text'])
        
        # Add sections
        y_position = 750
        for section in report.sections:
            # Add section title with formatting
            section_title_format = self.formatter.format_text(section.title, 'section_title')
            c.setFont(section_title_format['font'], section_title_format['size'])
            c.drawString(72, y_position, section_title_format['text'])
            y_position -= section_title_format['margin_bottom']
            
            # Add content with formatting
            content_format = self.formatter.format_text(section.content, 'body_text')
            c.setFont(content_format['font'], content_format['size'])
            
            # Split content into lines to handle text wrapping
            lines = self.formatter.wrap_text(content_format['text'], page_width - 144)
            for line in lines:
                c.drawString(72, y_position, line)
                y_position -= 15
            
            # Add visualizations
            for viz in section.visualizations:
                c.drawImage(viz["path"], 72, y_position - 200, width=400, height=200)
                y_position -= 220
                c.drawString(72, y_position, viz["title"])
                y_position -= 20
            
            y_position -= 20
            
            # Check if new page needed
            if y_position < 72:
                c.showPage()
                y_position = 750
        
        c.save()
        return full_path 