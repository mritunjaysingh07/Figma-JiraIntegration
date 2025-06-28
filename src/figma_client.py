from typing import Dict, List, Any
import requests
from loguru import logger
from pydantic import BaseModel

class FigmaAPIError(Exception):
    """Custom exception for Figma API errors"""
    def __init__(self, message: str, status_code: int = None, response: Dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

class FigmaClient:
    """Client for interacting with Figma API"""

    def __init__(self, access_token: str, file_key: str, config: Dict):
        """
        Initialize Figma client

        Args:
            access_token: Figma access token
            file_key: Figma file key to process
            config: Configuration dictionary (should include 'components_to_analyze')
        """
        self.access_token = access_token
        self.file_key = file_key
        self.config = config
        self.base_url = "https://api.figma.com/v1"
        self.headers = {
            "X-Figma-Token": access_token
        }

    def _make_request(self, method: str, endpoint: str) -> Dict:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"Figma API error: {e} - {response.text}")
            raise FigmaAPIError(str(e), status_code=response.status_code, response=response.json())
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def validate_access_token(self) -> bool:
        """Validate that the access token is valid by making a test API call"""
        try:
            self._make_request("GET", "me")
            return True
        except Exception as e:
            logger.error(f"Error validating Figma access token: {e}")
            return False

    def get_file_info(self) -> Dict:
        """Get basic information about a Figma file"""
        return self._make_request("GET", f"files/{self.file_key}")

    def get_file(self) -> Dict:
        """Get the full Figma file content"""
        return self._make_request("GET", f"files/{self.file_key}")

    def extract_elements(self, file_content: Dict) -> List[Dict]:
        """Extract relevant elements from Figma file content"""
        elements = []

        def process_node(node: Dict):
            if 'type' not in node:
                return
            if node['type'] in self.config.get("components_to_analyze", ['FRAME', 'GROUP', 'COMPONENT', 'INSTANCE', 'TEXT']):
                element = {
                    'id': node.get('id'),
                    'name': node.get('name'),
                    'type': node.get('type'),
                    'description': node.get('description', ''),
                    'parent_id': node.get('parent_id'),
                    'position': {
                        'x': node.get('x', 0),
                        'y': node.get('y', 0)
                    },
                    'properties': {}
                }
                # Add specific properties based on type
                if node['type'] == 'TEXT':
                    element['properties'] = {
                        'characters': node.get('characters', ''),
                        'style': node.get('style', {})
                    }
                elif node['type'] in ['COMPONENT', 'INSTANCE']:
                    element['properties'] = {
                        'component_id': node.get('componentId'),
                        'styles': node.get('styles', {}),
                        'layout': node.get('layoutMode'),
                        'constraints': node.get('constraints', {})
                    }
                elements.append(element)
            if 'children' in node:
                for child in node['children']:
                    child['parent_id'] = node.get('id')
                    process_node(child)

        if 'document' in file_content:
            process_node(file_content['document'])
        return elements

    def get_design_tokens(self, file_id: str) -> Dict[str, Any]:
        """
        Extract design tokens (colors, typography, etc.) from the Figma file
        
        Args:
            file_id: The Figma file ID
            
        Returns:
            Dictionary of design tokens
        """
        try:
            data = self._make_request("GET", f"files/{file_id}/styles")
            
            styles = data.get("meta", {}).get("styles", [])
            tokens = {
                "colors": [],
                "typography": [],
                "effects": [],
                "spacing": []
            }
            
            for style in styles:
                style_type = style.get("styleType", "").lower()
                if style_type in tokens:
                    tokens[style_type].append({
                        "name": style.get("name", ""),
                        "description": style.get("description", ""),
                        "key": style.get("key", "")
                    })
            
            logger.info(f"Extracted {sum(len(v) for v in tokens.values())} design tokens")
            return tokens
            
        except FigmaAPIError as e:
            logger.error(f"Error fetching design tokens: {e}")
            raise

    @staticmethod
    def extract_elements_static(file_content: Dict) -> List[Dict]:
        """
        Static method to extract elements from Figma file content without requiring API connection
        
        Args:
            file_content: Dictionary containing Figma file content
            
        Returns:
            List of extracted elements
        """
        elements = []
        
        def process_node(node: Dict):
            """Recursively process nodes to extract elements"""
            # Skip if node doesn't have a type
            if 'type' not in node:
                return
                
            # Extract element if it's a relevant type
            if node['type'] in ['FRAME', 'GROUP', 'COMPONENT', 'INSTANCE', 'TEXT']:
                element = {
                    'id': node.get('id'),
                    'name': node.get('name'),
                    'type': node.get('type'),
                    'description': node.get('description', ''),
                    'parent_id': node.get('parent_id'),
                    'position': {
                        'x': node.get('x', 0),
                        'y': node.get('y', 0)
                    }
                }
                
                # Add specific properties based on type
                if node['type'] == 'TEXT':
                    element['properties'] = {
                        'characters': node.get('characters', ''),
                        'style': node.get('style', {})
                    }
                elif node['type'] in ['COMPONENT', 'INSTANCE']:
                    element['properties'] = {
                        'component_id': node.get('componentId'),
                        'styles': node.get('styles', {}),
                        'layout': node.get('layoutMode'),
                        'constraints': node.get('constraints', {})
                    }
                
                elements.append(element)
            
            # Process children recursively
            if 'children' in node:
                for child in node['children']:
                    child['parent_id'] = node.get('id')  # Add parent reference
                    process_node(child)
        
        # Start processing from the document
        if 'document' in file_content:
            process_node(file_content['document'])
        
        return elements