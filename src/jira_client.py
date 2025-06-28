import re
from typing import Dict, List, Any
from jira import JIRA
from loguru import logger
from pydantic import BaseModel
from jira.exceptions import JIRAError

class JiraStory(BaseModel):
    """Represents a Jira story with all necessary fields"""
    summary: str
    description: str
    issue_type: str
    story_points: int
    acceptance_criteria: List[str]
    technical_requirements: List[str]  # Added field
    labels: List[str]
    components: List[str]
    design_link: str
    priority: str = "Medium"  # Added field with default
    business_value: str = ""  # Added field with default
    dependencies: List[str] = []  # Added field with default

    def to_jira_fields(self, project_key: str) -> Dict[str, Any]:
        """Convert to Jira API fields format"""
        fields = {
            'project': {'key': project_key},
            'summary': self.summary,
            'description': self.description,
            'issuetype': {'name': self.issue_type},
            'labels': self.labels
        }
        
        # Add acceptance criteria if present
        if self.acceptance_criteria:
            fields['description'] += "\n\nh2. Acceptance Criteria\n" + "\n".join(f"* {ac}" for ac in self.acceptance_criteria)
        
        return fields

    def to_dict(self) -> Dict:
        """Convert the story to a dictionary for JSON serialization"""
        return {
            'summary': self.summary,
            'description': self.description,
            'issue_type': self.issue_type,
            'story_points': self.story_points,
            'acceptance_criteria': self.acceptance_criteria,
            'technical_requirements': self.technical_requirements,
            'labels': self.labels,
            'components': self.components,
            'design_link': self.design_link,
            'priority': self.priority,
            'business_value': self.business_value,
            'dependencies': self.dependencies
        }

