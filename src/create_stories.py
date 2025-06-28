import os
from dotenv import load_dotenv
import yaml
from loguru import logger
from figma_client import FigmaClient
from jira_client import JiraClient
from ai_processor import AIProcessor
from story_generator import StoryGenerator
from coverage.enhanced_coverage import EnhancedCoverageTracker

def setup_logging():
    """Configure logging"""
    logger.add(
        "app.log",
        rotation="10 MB",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )

def load_config():
    """Load configuration from config.yaml"""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def find_figma_file(figma_client, file_name="Digital Assistant"):
    """Find Figma file by name"""
    try:
        # Get user's files
        response = figma_client._make_request("GET", "me/files/recent")
        files = response.get("files", [])
        
        print("\nAvailable Figma Files:")
        for file in files:
            print(f"- {file['name']} (ID: {file['key']})")
            if file["name"].lower() == file_name.lower():
                return file["key"]
        return None
    except Exception as e:
        logger.error(f"Error finding Figma file: {e}")
        return None

def find_jira_project(jira_client, project_name="Digital Assistant"):
    """Find Jira project by name"""
    try:
        projects = jira_client.jira.projects()
        print("\nAvailable Jira Projects:")
        for project in projects:
            print(f"- {project.key}: {project.name}")
            if project.name.lower() == project_name.lower():
                return project.key
        return None
    except Exception as e:
        logger.error(f"Error finding Jira project: {e}")
        return None

def process_and_create_jira(figma_client: FigmaClient, jira_client: JiraClient, 
                           story_generator: StoryGenerator, config: Dict, 
                           figma_file_key: str, jira_project_key: str) -> Tuple[List[FigmaElement], List[JiraStory]]:
    # Process design and create stories
    figma_elements = story_generator.process_design(figma_client, figma_file_key)
    jira_stories = []
    
    # Create Jira stories
    for element in figma_elements:
        try:
            story = story_generator.generate_story(element)
            if story:
                jira_client.create_story(story, jira_project_key)
                jira_stories.append(story)
        except Exception as e:
            logger.error(f"Error processing element {element.get('name', 'Unknown')}: {str(e)}")
    
    return figma_elements, jira_stories

def main():
    # Load environment variables and config
    load_dotenv()
    config = load_config()
    setup_logging()
    
    try:
        # Initialize Figma client
        figma_client = FigmaClient(
            access_token=os.getenv("FIGMA_ACCESS_TOKEN"),
            config=config["figma"]
        )
        
        # Validate Figma access
        if not figma_client.validate_access_token():
            logger.error("Invalid Figma access token")
            return
        
        # Find Figma file
        file_id = os.getenv("FIGMA_FILE_ID")
        if not file_id:
            print("\nLooking for Digital Assistant Figma file...")
            file_id = find_figma_file(figma_client)
            if not file_id:
                print("❌ Could not find Digital Assistant Figma file")
                return
        
        # Initialize Jira client
        jira_client = JiraClient(
            url=os.getenv("JIRA_URL"),
            email=os.getenv("JIRA_EMAIL"),
            api_token=os.getenv("JIRA_API_TOKEN"),
            config=config["jira"]
        )
        
        # Find Jira project
        project_key = find_jira_project(jira_client)
        if not project_key:
            print("❌ Could not find Digital Assistant Jira project")
            return
        
        # Update config with project key
        config["jira"]["project_key"] = project_key
        
        # Initialize AI processor
        ai_processor = AIProcessor(
            api_key=os.getenv("OPENAI_API_KEY"),
            config=config["ai"]
        )
        
        # Initialize story generator
        story_generator = StoryGenerator(
            figma_client=figma_client,
            ai_processor=ai_processor,
            config=config["story"]
        )
        
        # Initialize coverage tracker
        coverage_tracker = EnhancedCoverageTracker()
        
        # Process and create stories
        figma_elements, jira_stories = process_and_create_jira(figma_client, jira_client, story_generator, config, file_id, project_key)
        
        # Analyze coverage
        coverage_report = coverage_tracker.analyze_coverage(figma_elements, jira_stories)
        logger.info(f"Coverage Report: {coverage_report}")
        
        # Get coverage trends
        trends = coverage_tracker.get_coverage_trends()
        logger.info(f"Coverage Trends: {trends}")
        
    except Exception as e:
        logger.exception(f"Error processing Figma file: {e}")
        raise

if __name__ == "__main__":
    main()