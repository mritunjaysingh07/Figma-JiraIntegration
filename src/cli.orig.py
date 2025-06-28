import argparse
import json
import os
from src.config import config
from src.services.figma_service import FigmaService
from src.pdf_parser import PDFParser
from src.services.jira_service import JiraService
from src.ai_processor import AIProcessor
from loguru import logger

log_cfg = config.get("logging", {})
logger.add(
    log_cfg.get("file", "app.log"),
    rotation=log_cfg.get("max_size", "10 MB"),
    retention=log_cfg.get("backup_count", 3),
    enqueue=True,
    level="INFO"
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
    ai_cfg = config.get("ai", {})
    openai_key = config.get("openai_api_key") or ai_cfg.get("openai_api_key")
    ai = AIProcessor(api_key=openai_key, config=ai_cfg)
    jira_cfg = config["jira"].copy()
    if jira_project_key:
        jira_cfg["project_key"] = jira_project_key
    jira = JiraService(jira_cfg)

    # Filter for high-level elements only
    '''If your Figma data uses different types for screens/flows, adjust the tuple 
    in is_high_level_element accordingly.'''
    high_level_elements = [el for el in elements if is_high_level_element(el)]

    # 1. Analyze application context
    context = ai.analyze_application_context(high_level_elements)
    print("Application context:", context)

    # 2. Analyze each high-level element for stories (with context)
    
    analyses = []
    for element in high_level_elements:  # Limit to first 100 elements for token issue else pass all
        trimmed_element = trim_figma_element(element)
        analysis = ai.analyze_element_with_context(trimmed_element, context)
        analyses.append(analysis)
        print(f"DEBUG: Parsed analysis: title='{analysis.title}', user_story='{analysis.user_story}'")

    # 3. Group stories into epics and generate epic summaries (optional, for planning/reporting)
    epic_summaries = ai.generate_epic_summary(analyses, context)
    print("Epic Summaries:\n", epic_summaries)

    # 4. Create Jira stories (after grouping/summarizing)
    for analysis in analyses:
        print(f"DEBUG: Creating Jira story with summary: '{analysis.title}'")
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
    parser.add_argument("--project", help="Jira project key (overrides config)", type=str)
    parser.add_argument("--webhook", action="store_true", help="Run as webhook server")
    parser.add_argument("--json", help="Figma JSON filename in data folder", type=str)
    args = parser.parse_args()

    if args.webhook:
        from src.main import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    elif args.local:
        elements = extract_elements_from_pdf(args.local)
        types = set(el.get('type') for el in elements)
        print("All Figma element types in this file:", types)
        process_and_create_jira(elements, jira_project_key=args.project)
    elif args.api:
        elements = extract_elements_from_figma(args.api)
        types = set(el.get('type') for el in elements)
        print("All Figma element types in this file:", types)
        process_and_create_jira(elements, jira_project_key=args.project)
    elif args.json:
        elements = extract_elements_from_json(args.json)
        types = set(el.get('type') for el in elements)
        print("All Figma element types in this JSON file:", types)
        process_and_create_jira(elements, jira_project_key=args.project)
    else:
        parser.print_help()
