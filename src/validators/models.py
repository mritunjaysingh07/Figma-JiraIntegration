from typing import Dict, List, Optional
from pydantic import BaseModel, validator, Field

class FigmaElement(BaseModel):
    id: str
    type: str
    name: str
    description: Optional[str] = ""
    properties: Dict = {}
    children: List['FigmaElement'] = []

    @validator('type')
    def validate_type(cls, v):
        allowed_types = {'FRAME', 'COMPONENT', 'SCREEN', 'FLOW', 'PAGE'}
        if v not in allowed_types:
            raise ValueError(f'Invalid element type. Must be one of: {allowed_types}')
        return v

class JiraStory(BaseModel):
    title: str = Field(min_length=10, max_length=255)
    user_story: str
    acceptance_criteria: List[str] = Field(min_items=2)
    technical_requirements: List[str] = Field(min_items=1)
    story_points: int = Field(ge=1, le=8)
    priority: str