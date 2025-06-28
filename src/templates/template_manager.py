import yaml
from pathlib import Path
from typing import Dict, Any
from loguru import logger

class TemplateManager:
    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict:
        template_path = Path(__file__).parent / "story_templates.yaml"
        with open(template_path, 'r') as f:
            return yaml.safe_load(f)['templates']

    def get_template(self, element_type: str) -> Dict[str, Any]:
        template = self.templates.get(element_type, self.templates.get('DEFAULT'))
        if not template:
            logger.warning(f"No template found for type {element_type}, using basic template")
            template = self._get_basic_template()
        return template

    def _get_basic_template(self) -> Dict[str, Any]:
        return {
            "title_format": "{type}: {name}",
            "user_story_format": "As a user, I want to {action} so that {benefit}",
            "required_sections": ["acceptance_criteria"],
            "story_points_range": [1, 5],
            "default_priority": "Medium"
        }

    def format_story(self, element_type: str, **kwargs) -> Dict[str, str]:
        template = self.get_template(element_type)
        return {
            'title': template['title_format'].format(**kwargs),
            'user_story': template['user_story_format'].format(**kwargs),
            'required_sections': template['required_sections'],
            'story_points_range': template['story_points_range'],
            'default_priority': template['default_priority']
        }