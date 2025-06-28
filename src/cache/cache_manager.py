from functools import lru_cache
import hashlib
import json
from typing import Dict, Optional

class CacheManager:
    def __init__(self):
        self.cache = {}

    @lru_cache(maxsize=100)
    def get_cached_analysis(self, element_hash: str) -> Optional[Dict]:
        return self.cache.get(element_hash)

    def cache_analysis(self, element: Dict, analysis: Dict):
        element_hash = self._hash_element(element)
        self.cache[element_hash] = analysis

    def _hash_element(self, element: Dict) -> str:
        return hashlib.md5(
            json.dumps(element, sort_keys=True).encode()
        ).hexdigest()

    def clear_cache(self):
        self.cache.clear()
        self.get_cached_analysis.cache_clear()