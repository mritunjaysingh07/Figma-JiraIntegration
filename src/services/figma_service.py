import requests
from loguru import logger
from src.pdf_parser import PDFParser
from typing import List, Dict
from src.config import load_config

class FigmaService:
    def __init__(self, config):
        self.config = config
        self.pdf_parser = PDFParser()
        self.access_token = config.get("access_token")
        # If components_to_analyze is not set, analyze all types
        self.components_to_analyze = set(config.get("components_to_analyze", []))

    def fetch_design(self, design_id=None, pdf_path=None):
        """
        Try to fetch design from Figma API, fallback to PDF if not available.
        """
        if design_id:
            if not self.access_token:
                raise Exception("Figma access token not provided in config.")
            headers = {"X-Figma-Token": self.access_token}
            url = f"https://api.figma.com/v1/files/{design_id}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                logger.info("Fetched Figma design successfully.")
                data = response.json()
                return self._extract_elements(data)
            else:
                logger.error(f"Figma API error: {response.status_code} {response.text}")
                raise Exception(f"Figma API error: {response.status_code} {response.text}")
        if pdf_path:
            logger.info(f"Falling back to PDF parsing: {pdf_path}")
            return self.pdf_parser.parse_pdf(pdf_path)
        raise Exception("No design source available (Figma or PDF)")

    def _extract_elements(self, data):
        elements = []
        def walk(node):
            node_type = node.get("type")
            # If no filter, include all types
            if not self.components_to_analyze or node_type in self.components_to_analyze:
                elements.append({
                    "id": node.get("id"),
                    "name": node.get("name"),
                    "type": node_type,
                    "description": node.get("description", ""),
                    "properties": {},
                    "children": node.get("children", [])
                })
            for child in node.get("children", []):
                walk(child)
        walk(data["document"])
        return elements

def extract_elements_from_figma(file_id: str) -> List[Dict]:
    """Extract design elements from Figma file"""
    try:
        config = load_config()
        figma_token = config.get("figma", {}).get("access_token")
        
        if not figma_token:
            logger.warning("Figma token not found, using mock data for testing")
            return _get_mock_elements()

        # Use existing FigmaService class
        figma = FigmaService(figma_token)
        file_data = figma.get_file(file_id)
        return _process_figma_document(file_data.get("document", {}))

    except Exception as e:
        logger.error(f"Error extracting elements from Figma: {e}")
        raise