"""
Template Management Instrument for Saadhan AI Assistant
Handles template creation, customization, and versioning
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path

def empty_string_factory() -> str:
    return ""

@dataclass
class TemplateVariable:
    """
    Class representing a template variable
    
    Attributes:
        name: Name of the variable
        description: Description of what the variable represents
        type: Type of the variable ('string', 'number', 'date', 'boolean')
        required: Whether the variable is required
        default: Default value for the variable, defaults to empty string
    """
    name: str
    description: str
    type: str  # Can be 'string', 'number', 'date', 'boolean', etc.
    required: bool
    default: str = field(default_factory=empty_string_factory)

@dataclass
class Template:
    """Class representing a template"""
    id: str
    name: str
    type: str
    category: str
    author: str
    description: str
    content: str
    variables: List[str]
    metadata: Dict[str, Any]
    version: str
    created_at: str
    updated_at: str

class TemplateManager:
    def __init__(self, workspace_root: str):
        """
        Initialize template manager
        Args:
            workspace_root: Path to workspace root directory
        """
        self.workspace_root = workspace_root
        self.templates_dir = os.path.join(workspace_root, 'templates')
        self.versions_dir = os.path.join(workspace_root, 'template_versions')
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.versions_dir, exist_ok=True)

    def create_template(self, template_data: Dict) -> Template:
        """
        Create a new template
        Args:
            template_data: Dictionary containing template information
        Returns:
            Template object
        """
        try:
            # Generate template ID
            template_id = f"TPL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create template object
            template = Template(
                id=template_id,
                name=template_data['name'],
                type=template_data['type'],
                category=template_data.get('category', ''),
                author=template_data.get('author', 'system'),
                description=template_data.get('description', ''),
                content=template_data['content'],
                variables=template_data.get('variables', []),
                metadata=template_data.get('metadata', {}),
                version='1.0',
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )

            # Save template
            self._save_template(template)
            return template

        except Exception as e:
            raise Exception(f"Failed to create template: {str(e)}")

    def get_template(self, template_id: str) -> Optional[Template]:
        """
        Retrieve template by ID
        Args:
            template_id: Template identifier
        Returns:
            Template object if found, None otherwise
        """
        template_file = os.path.join(self.templates_dir, f"{template_id}.json")
        if not os.path.exists(template_file):
            return None

        try:
            with open(template_file, 'r') as f:
                data = json.load(f)
                return Template(**data)
        except Exception as e:
            raise Exception(f"Failed to load template: {str(e)}")

    def update_template(self, template_id: str, updates: Dict) -> Template:
        """
        Update template information
        Args:
            template_id: Template identifier
            updates: Dictionary containing updates
        Returns:
            Updated Template object
        Raises:
            Exception: If template is not found or update fails
        """
        template = self.get_template(template_id)
        if template is None:
            raise Exception("Template not found")

        try:
            # Create new version if content is updated
            if 'content' in updates:
                self._create_version(template)
                # Update version number
                current_version = float(template.version)
                template.version = f"{current_version + 0.1:.1f}"

            # Update template attributes
            for key, value in updates.items():
                if hasattr(template, key):
                    setattr(template, key, value)

            template.updated_at = datetime.now().isoformat()
            self._save_template(template)
            return template

        except Exception as e:
            raise Exception(f"Failed to update template: {str(e)}")

    def list_templates(self, template_type: str = None) -> List[Template]:
        """
        List all templates, optionally filtered by type
        Args:
            template_type: Template type filter
        Returns:
            List of Template objects
        """
        templates = []
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                template = self.get_template(filename[:-5])
                if template and (not template_type or template.type == template_type):
                    templates.append(template)
        return templates

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template
        Args:
            template_id: Template identifier
        Returns:
            bool indicating success
        """
        template_file = os.path.join(self.templates_dir, f"{template_id}.json")
        if not os.path.exists(template_file):
            return False

        try:
            os.remove(template_file)
            # Also remove versions
            version_dir = os.path.join(self.versions_dir, template_id)
            if os.path.exists(version_dir):
                shutil.rmtree(version_dir)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete template: {str(e)}")

    def _save_template(self, template: Template):
        """Save template data to file"""
        template_file = os.path.join(self.templates_dir, f"{template.id}.json")
        with open(template_file, 'w') as f:
            json.dump(asdict(template), f, indent=2)

    def _create_version(self, template: Template):
        """Create a new version of template"""
        version_dir = os.path.join(self.versions_dir, template.id)
        os.makedirs(version_dir, exist_ok=True)

        version_file = os.path.join(
            version_dir,
            f"v{template.version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(version_file, 'w') as f:
            json.dump(asdict(template), f, indent=2)

    def get_template_versions(self, template_id: str) -> List[Dict]:
        """
        Get version history of a template
        Args:
            template_id: Template identifier
        Returns:
            List of version information
        """
        version_dir = os.path.join(self.versions_dir, template_id)
        if not os.path.exists(version_dir):
            return []

        versions = []
        for filename in os.listdir(version_dir):
            if filename.endswith('.json'):
                with open(os.path.join(version_dir, filename), 'r') as f:
                    data = json.load(f)
                    versions.append({
                        'version': data['version'],
                        'updated_at': data['updated_at'],
                        'author': data['author']
                    })

        return sorted(versions, key=lambda x: float(x['version']))

    def render_template(self, template_id: str, variables: Dict) -> str:
        """
        Render template with provided variables
        Args:
            template_id: Template identifier
            variables: Dictionary of variables to replace
        Returns:
            Rendered template content
        """
        template = self.get_template(template_id)
        if template is None:
            raise Exception("Template not found")

        try:
            content = template.content
            for key, value in variables.items():
                placeholder = f"[{key}]"
                content = content.replace(placeholder, str(value))
            return content

        except Exception as e:
            raise Exception(f"Failed to render template: {str(e)}") 