import os
import pytest
from dotenv import load_dotenv
import yaml
from jira import JIRA, JIRAError
from src.jira_client import JiraClient

# Load environment variables and config before tests
load_dotenv()
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

def get_available_fields(jira_client):
    """Get all available custom fields and their IDs"""
    fields = jira_client.jira.fields()
    field_map = {}
    print("\nAvailable Custom Fields:")
    for field in fields:
        if field.get('custom'):
            print(f"- {field['name']} (ID: {field['id']})")
            field_map[field['name'].lower()] = field['id']
    return field_map

@pytest.fixture
def jira_client():
    """Create a Jira client instance for testing"""
    return JiraClient(
        url=os.getenv("JIRA_URL"),
        email=os.getenv("JIRA_EMAIL"),
        api_token=os.getenv("JIRA_API_TOKEN"),
        config=config["jira"]
    )

def test_jira_auth(jira_client):
    """Test Jira authentication"""
    try:
        # Attempt to get current user info
        user = jira_client.jira.myself()
        assert user["emailAddress"] == os.getenv("JIRA_EMAIL"), "Email mismatch in Jira authentication"
        print(f"✅ Successfully authenticated with Jira as {user['displayName']}")
    except JIRAError as e:
        pytest.fail(f"Failed to authenticate with Jira: {str(e)}")

def find_project_key(jira_client, project_name="Digital Assistant"):
    """Find the project key for a given project name"""
    try:
        projects = jira_client.jira.projects()
        print("\nAvailable Projects:")
        for project in projects:
            print(f"- {project.key}: {project.name}")
            if project.name.lower() == project_name.lower():
                return project.key
        return None
    except JIRAError as e:
        print(f"Error getting projects: {str(e)}")
        return None

def test_project_access(jira_client):
    """Test access to Digital Assistant project"""
    try:
        # First, get all projects and find the correct key
        project_key = find_project_key(jira_client)
        if not project_key:
            pytest.skip("Could not find Digital Assistant project. Please check project name.")
        
        project = jira_client.jira.project(project_key)
        assert project.name.lower() == "digital assistant".lower(), f"Project name mismatch: {project.name}"
        print(f"\n✅ Successfully accessed Digital Assistant project")
        print(f"Project Information:")
        print(f"- Key: {project.key}")
        print(f"- Name: {project.name}")
        print(f"- Lead: {project.lead.displayName}")
        
        # Update config with correct project key
        config["jira"]["project_key"] = project_key
        
    except JIRAError as e:
        pytest.fail(f"Failed to access project: {str(e)}")

def test_issue_types(jira_client):
    """Test available issue types in the project"""
    try:
        issue_types = jira_client.jira.issue_types()
        story_type = next((t for t in issue_types if t.name == "Story"), None)
        assert story_type is not None, "Story issue type not found"
        print("\n✅ Available issue types:")
        for issue_type in issue_types:
            print(f"- {issue_type.name}")
    except JIRAError as e:
        pytest.fail(f"Failed to get issue types: {str(e)}")

def test_custom_fields(jira_client):
    """Test and identify available custom fields"""
    try:
        # Get all available fields
        field_map = get_available_fields(jira_client)
        
        # Look for Story Points field (try common names)
        story_points_id = None
        for name in ['story points', 'story point estimate', 'points']:
            if name in field_map:
                story_points_id = field_map[name]
                break
        
        if story_points_id:
            print(f"\n✅ Found Story Points field: {story_points_id}")
            config["jira"]["fields"]["story_points"] = story_points_id
        else:
            print("\n⚠️ Story Points field not found. Please configure it in Jira.")
        
        # Update config to remove design_link field as it's not available
        if "design_link" in config["jira"]["fields"]:
            del config["jira"]["fields"]["design_link"]
            
    except JIRAError as e:
        pytest.fail(f"Failed to verify custom fields: {str(e)}")

def test_create_test_issue(jira_client):
    """Test creating and deleting a test issue"""
    try:
        # Get correct project key
        project_key = find_project_key(jira_client)
        if not project_key:
            pytest.skip("Could not find Digital Assistant project")
        
        # Create test issue with only available fields
        issue_dict = {
            "project": {"key": project_key},
            "summary": "Test Issue - Please Delete",
            "description": "This is a test issue created by the automated test suite.",
            "issuetype": {"name": "Story"},
            "labels": ["test-automation"]
        }
        
        # Add story points if available
        if "story_points" in config["jira"]["fields"]:
            issue_dict[config["jira"]["fields"]["story_points"]] = 1
        
        issue = jira_client.jira.create_issue(fields=issue_dict)
        print(f"\n✅ Successfully created test issue: {issue.key}")
        
        # Delete test issue
        issue.delete()
        print(f"✅ Successfully deleted test issue")
    except JIRAError as e:
        pytest.fail(f"Failed to create/delete test issue: {str(e)}")

if __name__ == "__main__":
    # Manual test execution
    print("Testing Jira Connection...")
    load_dotenv()
    
    try:
        client = JiraClient(
            url=os.getenv("JIRA_URL"),
            email=os.getenv("JIRA_EMAIL"),
            api_token=os.getenv("JIRA_API_TOKEN"),
            config=config["jira"]
        )
        
        # Test authentication
        user = client.jira.myself()
        print(f"\n✅ Successfully authenticated with Jira as {user['displayName']}")
        
        # Get all projects and find Digital Assistant
        project_key = find_project_key(client)
        if not project_key:
            print("\n❌ Could not find Digital Assistant project")
            print("Please check the project name or your permissions")
            exit(1)
            
        # Test project access
        project = client.jira.project(project_key)
        print(f"\nProject Information:")
        print(f"Name: {project.name}")
        print(f"Key: {project.key}")
        print(f"Lead: {project.lead.displayName}")
        
        # Update config with correct project key
        config["jira"]["project_key"] = project_key
        
        # Get available custom fields
        field_map = get_available_fields(client)
        
        # Create and delete test issue
        issue_dict = {
            "project": {"key": project_key},
            "summary": "Test Issue - Please Delete",
            "description": "This is a test issue created by the automated test suite.",
            "issuetype": {"name": "Story"},
            "labels": ["test-automation"]
        }
        
        # Add story points if available
        if "story_points" in config["jira"]["fields"]:
            issue_dict[config["jira"]["fields"]["story_points"]] = 1
        
        issue = client.jira.create_issue(fields=issue_dict)
        print(f"\n✅ Created test issue: {issue.key}")
        issue.delete()
        print("✅ Deleted test issue")
        
        print("\n✅ All Jira tests completed successfully")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        exit(1) 