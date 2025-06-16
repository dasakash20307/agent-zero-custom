"""
Data Collector for Research Instrument
Handles data collection and organization
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class Survey:
    """Survey data structure"""
    id: str
    title: str
    description: str
    questions: List[Dict]
    target_respondents: int
    responses: List[Dict]
    status: str
    created_at: str
    last_updated: str

@dataclass
class Interview:
    """Interview data structure"""
    id: str
    title: str
    interviewee: str
    date: str
    location: str
    questions: List[str]
    responses: Dict[str, str]
    notes: str
    status: str
    recorded: bool
    recording_path: Optional[str]

@dataclass
class Observation:
    """Field observation data structure"""
    id: str
    title: str
    date: str
    location: str
    observer: str
    target: str
    notes: str
    attachments: List[str]
    categories: List[str]

class DataCollector:
    def __init__(self, workspace_root: str):
        """
        Initialize data collector
        Args:
            workspace_root: Path to workspace root directory
        """
        self.workspace_root = workspace_root
        self.data_dir = os.path.join(workspace_root, 'research_data')
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, 'surveys'), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, 'interviews'), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, 'observations'), exist_ok=True)

    def create_survey(self, survey_data: Dict) -> Survey:
        """
        Create a new survey
        Args:
            survey_data: Dictionary containing survey information
        Returns:
            Survey object
        """
        try:
            survey_id = f"SRV_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            survey = Survey(
                id=survey_id,
                title=survey_data['title'],
                description=survey_data['description'],
                questions=survey_data['questions'],
                target_respondents=survey_data['target_respondents'],
                responses=[],
                status='active',
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat()
            )

            self._save_survey(survey)
            return survey

        except Exception as e:
            raise Exception(f"Failed to create survey: {str(e)}")

    def add_survey_response(self, survey_id: str, response_data: Dict) -> Survey:
        """
        Add response to survey
        Args:
            survey_id: Survey identifier
            response_data: Dictionary containing response data
        Returns:
            Updated Survey object
        """
        survey = self.get_survey(survey_id)
        if survey is None:
            raise Exception("Survey not found")

        try:
            response = {
                'id': f"RSP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'data': response_data,
                'timestamp': datetime.now().isoformat()
            }
            
            survey.responses.append(response)
            survey.last_updated = datetime.now().isoformat()
            self._save_survey(survey)
            return survey

        except Exception as e:
            raise Exception(f"Failed to add survey response: {str(e)}")

    def create_interview(self, interview_data: Dict) -> Interview:
        """
        Create a new interview
        Args:
            interview_data: Dictionary containing interview information
        Returns:
            Interview object
        """
        try:
            interview_id = f"INT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            interview = Interview(
                id=interview_id,
                title=interview_data['title'],
                interviewee=interview_data['interviewee'],
                date=interview_data['date'],
                location=interview_data['location'],
                questions=interview_data['questions'],
                responses={},
                notes=interview_data.get('notes', ''),
                status='scheduled',
                recorded=interview_data.get('recorded', False),
                recording_path=interview_data.get('recording_path', None)
            )

            self._save_interview(interview)
            return interview

        except Exception as e:
            raise Exception(f"Failed to create interview: {str(e)}")

    def update_interview(self, interview_id: str, responses: Dict[str, str], notes: str = None) -> Interview:
        """
        Update interview with responses
        Args:
            interview_id: Interview identifier
            responses: Dictionary of question-response pairs
            notes: Additional notes
        Returns:
            Updated Interview object
        """
        interview = self.get_interview(interview_id)
        if interview is None:
            raise Exception("Interview not found")

        try:
            interview.responses = responses
            if notes:
                interview.notes = notes
            interview.status = 'completed'
            self._save_interview(interview)
            return interview

        except Exception as e:
            raise Exception(f"Failed to update interview: {str(e)}")

    def create_observation(self, observation_data: Dict) -> Observation:
        """
        Create a new field observation
        Args:
            observation_data: Dictionary containing observation information
        Returns:
            Observation object
        """
        try:
            observation_id = f"OBS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            observation = Observation(
                id=observation_id,
                title=observation_data['title'],
                date=observation_data['date'],
                location=observation_data['location'],
                observer=observation_data['observer'],
                target=observation_data['target'],
                notes=observation_data['notes'],
                attachments=observation_data.get('attachments', []),
                categories=observation_data.get('categories', [])
            )

            self._save_observation(observation)
            return observation

        except Exception as e:
            raise Exception(f"Failed to create observation: {str(e)}")

    def export_data(self, data_type: str, data_id: str, format: str = 'json') -> str:
        """
        Export collected data in specified format
        Args:
            data_type: Type of data (survey/interview/observation)
            data_id: Data identifier
            format: Export format (json/csv)
        Returns:
            Path to exported file
        """
        try:
            if data_type == 'survey':
                data = self.get_survey(data_id)
            elif data_type == 'interview':
                data = self.get_interview(data_id)
            elif data_type == 'observation':
                data = self.get_observation(data_id)
            else:
                raise ValueError("Invalid data type")

            if data is None:
                raise Exception("Data not found")

            export_dir = os.path.join(self.data_dir, 'exports')
            os.makedirs(export_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_path = os.path.join(export_dir, f"{data_id}_{timestamp}.{format}")

            if format == 'json':
                with open(export_path, 'w') as f:
                    json.dump(asdict(data), f, indent=2)
            elif format == 'csv':
                if data_type == 'survey':
                    self._export_survey_csv(data, export_path)
                else:
                    raise ValueError(f"CSV export not supported for {data_type}")
            else:
                raise ValueError("Unsupported export format")

            return export_path

        except Exception as e:
            raise Exception(f"Failed to export data: {str(e)}")

    def _export_survey_csv(self, survey: Survey, export_path: str):
        """Export survey data to CSV format"""
        try:
            # Prepare headers
            headers = ['response_id', 'timestamp']
            for question in survey.questions:
                headers.append(question['text'])

            # Write to CSV
            with open(export_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)

                for response in survey.responses:
                    row = [response['id'], response['timestamp']]
                    for question in survey.questions:
                        row.append(response['data'].get(question['id'], ''))
                    writer.writerow(row)

        except Exception as e:
            raise Exception(f"Failed to export survey to CSV: {str(e)}")

    def _save_survey(self, survey: Survey):
        """Save survey data to file"""
        survey_file = os.path.join(self.data_dir, 'surveys', f"{survey.id}.json")
        with open(survey_file, 'w') as f:
            json.dump(asdict(survey), f, indent=2)

    def _save_interview(self, interview: Interview):
        """Save interview data to file"""
        interview_file = os.path.join(self.data_dir, 'interviews', f"{interview.id}.json")
        with open(interview_file, 'w') as f:
            json.dump(asdict(interview), f, indent=2)

    def _save_observation(self, observation: Observation):
        """Save observation data to file"""
        observation_file = os.path.join(self.data_dir, 'observations', f"{observation.id}.json")
        with open(observation_file, 'w') as f:
            json.dump(asdict(observation), f, indent=2)

    def get_survey(self, survey_id: str) -> Optional[Survey]:
        """Get survey by ID"""
        survey_file = os.path.join(self.data_dir, 'surveys', f"{survey_id}.json")
        if not os.path.exists(survey_file):
            return None

        with open(survey_file, 'r') as f:
            data = json.load(f)
            return Survey(**data)

    def get_interview(self, interview_id: str) -> Optional[Interview]:
        """Get interview by ID"""
        interview_file = os.path.join(self.data_dir, 'interviews', f"{interview_id}.json")
        if not os.path.exists(interview_file):
            return None

        with open(interview_file, 'r') as f:
            data = json.load(f)
            return Interview(**data)

    def get_observation(self, observation_id: str) -> Optional[Observation]:
        """Get observation by ID"""
        observation_file = os.path.join(self.data_dir, 'observations', f"{observation_id}.json")
        if not os.path.exists(observation_file):
            return None

        with open(observation_file, 'r') as f:
            data = json.load(f)
            return Observation(**data) 