"""
Template Validator for Template Management Instrument
Handles template validation and verification
"""

import re
from typing import Dict, List, Tuple, Optional

class TemplateValidator:
    def __init__(self):
        """Initialize template validator"""
        self.required_fields = {
            'proposal': [
                'project_title',
                'duration',
                'location',
                'budget',
                'objectives',
                'activities'
            ],
            'report': [
                'project_title',
                'reporting_period',
                'prepared_by',
                'activities',
                'progress',
                'challenges'
            ],
            'research': [
                'title',
                'researcher',
                'objectives',
                'methodology',
                'findings'
            ]
        }

        self.field_patterns = {
            'project_title': r'^[A-Za-z0-9\s\-_]{5,100}$',
            'budget': r'^\d+(\.\d{1,2})?$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^\+?[\d\-\s]{10,15}$',
            'date': r'^\d{4}-\d{2}-\d{2}$'
        }

    def validate_template(self, template_type: str, content: str) -> Tuple[bool, List[str]]:
        """
        Validate template content
        Args:
            template_type: Type of template
            content: Template content
        Returns:
            Tuple of (is_valid, list of errors)
        """
        if not content or not isinstance(content, str):
            return False, ["Template content must be a non-empty string"]
            
        if not template_type or not isinstance(template_type, str):
            return False, ["Template type must be a non-empty string"]

        errors = []

        # Check required fields
        if template_type in self.required_fields:
            missing_fields = self._check_required_fields(
                content,
                self.required_fields[template_type]
            )
            errors.extend(missing_fields)

        # Validate structure
        structure_errors = self._validate_structure(content)
        errors.extend(structure_errors)

        # Validate placeholders
        placeholder_errors = self._validate_placeholders(content)
        errors.extend(placeholder_errors)

        return len(errors) == 0, errors

    def _check_required_fields(self, content: str, required_fields: List[str]) -> List[str]:
        """Check if all required fields are present in template"""
        if not required_fields:
            return []
            
        errors = []
        for field in required_fields:
            if not field or not isinstance(field, str):
                continue
            placeholder = f"[{field}]"
            if placeholder not in content:
                errors.append(f"Missing required field: {field}")
        return errors

    def _validate_structure(self, content: str) -> List[str]:
        """Validate template structure"""
        errors = []

        try:
            # Check for balanced sections
            section_pattern = r'#{1,6}\s+.+'
            sections = re.findall(section_pattern, content)
            
            # Check section hierarchy
            current_level = 1
            for section in sections:
                match = re.match(r'^#+', section)
                if match:
                    level = len(match.group())
                    if level > current_level + 1:
                        errors.append(f"Invalid section hierarchy: {section.strip()}")
                    current_level = level

            # Check for balanced lists
            list_starts = content.count('- ')
            list_newlines = content.count('\n- ')
            if list_starts > 0 and list_starts != list_newlines + (1 if content.startswith('- ') else 0):
                errors.append("Unbalanced list items found")

            # Check for balanced tables
            table_rows = re.findall(r'\|[^|]+\|', content)
            if table_rows:
                first_row_cols = len(table_rows[0].split('|'))
                for i, row in enumerate(table_rows[1:], 1):
                    cols = len(row.split('|'))
                    if cols != first_row_cols:
                        errors.append(f"Inconsistent table column count in row {i+1}: expected {first_row_cols}, got {cols}")

        except Exception as e:
            errors.append(f"Structure validation error: {str(e)}")

        return errors

    def _validate_placeholders(self, content: str) -> List[str]:
        """Validate template placeholders"""
        errors = []
        
        try:
            # Find all placeholders
            placeholders = re.findall(r'\[([^\]]+)\]', content)
            
            for placeholder in placeholders:
                # Check placeholder naming
                if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', placeholder):
                    errors.append(f"Invalid placeholder name '{placeholder}': must start with a letter and contain only letters, numbers, and underscores")
                
                # Check if placeholder has corresponding pattern
                if placeholder in self.field_patterns:
                    pattern = self.field_patterns[placeholder]
                    if not self._is_valid_pattern(pattern):
                        errors.append(f"Invalid pattern for placeholder '{placeholder}': pattern compilation failed")

            # Check for unmatched brackets
            open_brackets = content.count('[')
            close_brackets = content.count(']')
            if open_brackets != close_brackets:
                errors.append(f"Unmatched brackets: {open_brackets} opening brackets and {close_brackets} closing brackets")

        except Exception as e:
            errors.append(f"Placeholder validation error: {str(e)}")

        return errors

    def _is_valid_pattern(self, pattern: str) -> bool:
        """Check if regex pattern is valid"""
        if not pattern or not isinstance(pattern, str):
            return False
            
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False

    def validate_field_value(self, field: str, value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a field value against its pattern
        Args:
            field: Field name
            value: Value to validate
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not field or not isinstance(field, str):
            return False, "Field name must be a non-empty string"
            
        if not isinstance(value, str):
            return False, f"Value for field '{field}' must be a string"

        if field not in self.field_patterns:
            return True, None

        pattern = self.field_patterns[field]
        if not self._is_valid_pattern(pattern):
            return False, f"Invalid pattern defined for field '{field}'"

        try:
            if not re.match(pattern, value):
                return False, f"Invalid format for field '{field}'"
        except Exception as e:
            return False, f"Error validating field '{field}': {str(e)}"

        return True, None

    def validate_variables(self, template_type: str, variables: Dict) -> Tuple[bool, List[str]]:
        """
        Validate template variables
        Args:
            template_type: Type of template
            variables: Dictionary of variables
        Returns:
            Tuple of (is_valid, list of errors)
        """
        if not template_type or not isinstance(template_type, str):
            return False, ["Template type must be a non-empty string"]
            
        if not isinstance(variables, dict):
            return False, ["Variables must be provided as a dictionary"]

        errors = []

        try:
            # Check required variables
            if template_type in self.required_fields:
                for field in self.required_fields[template_type]:
                    if field not in variables:
                        errors.append(f"Missing required variable: {field}")
                    else:
                        # Validate value format
                        is_valid, error = self.validate_field_value(field, str(variables[field]))
                        if not is_valid and error is not None:
                            errors.append(error)

        except Exception as e:
            errors.append(f"Variable validation error: {str(e)}")

        return len(errors) == 0, errors 