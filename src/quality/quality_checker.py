from typing import Dict, List
from enum import Enum
from dataclasses import dataclass
from loguru import logger

class QualityMetric(Enum):
    TITLE_QUALITY = "title_quality"
    USER_STORY_FORMAT = "user_story_format"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    TECHNICAL_REQUIREMENTS = "technical_requirements"
    STORY_POINTS_VALIDITY = "story_points_validity"

@dataclass
class QualityThreshold:
    metric: QualityMetric
    min_score: float
    weight: float

class QualityChecker:  # This is the correct class name
    def __init__(self):
        self.thresholds = [
            QualityThreshold(QualityMetric.TITLE_QUALITY, 0.7, 0.2),
            QualityThreshold(QualityMetric.USER_STORY_FORMAT, 0.8, 0.3),
            QualityThreshold(QualityMetric.ACCEPTANCE_CRITERIA, 0.7, 0.3),
            QualityThreshold(QualityMetric.TECHNICAL_REQUIREMENTS, 0.6, 0.2)
        ]

    def check_quality(self, story: Dict) -> Dict:
        scores = {}
        total_score = 0
        issues = []
        suggestions = []
        
        for threshold in self.thresholds:
            score, issue, suggestion = self._check_metric(threshold.metric, story)
            weighted_score = score * threshold.weight
            total_score += weighted_score
            scores[threshold.metric.value] = score
            
            if issue:
                issues.append(issue)
            if suggestion:
                suggestions.append(suggestion)

        passes_threshold = total_score >= 0.8
        
        return {
            'passes_threshold': passes_threshold,
            'total_score': total_score,
            'metric_scores': scores,
            'issues': issues,
            'suggestions': suggestions
        }

    def _check_metric(self, metric: QualityMetric, story: Dict) -> tuple[float, str, str]:
        if metric == QualityMetric.TITLE_QUALITY:
            return self._check_title_quality(story.get('title', ''))
        elif metric == QualityMetric.USER_STORY_FORMAT:
            return self._check_user_story_format(story.get('user_story', ''))
        elif metric == QualityMetric.ACCEPTANCE_CRITERIA:
            return self._check_acceptance_criteria(story.get('acceptance_criteria', []))
        elif metric == QualityMetric.TECHNICAL_REQUIREMENTS:
            return self._check_technical_requirements(story.get('technical_requirements', []))
        return 0.0, "Unknown metric", "No suggestion available"

    def _check_title_quality(self, title: str) -> tuple[float, str, str]:
        words = title.split()
        if len(words) < 3:
            return 0.5, "Title too short", "Add more context to the title"
        if len(words) > 10:
            return 0.7, "Title too long", "Consider a more concise title"
        return 1.0, "", ""

    def _check_user_story_format(self, user_story: str) -> tuple[float, str, str]:
        required_parts = ["As a", "I want", "so that"]
        if not all(part in user_story for part in required_parts):
            return 0.0, "Invalid user story format", "Use format: 'As a X, I want Y, so that Z'"
        return 1.0, "", ""

    def _check_acceptance_criteria(self, criteria: List[str]) -> tuple[float, str, str]:
        if not criteria:
            return 0.0, "No acceptance criteria", "Add at least 2 acceptance criteria"
        if len(criteria) < 2:
            return 0.5, "Insufficient acceptance criteria", "Add more acceptance criteria"
        return 1.0, "", ""

    def _check_technical_requirements(self, requirements: List[str]) -> tuple[float, str, str]:
        if not requirements:
            return 0.0, "No technical requirements", "Add at least 1 technical requirement"
        return 1.0, "", ""