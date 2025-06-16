# Research Instrument

## Purpose
The Research Instrument is responsible for managing research projects, sources, findings, and analysis within the Saadhan AI Assistant. It provides functionality for conducting structured research, tracking sources, documenting findings, and generating comprehensive reports.

## Core Functionalities

### 1. Research Project Management
- Create and manage research projects
- Track research status and progress
- Define research objectives
- Document methodology
- Manage research timeline

### 2. Source Management
- Track research sources
- Manage source metadata
- Source categorization
- Author tracking
- Publication date tracking

### 3. Finding Management
- Document research findings
- Link findings to sources
- Track evidence and impact
- Confidence assessment
- Finding categorization

### 4. Analysis
- Source analysis
- Finding synthesis
- Impact assessment
- Research progress tracking
- Report generation

## Components

### 1. ResearchManager (`research_manager.py`)
Main class for research operations:
- `create_research()`: Create new research projects
- `update_research()`: Update existing research
- `get_research()`: Retrieve research projects
- `list_research()`: List available research
- `add_source()`: Add research sources
- `add_finding()`: Add research findings
- `generate_report()`: Generate research reports
- `analyze_sources()`: Analyze research sources

### 2. Data Classes
Structured data representation:
- `Research`: Core research project information
- `ResearchSource`: Source tracking
- `ResearchFinding`: Finding documentation

## Usage Example
```python
from instruments.custom.saadhan.research import ResearchManager

# Initialize manager
research_manager = ResearchManager(workspace_root="/path/to/workspace")

# Create research project
research = research_manager.create_research(
    title="Impact Assessment Study",
    description="Study of community development impact",
    objectives=["Assess impact", "Identify improvements"],
    methodology="Mixed methods approach"
)

# Add source
source = research_manager.add_source(
    research_id=research.id,
    title="Community Survey Results",
    source_type="primary_data",
    content="Survey results...",
    authors=["Research Team"]
)

# Add finding
finding = research_manager.add_finding(
    research_id=research.id,
    title="Increased Community Engagement",
    description="Significant increase in participation",
    evidence="Survey shows 50% increase",
    impact="Positive community development",
    confidence=0.85
)

# Generate report
report = research_manager.generate_report(research.id)

# Analyze sources
analysis = research_manager.analyze_sources(research.id)
```

## Directory Structure
```
research/
├── __init__.py
├── research_manager.py
├── description.md
└── requirements.txt
```

## Integration Points
- File Management Instrument: For research file storage
- Template Management Instrument: For report templates
- Project Management Instrument: For project coordination
- Report Generation Instrument: For research reports

## Dependencies
- pathlib: Path handling
- typing: Type annotations
- json: Data serialization
- datetime: Timestamp management
- uuid: Unique ID generation
- dataclasses: Data structure management

## Notes
1. Research data is stored in JSON format
2. Version control is maintained for all research
3. Sources are tracked with metadata
4. Findings include confidence levels
5. Reports can be customized with templates 