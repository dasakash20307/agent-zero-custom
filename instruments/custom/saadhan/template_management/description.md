# Template Management Instrument

## Purpose
The Template Management Instrument is responsible for handling all template-related operations in the Saadhan AI Assistant. It provides functionality for creating, managing, and analyzing templates used across various aspects of the system, including reports, proposals, and research documents.

## Core Functionalities

### 1. Template Management
- Create and store templates
- Update existing templates
- Version control for templates
- Template categorization
- Template metadata management

### 2. Template Analysis
- Extract template structure from documents
- Identify variables and placeholders
- Analyze formatting patterns
- Compare template similarities
- Template validation

### 3. Template Scanning
- Scan existing documents for patterns
- Extract reusable components
- Identify common structures
- Learn from document examples

## Components

### 1. TemplateManager (`template_manager.py`)
Main class for template operations:
- `create_template()`: Create new templates
- `update_template()`: Update existing templates
- `get_template()`: Retrieve templates
- `list_templates()`: List available templates
- `delete_template()`: Remove templates
- `validate_template_data()`: Validate data against template
- `render_template()`: Render template with data

### 2. TemplateScanner (`template_scanner.py`)
Specialized class for template analysis:
- `scan_document()`: Analyze document structure
- `create_template()`: Create template from document
- `analyze_similarity()`: Compare templates
- `extract_sections()`: Extract document sections
- `extract_variables()`: Identify variables
- `extract_format_patterns()`: Analyze formatting

## Usage Example
```python
from instruments.custom.saadhan.template_management import TemplateManager, TemplateScanner

# Initialize managers
template_manager = TemplateManager(workspace_root="/path/to/workspace")
template_scanner = TemplateScanner()

# Create template from document
doc_structure = template_scanner.scan_document("path/to/document.md")
template = template_scanner.create_template(
    doc_structure,
    name="project_report",
    category="reports"
)

# Save template
template_manager.create_template(
    name=template.name,
    category=template.category,
    content=template.content,
    variables=template.variables,
    metadata=template.metadata
)

# Render template
data = {
    "project_name": "Project X",
    "status": "In Progress",
    "completion": "75%"
}
rendered = template_manager.render_template(template, data)
```

## Directory Structure
```
template_management/
├── __init__.py
├── template_manager.py
├── template_scanner.py
├── description.md
└── requirements.txt
```

## Integration Points
- File Management Instrument: For template storage
- Report Generation Instrument: For report templates
- Project Management Instrument: For project templates
- Research Instrument: For research document templates

## Dependencies
- pathlib: Path handling
- typing: Type annotations
- json: Data serialization
- datetime: Timestamp management
- uuid: Unique ID generation
- re: Regular expressions

## Notes
1. Templates are stored in JSON format
2. Version control is maintained for all templates
3. Templates can be created from example documents
4. Template variables are validated before rendering
5. Template similarity analysis helps in reuse 