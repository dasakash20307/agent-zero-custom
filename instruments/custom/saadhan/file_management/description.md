# File Management Instrument

## Overview
The File Management Instrument provides comprehensive file handling capabilities for the Saadhan AI Assistant. It includes features for file versioning, automatic backups, and file categorization.

## Components

### 1. FileManager
The main component that handles basic file operations and management.

#### Key Features:
- Automatic file backups
- File categorization
- Size formatting
- Directory management

#### Main Methods:
- `create_backup(file_path)`: Creates a backup of a specified file
- `restore_backup(backup_path, target_path)`: Restores a file from backup
- `list_backups(file_path)`: Lists all backups for a specific file
- `categorize_file(file_path)`: Categorizes a file based on its properties
- `auto_backup(file_path, max_backups)`: Creates automatic backup with rotation

### 2. VersionControl
Handles version tracking and management of files.

#### Key Features:
- Version creation and tracking
- File content hashing
- Version comparison
- Version restoration

#### Main Methods:
- `create_version(file_path, comment)`: Creates a new version of a file
- `get_versions(file_path)`: Gets all versions of a file
- `get_version(version_id)`: Gets a specific version by ID
- `restore_version(version_id, target_path)`: Restores a specific version
- `compare_versions(version_id1, version_id2)`: Compares two versions

## Usage Examples

### Basic File Management
```python
# Initialize file manager
file_manager = FileManager(base_dir="/path/to/workspace")

# Create backup
backup_path = file_manager.create_backup("document.txt")

# List backups
backups = file_manager.list_backups("document.txt")

# Restore from backup
file_manager.restore_backup(backup_path)

# Get file categorization
info = file_manager.categorize_file("document.txt")
```

### Version Control
```python
# Initialize version control
version_control = VersionControl(base_dir="/path/to/workspace")

# Create new version
version = version_control.create_version(
    "document.txt",
    comment="Added new section"
)

# Get version history
versions = version_control.get_versions("document.txt")

# Restore specific version
version_control.restore_version(version.version_id)

# Compare versions
comparison = version_control.compare_versions(
    version_id1="v1",
    version_id2="v2"
)
```

## Directory Structure
```
file_management/
├── __init__.py
├── file_manager.py
├── version_control.py
└── description.md
```

## Integration with Other Instruments
The File Management Instrument is designed to work seamlessly with other Saadhan instruments:

- **Template Management**: Provides version control for templates
- **Project Management**: Handles project file organization
- **Research**: Manages research document versions
- **Report Generation**: Controls report file versions

## Error Handling
The instrument includes comprehensive error handling for common scenarios:
- File not found
- Invalid backup/version
- Permission issues
- Storage constraints

## Best Practices
1. Regular backups of important files
2. Meaningful version comments
3. Proper file categorization
4. Regular cleanup of old backups
5. Version tracking for critical documents

## Dependencies
- Python 3.7+
- pathlib
- hashlib
- datetime
- typing
- dataclasses 