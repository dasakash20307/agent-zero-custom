# Report Generation Instrument

## Overview
The Report Generation Instrument provides comprehensive report creation and formatting capabilities for the Saadhan AI Assistant. It supports dynamic report generation with data visualization, template-based formatting, and multiple output formats.

## Components

### 1. ReportSection
A dataclass representing a section within a report.

#### Properties:
- `title`: Section title
- `content`: Main content text
- `data`: Optional data for visualization
- `charts`: Optional list of generated chart paths

### 2. Report
A dataclass representing a complete report.

#### Properties:
- `title`: Report title
- `sections`: List of ReportSection objects
- `metadata`: Report metadata
- `template_id`: Optional template identifier
- `created_at`: Report creation timestamp

### 3. ReportGenerator
The main class that handles report generation and formatting.

#### Key Features:
- Section creation with data visualization
- Multiple output formats (Markdown, HTML)
- Template-based formatting
- Chart generation from data
- File management

#### Main Methods:
- `create_section(title, content, data)`: Creates a report section
- `create_report(title, sections, metadata, template_id)`: Creates a complete report
- `format_report(report, output_format)`: Formats report in specified format
- `save_report(report, output_path, output_format)`: Saves report to file

## Usage Examples

### Basic Report Creation
```python
# Initialize report generator
report_gen = ReportGenerator(base_dir="/path/to/workspace")

# Create a section with data visualization
data = {
    'values': [10, 20, 30, 40],
    'labels': ['Q1', 'Q2', 'Q3', 'Q4']
}

section = report_gen.create_section(
    title="Quarterly Results",
    content="Analysis of quarterly performance...",
    data=data
)

# Create complete report
report = report_gen.create_report(
    title="Annual Report 2024",
    sections=[section],
    metadata={'author': 'Saadhan AI'}
)

# Save as markdown
report_gen.save_report(
    report=report,
    output_path="reports/annual_report_2024.md",
    output_format="markdown"
)
```

### Template-Based Report
```python
# Create report with template
report = report_gen.create_report(
    title="Project Progress Report",
    sections=[section1, section2],
    template_id="progress_report_template"
)

# Save as HTML
report_gen.save_report(
    report=report,
    output_path="reports/progress_report.html",
    output_format="html"
)
```

## Directory Structure
```
report/
├── __init__.py
├── report_generator.py
└── description.md
```

## Integration with Other Instruments
The Report Generation Instrument integrates with:

- **Template Management**: For report templates
- **File Management**: For file operations
- **Project Management**: For project data
- **Research**: For research findings

## Data Visualization
The instrument supports automatic chart generation:

1. Bar Charts:
   - For numeric data comparison
   - Automatically generated for numeric columns

2. Line Charts:
   - For time series data
   - Generated when time-based index is detected

## Output Formats
Supported formats include:

1. Markdown:
   - Clean, readable format
   - Embedded charts
   - Structured sections

2. HTML:
   - Styled presentation
   - Responsive design
   - Interactive elements

## Best Practices
1. Organize data properly for visualization
2. Use meaningful section titles
3. Provide comprehensive metadata
4. Use templates for consistency
5. Include relevant charts and visualizations

## Dependencies
- Python 3.7+
- pandas
- matplotlib
- pathlib
- typing
- dataclasses
- Template Management Instrument 