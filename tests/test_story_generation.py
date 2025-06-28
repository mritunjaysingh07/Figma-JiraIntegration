import json
import pytest
from unittest.mock import Mock, patch
from src.figma_client import FigmaClient, FigmaComponent
from src.ai_processor import AIProcessor, DesignAnalysis
from src.story_generator import StoryGenerator
from src.jira_client import JiraStory
import os
from dotenv import load_dotenv
from jira import JIRA
from src.quality.story_checker import StoryQualityChecker
from src.validators.models import FigmaElement, JiraStory as ValidatorJiraStory

@pytest.fixture
def sample_figma_data():
    with open("tests/sample_figma_data.json", "r") as f:
        return json.load(f)

@pytest.fixture
def mock_figma_client():
    return Mock(spec=FigmaClient)

@pytest.fixture
def mock_ai_processor():
    return Mock(spec=AIProcessor)

@pytest.fixture
def story_generator(mock_figma_client, mock_ai_processor):
    config = {
        "story_template": "As a {user_type}, I want to {action} so that {benefit}"
    }
    return StoryGenerator(mock_figma_client, mock_ai_processor, config)

@pytest.fixture
def sample_element():
    return FigmaElement(
        id="123",
        type="FRAME",
        name="Login Screen",
        description="User authentication interface"
    )

@pytest.fixture
def sample_story():
    return ValidatorJiraStory(
        title="Implement Secure Login Flow",
        user_story="As a user, I want to log in securely so that I can access my account",
        acceptance_criteria=["Valid credentials allow access", "Invalid credentials show error"],
        technical_requirements=["Implement JWT authentication"],
        story_points=3,
        priority="High"
    )

def test_generate_stories_from_components(story_generator, sample_figma_data):
    # Prepare test data
    components = [
        FigmaComponent(
            id="1:1",
            name="Message History",
            type="COMPONENT",
            description="Scrollable message history showing conversation",
            properties={"layout": "VERTICAL"}
        )
    ]
    
    # Mock AI analysis
    mock_analysis = DesignAnalysis(
        user_type="end user",
        action="view message history",
        benefit="I can review past conversations",
        priority="High",
        story_points=3,
        acceptance_criteria=["Messages are displayed in chronological order"],
        technical_notes=["Implement virtual scrolling for performance"]
    )
    
    story_generator.ai_processor.analyze_component.return_value = mock_analysis
    
    # Generate stories
    stories = story_generator.generate_stories(components)
    
    # Verify results
    assert len(stories) == 1
    story = stories[0]
    assert isinstance(story, JiraStory)
    assert story.summary == "Message History: view message history"
    assert story.priority == "High"
    assert story.story_points == 3
    assert "figma-generated" in story.labels

def test_group_related_stories(story_generator):
    # Create test stories
    stories = [
        JiraStory(
            summary="Story 1",
            description="Description 1",
            priority="High",
            story_points=3,
            acceptance_criteria=["Criterion 1"],
            labels=["figma-generated", "component-chat"]
        ),
        JiraStory(
            summary="Story 2",
            description="Description 2",
            priority="Medium",
            story_points=2,
            acceptance_criteria=["Criterion 2"],
            labels=["figma-generated", "component-settings"]
        )
    ]
    
    # Group stories
    groups = story_generator.group_related_stories(stories)
    
    # Verify grouping
    assert len(groups) == 2
    assert "component-chat" in groups
    assert "component-settings" in groups
    assert len(groups["component-chat"]) == 1
    assert len(groups["component-settings"]) == 1

def test_generate_epic(story_generator):
    # Create test stories
    stories = [
        JiraStory(
            summary="Implement chat interface",
            description="Description 1",
            priority="High",
            story_points=5,
            acceptance_criteria=["Criterion 1"],
            labels=["figma-generated"]
        ),
        JiraStory(
            summary="Add message input",
            description="Description 2",
            priority="Medium",
            story_points=3,
            acceptance_criteria=["Criterion 2"],
            labels=["figma-generated"]
        )
    ]
    
    # Mock AI response
    story_generator.ai_processor.generate_epic_summary.return_value = "Chat Interface Implementation"
    
    # Generate epic
    epic = story_generator.generate_epic(stories)
    
    # Verify epic
    assert epic["summary"] == "Chat Interface Implementation"
    assert "Implement chat interface" in epic["description"]
    assert "Add message input" in epic["description"]

def test_jira_connection():
    load_dotenv()
    
    # Connect to Jira
    jira = JIRA(
        server=os.getenv('JIRA_URL'),
        basic_auth=(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_API_TOKEN'))
    )
    
    # Test connection
    try:
        projects = jira.projects()
        print("Successfully connected to Jira!")
        print("Available projects:")
        for project in projects:
            print(f"- {project.key}: {project.name}")
    except Exception as e:
        print(f"Error connecting to Jira: {e}")

@pytest.mark.asyncio
async def test_story_generation(sample_element):
    ai_processor = AIProcessor("test-key", {"model": "test-model"})
    analysis = await ai_processor.analyze_element_with_context(
        sample_element.dict(),
        "User authentication system"
    )
    
    assert analysis.title is not None
    assert "As a" in analysis.user_story
    assert len(analysis.acceptance_criteria) >= 2

def test_story_quality(sample_story):
    checker = StoryQualityChecker()
    quality_report = checker.check_story_quality(sample_story)
    assert quality_report['passes_threshold']

if __name__ == "__main__":
    test_jira_connection()