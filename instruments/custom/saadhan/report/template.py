"""
Template module for handling report templates.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class TemplateSection:
    """Represents a section in a report template"""
    title: str
    content_template: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    required_fields: List[str] = field(default_factory=list)

@dataclass
class Template:
    """Represents a report template"""
    name: str
    description: str
    sections: List[TemplateSection]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate if data contains all required fields"""
        for section in self.sections:
            for field in section.required_fields:
                if field not in data:
                    return False
        return True
    
    def get_section(self, title: str) -> Optional[TemplateSection]:
        """Get a section by its title"""
        for section in self.sections:
            if section.title == title:
                return section
        return None
    
    def add_section(self, section: TemplateSection) -> None:
        """Add a new section to the template"""
        self.sections.append(section)
    
    def remove_section(self, title: str) -> bool:
        """Remove a section by its title"""
        for i, section in enumerate(self.sections):
            if section.title == title:
                self.sections.pop(i)
                return True
        return False
    
    def update_section(self, title: str, new_section: TemplateSection) -> bool:
        """Update a section by its title"""
        for i, section in enumerate(self.sections):
            if section.title == title:
                self.sections[i] = new_section
                return True
        return False

class TemplateBuilder:
    """Builder class for creating report templates"""
    
    def __init__(self):
        self.name = ""
        self.description = ""
        self.sections: List[TemplateSection] = []
        self.metadata: Dict[str, Any] = {}
    
    def set_name(self, name: str) -> 'TemplateBuilder':
        """Set template name"""
        self.name = name
        return self
    
    def set_description(self, description: str) -> 'TemplateBuilder':
        """Set template description"""
        self.description = description
        return self
    
    def add_section(
        self, 
        title: str, 
        content_template: str, 
        metadata: Dict[str, Any] = field(default_factory=dict),
        required_fields: List[str] = field(default_factory=list)
    ) -> 'TemplateBuilder':
        """Add a section to the template"""
        section = TemplateSection(
            title=title,
            content_template=content_template,
            metadata=metadata,
            required_fields=required_fields
        )
        self.sections.append(section)
        return self
    
    def set_metadata(self, metadata: Dict[str, Any]) -> 'TemplateBuilder':
        """Set template metadata"""
        self.metadata = metadata
        return self
    
    def build(self) -> Template:
        """Build and return the template"""
        if not self.name:
            raise ValueError("Template name is required")
        if not self.description:
            raise ValueError("Template description is required")
        if not self.sections:
            raise ValueError("Template must have at least one section")
        
        return Template(
            name=self.name,
            description=self.description,
            sections=self.sections,
            metadata=self.metadata
        ) 