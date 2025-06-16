"""
Template Scanner module for analyzing and extracting templates from documents.
"""
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import re
import uuid
import datetime
from dataclasses import dataclass
from .template_manager import Template, TemplateVariable

@dataclass
class DocumentStructure:
    """Class representing document structure"""
    sections: List[Dict[str, Any]]
    variables: List[str]
    format_patterns: Dict[str, List[str]]
    metadata: Dict[str, Any]

class TemplateScanner:
    """Analyzes documents to extract template patterns"""
    
    def __init__(self):
        self.patterns = {
            'section_headers': r'^#{1,6}\s+[^#\n]+$',  # Matches markdown headers #, ##, etc.
            'variables': r'\{([^}]+)\}',
            'table_headers': r'^[A-Z][a-zA-Z\s]*$',
            'list_items': r'^\s*[-•*]\s',
            'numbered_items': r'^\s*\d+\.',
            'metadata_tags': r'@\w+\s*:\s*([^\n]+)'
        }
    
    def scan_document(self, file_path: Union[str, Path]) -> DocumentStructure:
        """
        Scan a document and extract its structure
        Args:
            file_path: Path to document
        Returns:
            DocumentStructure object
        """
        file_path = Path(file_path)
        content = self._read_file(file_path)
        
        # Extract document components
        sections = self._extract_sections(content)
        variables = self._extract_variables(content)
        format_patterns = self._extract_format_patterns(content)
        metadata = self._extract_metadata(content)
        
        return DocumentStructure(
            sections=sections,
            variables=variables,
            format_patterns=format_patterns,
            metadata=metadata
        )
    
    def create_template(self, doc_structure: DocumentStructure, 
                       name: str, category: str) -> Template:
        """
        Create template from document structure
        Args:
            doc_structure: DocumentStructure object
            name: Template name
            category: Template category
        Returns:
            Template object
        """
        # Convert sections to template content
        content = self._structure_to_content(doc_structure)
        
        # Create template variables
        variables = [
            TemplateVariable(
                name=var,
                description=f"Variable for {var}",
                type="string",
                required=True
            )
            for var in doc_structure.variables
        ]
        
        # Create metadata
        metadata = {
            **doc_structure.metadata,
            'format_patterns': doc_structure.format_patterns,
            'source_file': str(doc_structure.metadata.get('source_file', ''))
        }
        
        # Generate unique ID
        template_id = str(uuid.uuid4())
        
        # Get current timestamp
        timestamp = datetime.datetime.now().isoformat()
        
        return Template(
            id=template_id,
            name=name,
            type='document',
            category=category,
            author='system',
            description=f"Template extracted from document: {name}",
            content=content,
            variables=[v.name for v in variables],
            metadata=metadata,
            version='1.0.0',
            created_at=timestamp,
            updated_at=timestamp
        )
    
    def _read_file(self, file_path: Path) -> str:
        """Read file content"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_sections(self, content: str) -> List[Dict[str, Any]]:
        """Extract sections from content"""
        sections = []
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.rstrip()
            # Only match h2 headers (##)
            if re.match(r'^##\s+[^#\n]+$', line):
                if current_section:
                    current_section['content'] = '\n'.join(current_section['content']).strip()
                    sections.append(current_section)
                current_section = {
                    'title': line.lstrip('#').strip(),
                    'content': []
                }
            elif current_section is not None:  # Only append if we have a current section
                current_section['content'].append(line)
        
        if current_section:
            current_section['content'] = '\n'.join(current_section['content']).strip()
            sections.append(current_section)
        
        return sections
    
    def _extract_variables(self, content: str) -> List[str]:
        """Extract variables from content"""
        matches = re.findall(self.patterns['variables'], content)
        return list(set(matches))
    
    def _extract_format_patterns(self, content: str) -> Dict[str, List[str]]:
        """Extract formatting patterns"""
        patterns = {
            'lists': [],
            'tables': [],
            'styles': []
        }
        
        lines = content.split('\n')
        for line in lines:
            if re.match(self.patterns['list_items'], line):
                patterns['lists'].append('bullet')
            elif re.match(self.patterns['numbered_items'], line):
                patterns['lists'].append('numbered')
            elif re.match(self.patterns['table_headers'], line):
                patterns['tables'].append(line.strip())
        
        return patterns
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from content"""
        metadata = {}
        matches = re.findall(self.patterns['metadata_tags'], content)
        
        for match in matches:
            key, value = match.split(':', 1)
            metadata[key.strip('@').lower()] = value.strip()
        
        return metadata
    
    def _structure_to_content(self, doc_structure: DocumentStructure) -> str:
        """Convert document structure to template content"""
        content_parts = []
        
        for section in doc_structure.sections:
            content_parts.append(section['title'])
            content_parts.extend(section['content'])
        
        return '\n'.join(content_parts)
    
    def analyze_similarity(self, template1: Template, template2: Template) -> float:
        """
        Analyze similarity between two templates
        Args:
            template1: First template
            template2: Second template
        Returns:
            Similarity score (0-1)
        """
        # Compare variables
        var_similarity = len(
            set(template1.variables) & set(template2.variables)
        ) / max(len(template1.variables), len(template2.variables))
        
        # Compare structure
        struct_similarity = self._compare_structure(
            template1.content,
            template2.content
        )
        
        # Compare metadata
        meta_similarity = self._compare_metadata(
            template1.metadata,
            template2.metadata
        )
        
        # Weighted average
        return (
            var_similarity * 0.4 +
            struct_similarity * 0.4 +
            meta_similarity * 0.2
        )
    
    def _compare_structure(self, content1: str, content2: str) -> float:
        """Compare structural similarity of content"""
        sections1 = len(re.findall(self.patterns['section_headers'], content1))
        sections2 = len(re.findall(self.patterns['section_headers'], content2))
        
        if sections1 == 0 and sections2 == 0:
            return 1.0
        
        return min(sections1, sections2) / max(sections1, sections2)
    
    def _compare_metadata(self, meta1: Dict[str, Any], 
                         meta2: Dict[str, Any]) -> float:
        """Compare metadata similarity"""
        keys1 = set(meta1.keys())
        keys2 = set(meta2.keys())
        
        if not keys1 and not keys2:
            return 1.0
        
        return len(keys1 & keys2) / max(len(keys1), len(keys2)) 