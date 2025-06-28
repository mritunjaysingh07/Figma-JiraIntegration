from enum import Enum
from typing import Dict, Optional
from datetime import datetime
import json
from pathlib import Path

class PromptVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"

class PromptManager:
    def __init__(self):
        self.history_file = Path("prompt_history.json")
        self.current_version = PromptVersion.V3
        self._load_history()

    def _load_history(self):
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = {}

    def get_prompt(self, prompt_type: str, version: Optional[PromptVersion] = None) -> str:
        version = version or self.current_version
        return PROMPT_VERSIONS[version][prompt_type]

    def record_prompt_performance(self, version: PromptVersion, metrics: Dict):
        timestamp = datetime.now().isoformat()
        if version not in self.history:
            self.history[version] = []
        
        self.history[version].append({
            "timestamp": timestamp,
            "metrics": metrics
        })
        
        self._save_history()

    def _save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def rollback_to_version(self, version: PromptVersion):
        if version in PromptVersion:
            self.current_version = version
            return True
        return False

PROMPT_VERSIONS = {
    PromptVersion.V1: {
        "context": "Basic V1 prompt...",
        "element": "Basic V1 element analysis..."
    },
    PromptVersion.V2: {
        "context": "Enhanced V2 prompt with better context...",
        "element": "Improved V2 element analysis..."
    },
    PromptVersion.V3: {
        "context": "Latest V3 prompt with advanced features...",
        "element": "Advanced V3 element analysis..."
    }
}