import logging
import sys
import json
import os
from typing import Any, Optional

def setup_logger(name: str = "module_extractor") -> logging.Logger:
    """Configures and returns a logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Console Handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
    return logger

class JSONCache:
    """Simple file-based cache for storing results of expensive operations."""
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def get_cache_path(self, key: str) -> str:
        # Simple filename-safe hash of the key (URL) could be better, but let's use a simple approach
        safe_key = "".join([c if c.isalnum() else "_" for c in key])
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def get(self, key: str) -> Optional[Any]:
        path = self.get_cache_path(key)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def set(self, key: str, value: Any):
        path = self.get_cache_path(key)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to write cache: {e}")
