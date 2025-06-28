from gitlab import Gitlab
import logging
from typing import Dict, Any, Optional
from src.config import Settings

logger = logging.getLogger(__name__)

class GitLabService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = Gitlab(
            url=settings.GITLAB_URL,
            private_token=settings.GITLAB_TOKEN
        )
        self.project = None
        if settings.GITLAB_PROJECT_ID:
            self.project = self.client.projects.get(settings.GITLAB_PROJECT_ID)

    def create_branch(self, branch_name: str, source_branch: Optional[str] = None) -> Dict[str, Any]:
        """Create a new branch in GitLab"""
        try:
            if not source_branch:
                source_branch = self.settings.DEFAULT_BRANCH
            
            branch = self.project.branches.create({
                'branch': branch_name,
                'ref': source_branch
            })
            
            return {
                'name': branch.name,
                'commit': branch.commit['id'],
                'web_url': f"{self.settings.GITLAB_URL}/{self.project.path_with_namespace}/-/tree/{branch.name}"
            }
        except Exception as e:
            logger.error(f"Error creating branch {branch_name}: {str(e)}")
            raise

    def create_merge_request(self, 
                           source_branch: str,
                           target_branch: str,
                           title: str,
                           description: str) -> Dict[str, Any]:
        """Create a new merge request in GitLab"""
        try:
            mr = self.project.mergerequests.create({
                'source_branch': source_branch,
                'target_branch': target_branch,
                'title': title,
                'description': description,
                'remove_source_branch': True,
                'squash': True
            })
            
            return {
                'id': mr.iid,
                'web_url': mr.web_url,
                'title': mr.title,
                'state': mr.state
            }
        except Exception as e:
            logger.error(f"Error creating merge request from {source_branch} to {target_branch}: {str(e)}")
            raise

    def scaffold_files(self, branch_name: str, files: Dict[str, str]) -> None:
        """Create or update files in a branch"""
        try:
            for file_path, content in files.items():
                self.project.files.create({
                    'file_path': file_path,
                    'branch': branch_name,
                    'content': content,
                    'commit_message': f"Add {file_path}"
                })
        except Exception as e:
            logger.error(f"Error scaffolding files in branch {branch_name}: {str(e)}")
            raise

    def get_branch(self, branch_name: str) -> Optional[Dict[str, Any]]:
        """Get branch details"""
        try:
            branch = self.project.branches.get(branch_name)
            return {
                'name': branch.name,
                'commit': branch.commit['id'],
                'protected': branch.protected
            }
        except Exception as e:
            logger.error(f"Error getting branch {branch_name}: {str(e)}")
            return None 