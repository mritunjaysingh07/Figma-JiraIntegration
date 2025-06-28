from typing import Dict, List, Set
from datetime import datetime
import json
from pathlib import Path
from ..validators.models import FigmaElement, JiraStory
from loguru import logger

class EnhancedCoverageTracker:
    def __init__(self):
        self.history_file = Path("coverage_history.json")
        self.current_coverage = {}
        self._load_history()

    def _load_history(self):
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = []

    def analyze_coverage(self, elements: List[FigmaElement], stories: List[JiraStory]) -> Dict:
        total_elements = len(elements)
        processed_elements = len(stories)
        
        self.current_coverage = {
            'total_elements': total_elements,
            'processed_elements': processed_elements,
            'coverage_percentage': (processed_elements / total_elements * 100),
            'element_type_coverage': self._analyze_type_coverage(elements, stories),
            'missing_elements': self._find_missing_elements(elements, stories)
        }
        
        coverage_data = self._calculate_coverage(elements, stories)
        self._record_coverage(coverage_data)
        
        logger.info(f"Design coverage: {self.current_coverage['coverage_percentage']}%")
        return self.current_coverage

    def _calculate_coverage(self, elements: List[FigmaElement], stories: List[JiraStory]) -> Dict:
        element_types = self._get_element_types(elements)
        story_elements = self._get_story_elements(stories)
        
        coverage = {
            'timestamp': datetime.now().isoformat(),
            'total_elements': len(elements),
            'total_stories': len(stories),
            'coverage_by_type': self._calculate_type_coverage(elements, story_elements),
            'missing_elements': list(self._find_missing_elements(elements, story_elements)),
            'patterns': self._analyze_patterns(elements, stories)
        }
        
        coverage['overall_percentage'] = (len(stories) / len(elements)) * 100
        return coverage

    def _get_element_types(self, elements: List[FigmaElement]) -> Set[str]:
        return {el.get('type') for el in elements if el.get('type')}

    def _get_story_elements(self, stories: List[JiraStory]) -> Set[str]:
        return {story.get('element_id') for story in stories if story.get('element_id')}

    def _record_coverage(self, coverage_data: Dict):
        self.history.append(coverage_data)
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def get_coverage_trends(self) -> Dict:
        if not self.history:
            return {}
            
        return {
            'trend': self._calculate_trend(),
            'common_missing_patterns': self._analyze_missing_patterns(),
            'improvement_suggestions': self._generate_suggestions()
        }

    def _analyze_type_coverage(self, elements: List[FigmaElement], stories: List[JiraStory]) -> Dict:
        type_counts = {}
        for element in elements:
            type_counts[element.type] = type_counts.get(element.type, 0) + 1
        return type_counts

    def _find_missing_elements(self, elements: List[FigmaElement], stories: List[JiraStory]) -> List[str]:
        story_elements = {story.title for story in stories}
        return [element.name for element in elements if element.name not in story_elements]