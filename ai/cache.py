"""
In-Memory AI Response Cache
---------------------------
Caches Gemini calls by hashing prompt version + input content.
Reduces cost, rate-limits, and response latency.
"""

import hashlib
import time
from typing import Optional, Any, Dict
from config import config

class AICache:
    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self._store: Dict[str, Dict[str, Any]] = {}

    def _hash_key(self, prompt_version: str, payload: Any) -> str:
        serialized = f"{prompt_version}::{str(payload)}"
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, prompt_version: str, payload: Any) -> Optional[Any]:
        key = self._hash_key(prompt_version, payload)
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del self._store[key]
            return None
        return entry["data"]

    def set(self, prompt_version: str, payload: Any, data: Any, ttl: Optional[int] = None) -> None:
        key = self._hash_key(prompt_version, payload)
        duration = ttl if ttl is not None else self.default_ttl
        self._store[key] = {
            "data": data,
            "expires_at": time.time() + duration
        }

    def clear(self) -> None:
        self._store.clear()

ai_cache = AICache(default_ttl=config.AI_CACHE_TTL_SECONDS)
