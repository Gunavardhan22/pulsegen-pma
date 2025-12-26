from typing import List, Dict, Any
from collections import defaultdict
import re
from app.utils import setup_logger

logger = setup_logger()

class ModuleInference:
    """
    Infers logical modules and submodules from crawled documentation pages.
    Strategies:
    1. URL Path Segments: /docs/deployment/aws -> Module: Deployment, Submodule: AWS
    2. Page Titles: "API Reference - Users" -> Module: API Reference, Submodule: Users
    3. Hierarchy from H1/H2 tags within pages.
    """

    def __init__(self, start_urls: List[str]):
        # We assume the first start_url is the root for path analysis
        self.root_path_segments = [s for s in start_urls[0].split('/') if s]
        
    def infer_structure(self, crawled_data: List[Dict]) -> Dict[str, Any]:
        """
        Organizes flat crawled pages into a nested dictionary structure.
        Returns: { "Module Name": { "content": [], "submodules": { "Submodule Name": { ... } } } }
        """
        logger.info("Inferring module structure...")
        
        # Intermediate structure: path_tuple -> list of page_data
        grouped_pages = defaultdict(list)

        for page in crawled_data:
            url = page['url']
            path_segments = self._get_relevant_segments(url)
            
            if not path_segments:
                # Fallback to title if path is too short (e.g. root page)
                key = ("General",)
            else:
                key = tuple([self._format_segment(s) for s in path_segments])
            
            grouped_pages[key].append(page)

        # Build tree
        structure = {}
        
        for path_tuple, pages in grouped_pages.items():
            current_level = structure
            
            # If path is empty or just root, put in a general bucket
            if not path_tuple:
                module_name = "General"
            else:
                module_name = path_tuple[0]

            if module_name not in current_level:
                current_level[module_name] = {"pages": [], "submodules": {}}
            
            # If there are submodules (more segments)
            if len(path_tuple) > 1:
                submodule_name = path_tuple[1]
                if submodule_name not in current_level[module_name]["submodules"]:
                     current_level[module_name]["submodules"][submodule_name] = {"pages": []}
                
                # We currently support 1 level of nesting for simplicity as requested, 
                # but we could go deeper.
                current_level[module_name]["submodules"][submodule_name]["pages"].extend(pages)
            else:
                current_level[module_name]["pages"].extend(pages)

        return structure

    def _get_relevant_segments(self, url: str) -> List[str]:
        """Extracts path segments that likely represent modules."""
        # Simple heuristic: remove protocol/domain, split by /, ignore common prefixes
        # This can be improved by comparing against the 'root' URL content.
        
        parts = [p for p in url.split('/') if p and '.' not in p and p not in ['http:', 'https:', 'www']]
        # Filter out parts that are common to the root domain if possible, or just take the last N
        # For a generic solution, taking the first 1-2 meaningful segments after domain is a good guess.
        
        # Heuristic: Skip the domain part.
        # e.g. example.com/docs/api/v1 -> ['docs', 'api', 'v1']
        # If docs is common, we might want 'api' as module.
        
        # Let's assume the segment AFTER the common prefix is the module.
        # For now, just taking the last 2 identifier-like segments usually works for "Module/Submodule"
        
        relevant = []
        for p in parts:
            if p not in self.root_path_segments: # rudimentary exclusion
               relevant.append(p)
               
        # If method returned empty (url matches root segments exactly), return []
        if not relevant and parts:
             return [] 

        return relevant

    def _format_segment(self, segment: str) -> str:
        """Converts 'getting-started' to 'Getting Started'."""
        return segment.replace('-', ' ').replace('_', ' ').replace('.html', '').title()