class JiraClient:
    """Client for interacting with Jira"""
    
    # Standard Jira issue type mappings
    ISSUE_TYPE_MAPPINGS = {
        'Feature': ['Feature', 'Story', 'New Feature'],
        'Enhancement': ['Enhancement', 'Improvement', 'Story'],
        'Technical': ['Technical Task', 'Task', 'Story'],
        'UI Component': ['Story', 'Sub-task', 'Task'],
        'Integration': ['Story', 'Task'],
        'Story': ['Story', 'Task'],  # Fallback mapping
        'Epic': ['Epic']  # Add Epic mapping
    }
    
    def __init__(self, url: str, email: str, api_token: str, config: Dict):
        """
        Initialize Jira client
        
        Args:
            url: Jira instance URL (with or without https://)
            email: Jira account email
            api_token: Jira API token
            config: Configuration dictionary
        """
        # Clean up URL if it includes protocol
        self.url = self._clean_url(url)
        self.email = email
        self.config = config
        
        # Initialize Jira client
        try:
            self.jira = JIRA(
                server=f"https://{self.url}",
                basic_auth=(email, api_token)
            )
            
            # Validate project exists
            try:
                self.project = self.jira.project(self.config['project_key'])
                logger.info(f"Connected to Jira project: {self.project.name} ({self.project.key})")
                
                # Cache available issue types for the project
                self.available_issue_types = self._get_available_issue_types()
                logger.info(f"Available issue types: {', '.join(self.available_issue_types.keys())}")
                
                # Get available fields for the project
                self.available_fields = self._get_available_fields()
                logger.info(f"Available fields retrieved for project {self.project.key}")
                
            except Exception as e:
                logger.error(f"Project {self.config['project_key']} not found or not accessible: {e}")
                raise ValueError(f"Project {self.config['project_key']} not found or not accessible. Please check your project key and permissions.")
                
            logger.info("Initialized Jira client")
        except Exception as e:
            logger.error(f"Failed to initialize Jira client: {e}")
            raise

    def _clean_url(self, url: str) -> str:
        """Remove protocol and trailing slashes from URL"""
        # Remove protocol if present
        url = re.sub(r'^https?://', '', url)
        # Remove trailing slashes
        url = url.rstrip('/')
        return url

    def _get_available_issue_types(self) -> Dict[str, Dict]:
        """Get available issue types for the project"""
        try:
            issue_types = {}
            for issue_type in self.project.issueTypes:
                issue_types[issue_type.name] = {
                    'id': issue_type.id,
                    'name': issue_type.name,
                    'subtask': issue_type.subtask
                }
            return issue_types
        except Exception as e:
            logger.error(f"Error getting issue types: {e}")
            return {}

    def _get_available_fields(self) -> Dict[str, Dict]:
        """Get available fields for the project"""
        try:
            fields = {}
            for field in self.jira.fields():
                fields[field['name'].lower()] = {
                    'id': field['id'],
                    'name': field['name'],
                    'custom': field.get('custom', False),
                    'schema': field.get('schema', {})
                }
            return fields
        except Exception as e:
            logger.error(f"Error getting available fields: {e}")
            return {}

    def _map_issue_type(self, requested_type: str) -> str:
        """Map requested issue type to available project issue type"""
        # First, try exact match
        if requested_type in self.available_issue_types:
            return requested_type
            
        # Try standard mappings
        if requested_type in self.ISSUE_TYPE_MAPPINGS:
            for mapped_type in self.ISSUE_TYPE_MAPPINGS[requested_type]:
                if mapped_type in self.available_issue_types:
                    logger.info(f"Mapped issue type '{requested_type}' to '{mapped_type}'")
                    return mapped_type
        
        # Fallback to Story or Task
        for fallback in ['Story', 'Task']:
            if fallback in self.available_issue_types:
                logger.warning(f"Using fallback issue type '{fallback}' for '{requested_type}'")
                return fallback
                
        raise ValueError(f"No valid issue type found for '{requested_type}'. Available types: {list(self.available_issue_types.keys())}")

    def create_story(self, story: JiraStory) -> Any:
        """
        Create a Jira story from the provided story data
        
        Args:
            story: Story data to create in Jira
            
        Returns:
            Created Jira issue
        """
        try:
            # Validate project exists
            if not hasattr(self, 'project'):
                raise ValueError(f"Project {self.config['project_key']} not initialized. Please check your configuration.")
            
            # Map issue type to valid project issue type
            mapped_issue_type = self._map_issue_type(story.issue_type)
            
            # Convert story to Jira fields format
            fields = story.to_jira_fields(self.config['project_key'])
            fields['issuetype'] = {'name': mapped_issue_type}
            
            # Add custom fields if configured and available
            if 'story_points' in self.config['fields'] and story.story_points:
                field_id = self.config['fields']['story_points']
                if self._is_field_available(field_id):
                    fields[field_id] = float(story.story_points)
            
            if 'design_link' in self.config['fields'] and story.design_link:
                field_id = self.config['fields']['design_link']
                if self._is_field_available(field_id):
                    fields[field_id] = story.design_link

            # Create the issue
            issue = self.jira.create_issue(fields=fields)
            logger.info(f"Created Jira story: {issue.key} - {story.summary}")
            return issue
            
        except JIRAError as e:
            error_msg = f"Failed to create Jira story: {e.text}"
            if e.status_code == 400:
                error_details = e.response.json()
                if 'errors' in error_details:
                    error_msg += f"\nErrors: {error_details['errors']}"
                if 'errorMessages' in error_details:
                    error_msg += f"\nMessages: {error_details['errorMessages']}"
            logger.error(error_msg)
            raise
        except Exception as e:
            logger.error(f"Error creating Jira story: {str(e)}")
            raise

    def _is_field_available(self, field_id: str) -> bool:
        """Check if a field is available in the project"""
        try:
            # Check if field exists in available fields
            return any(field['id'] == field_id for field in self.available_fields.values())
        except Exception as e:
            logger.warning(f"Error checking field availability for {field_id}: {e}")
            return False

    def update_story(self, key: str, story: Dict[str, Any]) -> Any:
        """
        Update an existing story in Jira
        
        Args:
            key: Issue key to update
            story: Dictionary containing story fields to update
            
        Returns:
            Updated issue object
        """
        try:
            issue = self.jira.issue(key)
            issue.update(fields=story)
            logger.info(f"Updated Jira story: {key}")
            return issue
        except Exception as e:
            logger.error(f"Failed to update Jira story: {e}")
            raise

    def search_issues(self, jql: str) -> List[Any]:
        """
        Search for issues using JQL
        
        Args:
            jql: JQL query string
            
        Returns:
            List of matching issues
        """
        try:
            issues = self.jira.search_issues(jql)
            logger.debug(f"Found {len(issues)} issues matching query: {jql}")
            return issues
        except Exception as e:
            logger.error(f"Failed to search issues: {e}")
            raise

    def create_epic(self, summary: str, description: str) -> Any:
        """
        Create a new epic in Jira
        
        Args:
            summary: Epic summary
            description: Epic description
            
        Returns:
            Created Jira epic
        """
        try:
            # Map epic type
            epic_type = self._map_issue_type('Epic')
            
            fields = {
                'project': {'key': self.config['project_key']},
                'summary': summary,
                'description': description,
                'issuetype': {'name': epic_type}
            }
            
            # Add epic name if the field is configured
            if 'epic_name' in self.config['fields']:
                field_id = self.config['fields']['epic_name']
                if self._is_field_available(field_id):
                    fields[field_id] = summary
            
            epic = self.jira.create_issue(fields=fields)
            logger.info(f"Created Jira epic: {epic.key} - {summary}")
            
            return epic
            
        except Exception as e:
            logger.error(f"Error creating Jira epic: {e}")
            raise

    def _get_epic_link_field(self) -> str:
        """Get the correct epic link field ID by checking available fields"""
        try:
            # First try to get from config
            epic_link_field = self.config['fields'].get('epic_link')
            
            # If not in config, try to find it from available fields
            if not epic_link_field:
                for field in self.jira.fields():
                    if field['name'].lower() in ['epic link', 'epic_link']:
                        epic_link_field = field['id']
                        break
            
            # If still not found, try common default values
            if not epic_link_field:
                common_fields = ['customfield_10014', 'customfield_10000']
                for field_id in common_fields:
                    try:
                        field = self.jira.field(field_id)
                        if field and field['name'].lower() in ['epic link', 'epic_link']:
                            epic_link_field = field_id
                            break
                    except:
                        continue
            
            if not epic_link_field:
                raise ValueError("Could not find Epic Link field. Please configure it manually.")
                
            logger.info(f"Using Epic Link field: {epic_link_field}")
            return epic_link_field
            
        except Exception as e:
            logger.error(f"Error finding Epic Link field: {e}")
            raise

    def link_to_epic(self, issue_key: str, epic_key: str) -> None:
        """
        Link an issue to an epic
        
        Args:
            issue_key: The issue to link
            epic_key: The epic to link to
        """
        try:
            # Get the epic link field ID
            epic_link_field = self._get_epic_link_field()
            
            # Try direct field update first
            try:
                issue = self.jira.issue(issue_key)
                issue.update(fields={epic_link_field: epic_key})
                logger.info(f"Linked {issue_key} to epic {epic_key} using field update")
                return
            except Exception as e:
                logger.warning(f"Could not link using field update: {e}")
            
            # Try alternative method using issue link
            try:
                self.jira.create_issue_link(
                    type="Relates",
                    inwardIssue=issue_key,
                    outwardIssue=epic_key
                )
                logger.info(f"Linked {issue_key} to epic {epic_key} using issue link")
                return
            except Exception as e:
                logger.warning(f"Could not create issue link: {e}")
            
            raise Exception("All linking methods failed")
            
        except Exception as e:
            logger.error(f"Error linking {issue_key} to epic {epic_key}: {e}")
            # Log more details about the error
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                logger.error(f"Error details: {e.response.text}")
            raise

    def create_epic_with_stories(self, epic_data: Dict) -> Any:
        """
        Create an epic and link its stories
        
        Args:
            epic_data: Dictionary containing epic details and stories
            
        Returns:
            Created epic
        """
        try:
            # Create the epic
            epic = self.create_epic(epic_data['summary'], epic_data['description'])
            logger.info(f"Created epic: {epic.key}")
            
            # Create and link stories if present
            if 'stories' in epic_data and epic_data['stories']:
                for story in epic_data['stories']:
                    try:
                        # Create the story
                        issue = self.create_story(story)
                        logger.info(f"Created story: {issue.key}")
                        
                        # Try to link story to epic
                        try:
                            self.link_to_epic(issue.key, epic.key)
                        except Exception as e:
                            logger.error(f"Failed to link story {issue.key} to epic {epic.key}: {e}")
                            # Continue with other stories even if linking fails
                            continue
                            
                    except Exception as e:
                        logger.error(f"Error processing story for epic {epic.key}: {e}")
                        continue
            
            return epic
            
        except Exception as e:
            logger.error(f"Error creating epic with stories: {e}")
            raise

    def process_epics_and_stories(self, epics: List[Dict]) -> List[Any]:
        """
        Process and create all epics with their stories
        
        Args:
            epics: List of epic data dictionaries
            
        Returns:
            List of created epics
        """
        created_epics = []
        
        for epic_data in epics:
            try:
                epic = self.create_epic_with_stories(epic_data)
                created_epics.append(epic)
                logger.info(f"Successfully created epic {epic.key} with its stories")
            except Exception as e:
                logger.error(f"Error processing epic {epic_data.get('summary', 'Unknown')}: {e}")
                continue
        
        return created_epics

    def link_issues(self, from_issue: str, to_issue: str, link_type: str = "Relates") -> None:
        """
        Create a link between two issues
        
        Args:
            from_issue: Source issue key
            to_issue: Target issue key
            link_type: Type of link to create
        """
        try:
            self.jira.create_issue_link(
                type=link_type,
                inwardIssue=from_issue,
                outwardIssue=to_issue
            )
            logger.info(f"Created link between {from_issue} and {to_issue}")
            
        except Exception as e:
            logger.error(f"Error linking issues: {e}")
            raise

    def add_comment(self, issue_key: str, comment: str) -> None:
        """
        Add a comment to an issue
        
        Args:
            issue_key: The issue to comment on
            comment: The comment text
        """
        try:
            self.jira.add_comment(issue_key, comment)
            logger.info(f"Added comment to {issue_key}")
            
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            raise

    def delete_all_project_issues(self) -> None:
        """Delete all issues from the configured project"""
        try:
            # Search for all issues in the project
            jql = f'project = {self.config["project_key"]}'
            issues = self.jira.search_issues(jql, maxResults=1000)
            
            if not issues:
                logger.info(f"No issues found in project {self.config['project_key']}")
                return
                
            logger.info(f"Found {len(issues)} issues to delete")
            
            # Delete each issue
            for issue in issues:
                try:
                    self.delete_issue(issue.key)
                    logger.info(f"Deleted issue: {issue.key}")
                except Exception as e:
                    logger.error(f"Error deleting issue {issue.key}: {e}")
                    continue
            
            logger.info("Finished deleting issues")
            
        except Exception as e:
            logger.error(f"Error deleting project issues: {e}")
            raise

    def delete_issue(self, issue_key: str) -> None:
        """
        Delete an issue from Jira
        
        Args:
            issue_key: The key of the issue to delete
        """
        try:
            issue = self.jira.issue(issue_key)
            issue.delete()
            logger.info(f"Deleted issue: {issue_key}")
        except Exception as e:
            logger.error(f"Failed to delete issue {issue_key}: {e}")
            raise 