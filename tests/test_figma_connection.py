import os
import pytest
from dotenv import load_dotenv
import yaml
from src.figma_client import FigmaClient, FigmaAPIError

# Load environment variables and config before tests
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

@pytest.fixture
def figma_client():
    """Create a Figma client instance for testing"""
    return FigmaClient(
        access_token=os.getenv("FIGMA_ACCESS_TOKEN"),
        file_key=os.getenv("FIGMA_FILE_KEY"),
        config=config["figma"]
    )

def test_figma_auth(figma_client):
    """Test Figma API authentication"""
    assert figma_client.validate_access_token(), "Failed to authenticate with Figma API"
    print("✅ Successfully authenticated with Figma API")

def test_find_digital_assistant_file(figma_client):
    """Test finding and accessing the Digital Assistant file"""
    try:
        # Get file info - you'll need to replace this with your actual file ID
        file_key = os.getenv("FIGMA_FILE_KEY")  # Add this to your .env file
        if not file_key:
            pytest.skip("FIGMA_FILE_KEY not set in environment variables")
        
        file_info = figma_client.get_file_info()
        assert file_info["name"] == "Digital Assistant", f"File name mismatch: {file_info['name']}"
        print(f"\n✅ Successfully found Digital Assistant file")
        print(f"File Information:")
        print(f"- Name: {file_info['name']}")
        print(f"- Last Modified: {file_info.get('lastModified', 'N/A')}")
        print(f"- Version: {file_info.get('version', 'N/A')}")
    except FigmaAPIError as e:
        pytest.fail(f"Failed to access Figma file: {str(e)}")

def test_extract_components(figma_client):
    """Test extracting components from the Digital Assistant file"""
    try:
        file_key = os.getenv("FIGMA_FILE_KEY")
        if not file_key:
            pytest.skip("FIGMA_FILE_KEY not set in environment variables")
        
        file_content = figma_client.get_file()
        components = figma_client.extract_elements(file_content)
        assert len(components) > 0, "No components found in file"
        
        print(f"\n✅ Successfully extracted {len(components)} components")
        print("\nFirst 5 components:")
        for comp in components[:5]:
            print(f"- {comp['name']} ({comp['type']})")
    except FigmaAPIError as e:
        pytest.fail(f"Failed to extract components: {str(e)}")

def test_design_tokens(figma_client):
    """Test extracting design tokens from the Digital Assistant file"""
    try:
        file_key = os.getenv("FIGMA_FILE_KEY")
        if not file_key:
            pytest.skip("FIGMA_FILE_KEY not set in environment variables")
        
        tokens = figma_client.get_design_tokens(file_key)
        print("\n✅ Successfully extracted design tokens:")
        for token_type, items in tokens.items():
            print(f"\n{token_type.title()} tokens: {len(items)}")
            for item in items[:3]:  # Show first 3 of each type
                print(f"- {item['name']}")
    except FigmaAPIError as e:
        pytest.fail(f"Failed to extract design tokens: {str(e)}")

if __name__ == "__main__":
    # Manual test execution
    print("Testing Figma Connection...")
    load_dotenv()
    
    try:
        client = FigmaClient(
            access_token=os.getenv("FIGMA_ACCESS_TOKEN"),
            file_key=os.getenv("FIGMA_FILE_KEY"),
            config=config["figma"]
        )
        
        # Test authentication
        if client.validate_access_token():
            print("\n✅ Successfully authenticated with Figma API")
        else:
            print("\n❌ Failed to authenticate with Figma API")
            exit(1)
        
        # Test file access
        file_key = os.getenv("FIGMA_FILE_KEY")
        if not file_key:
            print("\n❌ FIGMA_FILE_KEY not set in environment variables")
            print("Please add your Digital Assistant file ID to .env file:")
            print('FIGMA_FILE_KEY="your_file_key_here"')
            exit(1)
        
        # Get file info
        file_info = client.get_file_info()
        print(f"\nFile Information:")
        print(f"Name: {file_info['name']}")
        print(f"Last Modified: {file_info.get('lastModified', 'N/A')}")
        print(f"Version: {file_info.get('version', 'N/A')}")
        
        # Get file content and extract components
        file_content = client.get_file()
        components = client.extract_elements(file_content)
        print(f"\nFound {len(components)} components")
        if components:
            print("\nFirst 5 components:")
            for comp in components[:5]:
                print(f"- {comp['name']} ({comp['type']})")
        
        # Get design tokens
        tokens = client.get_design_tokens(file_key)
        print("\nDesign Tokens:")
        for token_type, items in tokens.items():
            print(f"\n{token_type.title()}: {len(items)} tokens")
            for item in items[:3]:
                print(f"- {item['name']}")
        
        print("\n✅ All Figma tests completed successfully")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        exit(1) 