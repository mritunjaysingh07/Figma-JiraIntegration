import argparse
import json
import os
from typing import List, Dict, Optional
from src.config import load_config, config
from src.services.figma_service import FigmaService, extract_elements_from_figma
from src.services.jira_service import JiraService
from src.pdf_parser import PDFParser
from src.coverage.enhanced_coverage import EnhancedCoverageTracker
from src.quality.quality_checker import QualityChecker
from src.templates.template_manager import TemplateManager
from src.prompts.version_control import PromptManager
from src.ai_processor import AIProcessor
from loguru import logger
import sys


log_cfg = config.get("logging", {})
# Remove any existing handlers
logger.remove()

# Add console handler with INFO level
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)

# Add file handler with configured settings
logger.add(
    log_cfg.get("file", "app.log"),
    rotation=log_cfg.get("max_size", "10 MB"),
    retention=log_cfg.get("retention", "10 days"),
    level=log_cfg.get("level", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    enqueue=True
)

def extract_elements_from_pdf(pdf_path):
    parser = PDFParser()
    return parser.parse_pdf(pdf_path)

def extract_elements_from_figma(design_id):
    figma_service = FigmaService(config.get("figma", {}))
    return figma_service.fetch_design(design_id=design_id)

def extract_elements_from_json(json_filename):
    json_path = os.path.join("data", json_filename)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Recursively collect all elements of interest (FRAME, COMPONENT, etc.)
    def collect_elements(node):
        elements = []
        if isinstance(node, dict):
            if node.get("type") in ("FRAME", "COMPONENT"):
                elements.append(node)
            for child in node.get("children", []):
                elements.extend(collect_elements(child))
        elif isinstance(node, list):
            for item in node:
                elements.extend(collect_elements(item))
        return elements
    return collect_elements(data.get("document", {}))

def process_and_create_jira(elements, jira_project_key=None):
    """
    Process Figma elements and create Jira stories
    Args:
        elements: List of Figma elements
        jira_project_key: Optional Jira project key
    """
    try:
        # Initialize AI processor
        ai = AIProcessor(
            api_key=config.get('ai', {}).get('openai_api_key'),
            config=config
        )
        
        # Process elements and create Jira stories
        context = ai.analyze_application_context(elements)
        logger.info(f"Application context: {context}")
        
        # Analyze elements with context
        for element in elements:
            if not is_high_level_element(element):
                continue
            
            try:
                trimmed_element = trim_figma_element(element)
                analysis = ai.analyze_element_with_context(trimmed_element, context)
                logger.info(f"DEBUG: Creating Jira story with summary: '{analysis.title}'")
                extra_fields = {
                    "acceptance_criteria": analysis.acceptance_criteria,
                    "technical_requirements": analysis.technical_requirements,
                }
                jira.create_story(
                    summary=analysis.title,
                    description=analysis.user_story,
                    story_points=analysis.story_points,
                    extra_fields=extra_fields
                )
            except Exception as e:
                logger.error(f"Error processing element {element.get('name', 'unknown')}: {e}")
                continue
    except Exception as e:
        logger.error(f"Error in main processing: {e}")
        raise

#Use this function in case of toke issue only
def trim_figma_element(element):
    return {
        "id": element.get("id"),
        "name": element.get("name"),
        "type": element.get("type"),
        "description": element.get("description", ""),
        # Add more fields only if absolutely necessary
    }

def is_high_level_element(element):
    # Adjust these types as needed for your Figma data, adjust the figma element as per figma design Need
    return element.get('type') in ('FRAME', 'CANVAS', 'SCREEN', 'PAGE', 'FLOW', "TEXT","COMPONENT")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Figma to Jira Automation")
    parser.add_argument("--local", help="Path to PDF file", type=str)
    parser.add_argument("--api", help="Figma design (file) ID", type=str)
    parser.add_argument("--project", help="Jira project key", type=str)
    parser.add_argument("--config", help="Path to config file", type=str, default="config.yaml")
    parser.add_argument("--debug", help="Enable debug mode", action="store_true")
    args = parser.parse_args()

    # Load configuration
    load_config(args.config)
    
    # Initialize Jira service
    jira = JiraService(config.get('jira', {}))

    # Extract elements based on input type
    elements = None
    if args.local:
        elements = extract_elements_from_pdf(args.local)
    elif args.api:
        elements = extract_elements_from_figma(args.api)
    else:
        print("Error: Must provide either --local or --api")
        sys.exit(1)

    # Process and create Jira stories
    try:
        process_and_create_jira(elements, jira_project_key=args.project)
    except Exception as e:
        logger.error(f"Critical error in main execution: {e}")
        raise

    # Print element types if we have elements
    if elements:
        types = set(el.get('type') for el in elements)
        print("All Figma element types in this file:", types)
