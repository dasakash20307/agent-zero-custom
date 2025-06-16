# Report Generation Module

## Overview
The Report Generation module is a component of the Saadhan AI Assistant that handles the creation, formatting, and export of various types of reports. It supports multiple output formats (PDF, DOCX) and includes features for data visualization, dynamic template management, and consistent styling.

## Components
1. **Report Generator** (`report_generator.py`): Main class for report generation and export
2. **Formatter** (`formatter.py`): Handles report formatting and styling
3. **Template** (`template.py`): Manages report templates and sections
4. **Template Scanner** (`template_scanner.py`): Analyzes and extracts templates from existing documents
5. **Requirements** (`requirements.txt`): Lists required dependencies

## Setup
1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Dynamic Template Features
1. **Template Scanning**
   - Analyze existing documents (DOCX, PDF, TXT, MD)
   - Extract structure, sections, and placeholders
   - Identify formatting patterns and styles

2. **Template Storage**
   - Store extracted templates by category
   - Maintain template metadata and structure
   - Support version tracking

3. **Template Matching**
   - Find similar templates for new documents
   - Calculate template similarity scores
   - Suggest best matching templates

4. **Template Creation**
   - Create new templates from reference documents
   - Extract placeholders automatically
   - Preserve formatting patterns

## Usage Example
```python
from instruments.custom.saadhan.report.report_generator import ReportGenerator
import pandas as pd

# Initialize report generator
report_gen = ReportGenerator(workspace_root="/path/to/workspace")

# Option 1: Create report from existing template
report_data = {
    "title": "Monthly Progress Report",
    "project_name": "Project X",
    "status": "In Progress",
    "completed_tasks": "Task 1, Task 2",
    "pending_tasks": "Task 3, Task 4"
}

report = report_gen.create_report(
    template_type="progress_report",
    project_id="PRJ001",
    data=report_data
)

# Option 2: Create report from reference document
reference_doc = "path/to/reference/report.docx"
report = report_gen.create_report(
    template_type="progress_report",
    project_id="PRJ001",
    data=report_data,
    reference_doc=reference_doc  # This will scan and use the reference document's structure
)

# Add visualization
metrics_data = pd.DataFrame({
    'Month': ['Jan', 'Feb', 'Mar'],
    'Tasks Completed': [5, 8, 12]
})

report.add_visualization(
    data=metrics_data,
    viz_type="line_chart",
    title="Task Completion Trend"
)

# Export report
pdf_path = report_gen.export_report(report, format="pdf", output_path="reports/progress_report")
docx_path = report_gen.export_report(report, format="docx", output_path="reports/progress_report")
```

## Template Scanning Example
```python
from instruments.custom.saadhan.report.report_generator import ReportGenerator

# Initialize report generator
report_gen = ReportGenerator(workspace_root="/path/to/workspace")

# Scan and store a template
template = report_gen.scan_and_store_template(
    file_path="path/to/example/report.docx",
    template_name="example_report",
    category="project_reports"
)

# Find similar templates
similar_templates = report_gen.find_similar_templates(
    file_path="path/to/new/report.docx",
    category="project_reports"
)

# Create report using scanned template
report = report_gen.create_report(
    template_type=template.name,
    project_id="PRJ001",
    data=report_data
)
```

## Features
1. **Template-based Generation**
   - Use predefined templates
   - Support for dynamic content
   - Required field validation
   - Template scanning and extraction
   - Similar template matching

2. **Rich Formatting**
   - Consistent styling
   - Multiple text styles
   - Custom fonts and sizes
   - Format pattern preservation

3. **Data Visualization**
   - Line charts
   - Bar charts
   - Scatter plots
   - Pie charts

4. **Multiple Export Formats**
   - PDF with proper pagination
   - DOCX with formatting
   - Configurable output paths

5. **Error Handling**
   - Template validation
   - Required field checking
   - Format compatibility checks
   - Import dependency checks

## Directory Structure
```
report/
├── __init__.py
├── report_generator.py  # Main report generation logic
├── formatter.py        # Formatting and styling utilities
├── template.py        # Template management
├── template_scanner.py # Template analysis and extraction
├── requirements.txt   # Package dependencies
└── README.md         # This documentation
```

## Dependencies
- pandas: Data manipulation and analysis
- matplotlib: Data visualization
- python-docx: DOCX file generation and analysis
- PyPDF2: PDF file analysis
- reportlab: PDF generation

## Notes
1. Ensure all dependencies are installed before using the module
2. The module requires write access to create temporary files for visualizations
3. Templates are stored in the knowledge base under custom/dilasa/templates
4. The template scanner supports DOCX, PDF, TXT, and MD formats
5. Template similarity matching uses a weighted scoring system
6. Output directories must be writable for report export 