import os
import sys
import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    # Run tests from the project root
    pytest.main(["tests/test_figma_connection.py"])
