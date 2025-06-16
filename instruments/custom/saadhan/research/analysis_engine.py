"""
Analysis Engine for Research Instrument
Handles data analysis and visualization
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AnalysisResult:
    """Analysis result data structure"""
    id: str
    title: str
    description: str
    data_source: str
    method: str
    parameters: Dict
    results: Dict
    visualizations: List[str]
    created_at: str
    analyst: str

class AnalysisEngine:
    def __init__(self, workspace_root: str):
        """
        Initialize analysis engine
        Args:
            workspace_root: Path to workspace root directory
        """
        self.workspace_root = workspace_root
        self.analysis_dir = os.path.join(workspace_root, 'research_analysis')
        self.results_dir = os.path.join(self.analysis_dir, 'results')
        self.viz_dir = os.path.join(self.analysis_dir, 'visualizations')
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.analysis_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.viz_dir, exist_ok=True)

    def analyze_survey_data(self, survey_data: Dict[str, Any], analysis_params: Dict[str, Any]) -> AnalysisResult:
        """
        Analyze survey data
        Args:
            survey_data: Survey data to analyze
            analysis_params: Analysis parameters
        Returns:
            AnalysisResult object
        """
        try:
            analysis_id = f"ANL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Perform basic statistical analysis
            results = {
                'response_count': len(survey_data['responses']),
                'completion_rate': self._calculate_completion_rate(survey_data),
                'question_analysis': self._analyze_questions(survey_data),
                'cross_tabulation': self._perform_cross_tabulation(survey_data, analysis_params)
            }

            # Generate visualizations
            visualizations = self._generate_survey_visualizations(
                survey_data,
                analysis_params,
                analysis_id
            )

            result = AnalysisResult(
                id=analysis_id,
                title=analysis_params['title'],
                description=analysis_params['description'],
                data_source='survey',
                method='statistical_analysis',
                parameters=analysis_params,
                results=results,
                visualizations=visualizations,
                created_at=datetime.now().isoformat(),
                analyst=analysis_params.get('analyst', 'system')
            )

            self._save_analysis_result(result)
            return result

        except Exception as e:
            raise Exception(f"Failed to analyze survey data: {str(e)}")

    def analyze_interview_data(self, interview_data: Dict, analysis_params: Dict) -> AnalysisResult:
        """
        Analyze interview data
        Args:
            interview_data: Interview data to analyze
            analysis_params: Analysis parameters
        Returns:
            AnalysisResult object
        """
        try:
            analysis_id = f"ANL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Perform qualitative analysis
            results = {
                'themes': self._identify_themes(interview_data),
                'key_insights': self._extract_key_insights(interview_data),
                'sentiment_analysis': self._analyze_sentiment(interview_data),
                'word_frequency': self._analyze_word_frequency(interview_data)
            }

            result = AnalysisResult(
                id=analysis_id,
                title=analysis_params['title'],
                description=analysis_params['description'],
                data_source='interview',
                method='qualitative_analysis',
                parameters=analysis_params,
                results=results,
                visualizations=[],  # Qualitative analysis typically doesn't have visualizations
                created_at=datetime.now().isoformat(),
                analyst=analysis_params.get('analyst', 'system')
            )

            self._save_analysis_result(result)
            return result

        except Exception as e:
            raise Exception(f"Failed to analyze interview data: {str(e)}")

    def analyze_observation_data(self, observation_data: Dict, analysis_params: Dict) -> AnalysisResult:
        """
        Analyze observation data
        Args:
            observation_data: Observation data to analyze
            analysis_params: Analysis parameters
        Returns:
            AnalysisResult object
        """
        try:
            analysis_id = f"ANL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Perform observation analysis
            results = {
                'patterns': self._identify_patterns(observation_data),
                'categories': self._analyze_categories(observation_data),
                'temporal_analysis': self._analyze_temporal_patterns(observation_data),
                'spatial_analysis': self._analyze_spatial_patterns(observation_data)
            }

            result = AnalysisResult(
                id=analysis_id,
                title=analysis_params['title'],
                description=analysis_params['description'],
                data_source='observation',
                method='observational_analysis',
                parameters=analysis_params,
                results=results,
                visualizations=[],
                created_at=datetime.now().isoformat(),
                analyst=analysis_params.get('analyst', 'system')
            )

            self._save_analysis_result(result)
            return result

        except Exception as e:
            raise Exception(f"Failed to analyze observation data: {str(e)}")

    def _calculate_completion_rate(self, survey_data: Dict) -> float:
        """Calculate survey completion rate"""
        total_questions = len(survey_data['questions'])
        completed_responses = 0
        
        for response in survey_data['responses']:
            answered_questions = len(response['data'])
            if answered_questions == total_questions:
                completed_responses += 1
                
        return completed_responses / len(survey_data['responses']) if survey_data['responses'] else 0

    def _analyze_questions(self, survey_data: Dict) -> Dict:
        """Analyze individual questions"""
        analysis = {}
        
        for question in survey_data['questions']:
            responses = [r['data'].get(question['id']) for r in survey_data['responses']]
            analysis[question['id']] = {
                'response_count': len([r for r in responses if r]),
                'unique_responses': len(set(responses)),
                'frequency': self._calculate_frequency(responses)
            }
            
        return analysis

    def _calculate_frequency(self, responses: List) -> Dict:
        """Calculate frequency distribution of responses"""
        frequency = {}
        for response in responses:
            if response:
                frequency[response] = frequency.get(response, 0) + 1
        return frequency

    def _perform_cross_tabulation(self, survey_data: Dict, analysis_params: Dict) -> Dict:
        """Perform cross-tabulation analysis"""
        cross_tab = {}
        if 'cross_tabulation' in analysis_params:
            for var1, var2 in analysis_params['cross_tabulation']:
                key = f"{var1}_vs_{var2}"
                cross_tab[key] = self._cross_tabulate(
                    survey_data['responses'],
                    var1,
                    var2
                )
        return cross_tab

    def _cross_tabulate(self, responses: List[Dict], var1: str, var2: str) -> Dict:
        """Create cross-tabulation table"""
        table = {}
        for response in responses:
            val1 = response['data'].get(var1)
            val2 = response['data'].get(var2)
            if val1 and val2:
                if val1 not in table:
                    table[val1] = {}
                table[val1][val2] = table[val1].get(val2, 0) + 1
        return table

    def _generate_survey_visualizations(
        self,
        survey_data: Dict,
        analysis_params: Dict,
        analysis_id: str
    ) -> List[str]:
        """Generate visualizations for survey data"""
        visualizations = []
        
        # Implementation would include actual visualization generation
        # For now, we'll just return placeholder paths
        viz_types = ['response_distribution', 'completion_trends', 'cross_tabulation']
        
        for viz_type in viz_types:
            viz_path = os.path.join(
                self.viz_dir,
                f"{analysis_id}_{viz_type}.png"
            )
            visualizations.append(viz_path)
            
        return visualizations

    def _identify_themes(self, interview_data: Dict) -> List[Dict]:
        """Identify themes in interview responses"""
        # Implementation would include actual theme identification
        # For now, return placeholder data
        return [
            {'theme': 'Theme 1', 'frequency': 5, 'examples': []},
            {'theme': 'Theme 2', 'frequency': 3, 'examples': []}
        ]

    def _extract_key_insights(self, interview_data: Dict) -> List[str]:
        """Extract key insights from interview data"""
        # Implementation would include actual insight extraction
        return ['Insight 1', 'Insight 2']

    def _analyze_sentiment(self, interview_data: Dict) -> Dict:
        """Perform sentiment analysis on interview responses"""
        # Implementation would include actual sentiment analysis
        return {
            'overall_sentiment': 'positive',
            'sentiment_scores': {'positive': 0.6, 'neutral': 0.3, 'negative': 0.1}
        }

    def _analyze_word_frequency(self, interview_data: Dict) -> Dict:
        """Analyze word frequency in interview responses"""
        # Implementation would include actual word frequency analysis
        return {'word1': 10, 'word2': 8, 'word3': 5}

    def _identify_patterns(self, observation_data: Dict) -> List[Dict]:
        """Identify patterns in observation data"""
        # Implementation would include actual pattern identification
        return [
            {'pattern': 'Pattern 1', 'frequency': 3, 'context': ''},
            {'pattern': 'Pattern 2', 'frequency': 2, 'context': ''}
        ]

    def _analyze_categories(self, observation_data: Dict) -> Dict:
        """Analyze observation categories"""
        # Implementation would include actual category analysis
        return {
            'category1': {'count': 5, 'examples': []},
            'category2': {'count': 3, 'examples': []}
        }

    def _analyze_temporal_patterns(self, observation_data: Dict) -> Dict:
        """Analyze temporal patterns in observations"""
        # Implementation would include actual temporal analysis
        return {
            'time_of_day': {'morning': 5, 'afternoon': 3, 'evening': 2},
            'day_of_week': {'monday': 2, 'tuesday': 3, 'wednesday': 5}
        }

    def _analyze_spatial_patterns(self, observation_data: Dict) -> Dict:
        """Analyze spatial patterns in observations"""
        # Implementation would include actual spatial analysis
        return {
            'location1': {'frequency': 5, 'patterns': []},
            'location2': {'frequency': 3, 'patterns': []}
        }

    def _save_analysis_result(self, result: AnalysisResult):
        """Save analysis result to file"""
        result_file = os.path.join(self.results_dir, f"{result.id}.json")
        with open(result_file, 'w') as f:
            json.dump({
                'id': result.id,
                'title': result.title,
                'description': result.description,
                'data_source': result.data_source,
                'method': result.method,
                'parameters': result.parameters,
                'results': result.results,
                'visualizations': result.visualizations,
                'created_at': result.created_at,
                'analyst': result.analyst
            }, f, indent=2)

    def get_analysis_result(self, analysis_id: str) -> Optional[AnalysisResult]:
        """
        Retrieve analysis result
        Args:
            analysis_id: Analysis identifier
        Returns:
            AnalysisResult object if found, None otherwise
        """
        result_file = os.path.join(self.results_dir, f"{analysis_id}.json")
        if not os.path.exists(result_file):
            return None

        with open(result_file, 'r') as f:
            data = json.load(f)
            return AnalysisResult(**data) 