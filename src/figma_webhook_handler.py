import json
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from loguru import logger
from figma_client import FigmaClient
from story_generator import StoryGenerator
from jira_client import JiraClient

app = FastAPI()

class FigmaWebhookHandler:
    def __init__(self, figma_client: FigmaClient, story_generator: StoryGenerator, jira_client: JiraClient):
        self.figma_client = figma_client
        self.story_generator = story_generator
        self.jira_client = jira_client

    async def process_file_update(self, file_id: str) -> Dict[str, Any]:
        """Process a Figma file update and update Jira stories"""
        try:
            # Validate file access
            file_info = self.figma_client.get_file_info(file_id)
            logger.info(f"Processing updates for file: {file_info['name']}")
            
            # Get updated components
            components = self.figma_client.get_file_components(file_id)
            
            # Generate new stories
            stories = self.story_generator.generate_stories(components)
            
            # Update or create Jira issues
            results = []
            for story in stories:
                # Check if story already exists (by component name)
                existing_issues = self.jira_client.search_issues(
                    f'project = {self.jira_client.config["project_key"]} AND labels = component-{story.labels[1]}'
                )
                
                if existing_issues:
                    # Update existing issue
                    issue = existing_issues[0]
                    self.jira_client.update_story(issue.key, story)
                    results.append({
                        "status": "updated",
                        "key": issue.key,
                        "summary": story.summary
                    })
                else:
                    # Create new issue
                    issue = self.jira_client.create_story(story)
                    results.append({
                        "status": "created",
                        "key": issue.key,
                        "summary": story.summary
                    })
            
            return {
                "status": "success",
                "file_id": file_id,
                "file_name": file_info["name"],
                "stories_processed": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error processing file update: {e}")
            raise HTTPException(status_code=500, detail=str(e))

webhook_handler = None

@app.post("/webhook/figma/{file_id}")
async def figma_webhook(
    request: Request,
    file_id: str
):
    """Handle Figma file update requests"""
    if not webhook_handler:
        raise HTTPException(status_code=500, detail="Webhook handler not initialized")
    
    return await webhook_handler.process_file_update(file_id)

def init_webhook_handler(
    figma_client: FigmaClient,
    story_generator: StoryGenerator,
    jira_client: JiraClient
):
    """Initialize the webhook handler with required clients"""
    global webhook_handler
    webhook_handler = FigmaWebhookHandler(figma_client, story_generator, jira_client) 