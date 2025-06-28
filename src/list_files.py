import os
from dotenv import load_dotenv
import yaml
from figma_client import FigmaClient
from loguru import logger
from collections import defaultdict

def load_config():
    """Load configuration from config.yaml"""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def analyze_node(node, elements=None, depth=0):
    """Analyze a node and its children"""
    if elements is None:
        elements = defaultdict(list)
    
    # Store node information by type
    node_type = node.get('type', 'Unknown')
    if node_type != 'DOCUMENT' and node_type != 'CANVAS':
        elements[node_type].append({
            'name': node.get('name', 'Unnamed'),
            'id': node.get('id', ''),
            'description': node.get('description', '')
        })
    
    # Recursively process children
    if node.get('children'):
        for child in node.get('children', []):
            analyze_node(child, elements, depth + 1)
            
    return elements

def main():
    # Load environment variables and config
    load_dotenv()
    config = load_config()
    
    # The specific file ID from your URL
    FILE_ID = "kvVRZ8x8LR6AXe6f6cGtNs"
    
    try:
        # Initialize Figma client
        figma_client = FigmaClient(
            access_token=os.getenv("FIGMA_ACCESS_TOKEN"),
            config=config["figma"]
        )
        
        # Validate Figma access
        if not figma_client.validate_access_token():
            print("❌ Invalid Figma access token. Please check your .env file")
            return
        
        print(f"\nAttempting to access Figma file: {FILE_ID}")
        
        try:
            # Get the full file data
            file_data = figma_client._make_request("GET", f"files/{FILE_ID}")
            
            if file_data:
                print("\n✅ Successfully accessed the Figma file!")
                print("-" * 50)
                print(f"Name: {file_data.get('name', 'Unnamed')}")
                print(f"Last Modified: {file_data.get('lastModified', 'N/A')}")
                print(f"Version: {file_data.get('version', 'N/A')}")
                
                # Analyze document structure
                print("\nDocument Elements:")
                print("-" * 50)
                document = file_data.get('document', {})
                elements = analyze_node(document)
                
                # Print elements by type
                for element_type, items in elements.items():
                    if items:
                        print(f"\n{element_type} Elements ({len(items)}):")
                        for item in items:
                            print(f"- {item['name']}")
                
                print("\nElement Count by Type:")
                print("-" * 50)
                for element_type, items in elements.items():
                    print(f"{element_type}: {len(items)} elements")
                
                # Check which elements are configured for analysis
                print("\nConfigured to analyze these types:")
                for comp_type in config["figma"]["components_to_analyze"]:
                    count = len(elements.get(comp_type, []))
                    print(f"- {comp_type}: {count} found")
                    
                print("-" * 50)
            else:
                print("\n❌ Could not access file data")
                
        except Exception as e:
            print(f"\n❌ Error accessing file: {str(e)}")
            print("\nTroubleshooting tips:")
            print("1. Verify your Figma access token has permission to access this file")
            print("2. Make sure you're using a Personal Access Token from Figma")
            print("3. Check if you're logged in to the correct Figma account")
            print("4. Ensure you have at least View access to the file")
            raise
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 