from pydantic_settings import BaseSettings
from typing import Optional
import yaml
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Jira settings
    JIRA_URL: str
    JIRA_EMAIL: str
    JIRA_API_TOKEN: str
    
    # # GitLab settings
    # GITLAB_URL: str
    # GITLAB_TOKEN: str
    # GITLAB_PROJECT_ID: Optional[int] = None
    
    # # Webhook settings
    # WEBHOOK_SECRET: str
    
    # # Application settings
    # DEFAULT_BRANCH: str = "main"
    # BRANCH_PREFIX: str = "feature"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

def load_config(config_path: str = "config.yaml"):
    config_path = os.path.join(os.path.dirname(__file__), config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()