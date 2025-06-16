"""
Tests for Project Management module
"""
import os
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from instruments.custom.saadhan.project_management import ProjectManager
from instruments.custom.saadhan.file_management import FileManager, VersionControl
from instruments.custom.saadhan.template_management import TemplateManager

@pytest.fixture
def test_workspace(tmp_path):
    """Create a temporary workspace for testing"""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    return workspace

@pytest.fixture
def project_manager(test_workspace):
    """Create a project manager instance"""
    return ProjectManager(test_workspace)

def test_create_project(project_manager):
    """Test project creation"""
    # Test data
    title = "Test Project"
    description = "A test project"
    start_date = datetime.now().isoformat()
    end_date = datetime.now().isoformat()
    metadata = {"key": "value"}
    
    # Create project
    project = project_manager.create_project(
        title=title,
        description=description,
        start_date=start_date,
        end_date=end_date,
        metadata=metadata
    )
    
    # Verify project
    assert project.title == title
    assert project.description == description
    assert project.start_date == start_date
    assert project.end_date == end_date
    assert project.metadata == metadata
    assert project.status == "planned"
    assert project.progress == 0.0
    assert len(project.activities) == 0
    assert len(project.beneficiaries) == 0

def test_update_project(project_manager):
    """Test project update"""
    # Create project
    project = project_manager.create_project(
        title="Test Project",
        description="A test project",
        start_date=datetime.now().isoformat(),
        end_date=datetime.now().isoformat()
    )
    
    # Update data
    updates = {
        "title": "Updated Project",
        "description": "Updated description",
        "status": "in_progress"
    }
    
    # Update project
    updated = project_manager.update_project(project.id, updates)
    
    # Verify updates
    assert updated.title == updates["title"]
    assert updated.description == updates["description"]
    assert updated.status == updates["status"]

def test_add_activity(project_manager):
    """Test adding activity to project"""
    # Create project
    project = project_manager.create_project(
        title="Test Project",
        description="A test project",
        start_date=datetime.now().isoformat(),
        end_date=datetime.now().isoformat()
    )
    
    # Activity data
    title = "Test Activity"
    description = "A test activity"
    start_date = datetime.now().isoformat()
    end_date = datetime.now().isoformat()
    
    # Add activity
    activity = project_manager.add_activity(
        project.id,
        title=title,
        description=description,
        start_date=start_date,
        end_date=end_date
    )
    
    # Verify activity
    assert activity.title == title
    assert activity.description == description
    assert activity.start_date == start_date
    assert activity.end_date == end_date
    assert activity.status == "planned"
    assert activity.progress == 0.0

def test_add_beneficiary(project_manager):
    """Test adding beneficiary to project"""
    # Create project
    project = project_manager.create_project(
        title="Test Project",
        description="A test project",
        start_date=datetime.now().isoformat(),
        end_date=datetime.now().isoformat()
    )
    
    # Beneficiary data
    name = "Test Beneficiary"
    type = "individual"
    contact = "test@example.com"
    benefits = ["benefit1", "benefit2"]
    
    # Add beneficiary
    beneficiary = project_manager.add_beneficiary(
        project.id,
        name=name,
        type=type,
        contact=contact,
        benefits=benefits
    )
    
    # Verify beneficiary
    assert beneficiary.name == name
    assert beneficiary.type == type
    assert beneficiary.contact == contact
    assert beneficiary.benefits == benefits

def test_update_progress(project_manager):
    """Test updating project and activity progress"""
    # Create project
    project = project_manager.create_project(
        title="Test Project",
        description="A test project",
        start_date=datetime.now().isoformat(),
        end_date=datetime.now().isoformat()
    )
    
    # Add activity
    activity = project_manager.add_activity(
        project.id,
        title="Test Activity",
        description="A test activity",
        start_date=datetime.now().isoformat(),
        end_date=datetime.now().isoformat()
    )
    
    # Update activity progress
    progress = 50.0
    updated_progress = project_manager.update_progress(
        project.id,
        activity_id=activity.id,
        progress=progress
    )
    
    # Verify progress
    assert updated_progress == progress
    
    # Get updated project
    updated_project = project_manager.get_project(project.id)
    assert updated_project.progress == progress  # Since there's only one activity

def test_generate_report(project_manager):
    """Test generating project report"""
    # Create project with activities and beneficiaries
    project = project_manager.create_project(
        title="Test Project",
        description="A test project",
        start_date=datetime.now().isoformat(),
        end_date=datetime.now().isoformat()
    )
    
    # Add activity
    project_manager.add_activity(
        project.id,
        title="Test Activity",
        description="A test activity",
        start_date=datetime.now().isoformat(),
        end_date=datetime.now().isoformat()
    )
    
    # Add beneficiary
    project_manager.add_beneficiary(
        project.id,
        name="Test Beneficiary",
        type="individual",
        contact="test@example.com",
        benefits=["benefit1"]
    )
    
    # Generate report
    report = project_manager.generate_report(project.id)
    
    # Verify report structure
    assert isinstance(report, dict)
    assert "project_id" in report
    assert "title" in report
    assert "description" in report
    assert "status" in report
    assert "progress" in report
    assert "activities" in report
    assert "beneficiaries" in report 