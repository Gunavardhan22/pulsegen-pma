from typing import List, Dict, Any, Optional
from collections import defaultdict
import re
from urllib.parse import urlparse
from app.utils import setup_logger

logger = setup_logger()

class ModuleInference:
    """
    Infers logical modules and submodules from crawled documentation pages.
    Strategies:
    1. URL Path Segments: /docs/deployment/aws -> Module: Deployment, Submodule: AWS
    2. Page Titles: "API Reference - Users" -> Module: API Reference, Submodule: Users
    3. Heading structure from content blocks.
    """

    def __init__(self, start_urls: List[str]):
        # We assume the first start_url is the root for path analysis
        parsed = urlparse(start_urls[0])
        self.root_path_segments = [s for s in parsed.path.split('/') if s]
        
    def infer_structure(self, crawled_data: List[Dict]) -> Dict[str, Any]:
        """
        Organizes flat crawled pages into a nested dictionary structure.
        Returns: { "Module Name": { "pages": [], "submodules": { "Submodule Name": { "pages": [] } } } }
        """
        logger.info("Inferring module structure...")
        
        # Intermediate structure: path_tuple -> list of page_data
        grouped_pages = defaultdict(list)

        for page in crawled_data:
            url = page['url']
            title = page.get('title', '')
            
            path_segments = self._get_relevant_segments(url)
            
            # Strategy 2: If path segments are poor, try to infer from title
            if not path_segments or (len(path_segments) == 1 and path_segments[0].lower() in ['docs', 'index', 'home']):
                inferred = self._infer_from_title(title)
                if inferred:
                    path_segments = inferred
            
            if not path_segments:
                key = ("General",)
            else:
                key = tuple([self._format_segment(s) for s in path_segments])
            
            grouped_pages[key].append(page)

        # Build tree (Limit to 2 levels of hierarchy: Module -> Submodule)
        structure = {}
        
        for path_tuple, pages in grouped_pages.items():
            current_level = structure
            
            module_name = path_tuple[0] if path_tuple else "General"

            if module_name not in current_level:
                current_level[module_name] = {"pages": [], "submodules": {}}
            
            if len(path_tuple) > 1:
                submodule_name = path_tuple[1]
                if submodule_name not in current_level[module_name]["submodules"]:
                     current_level[module_name]["submodules"][submodule_name] = {"pages": []}
                
                current_level[module_name]["submodules"][submodule_name]["pages"].extend(pages)
            else:
                current_level[module_name]["pages"].extend(pages)

        return structure

    def _get_relevant_segments(self, url: str) -> List[str]:
        """Extracts path segments that likely represent modules."""
        parsed = urlparse(url)
        path = parsed.path
        parts = [p for p in path.split('/') if p and '.' not in p]
        
        # Filter out segments that are part of the root path
        relevant = []
        for i, p in enumerate(parts):
            if i < len(self.root_path_segments) and p == self.root_path_segments[i]:
                continue
            relevant.append(p)
               
        return relevant

    def _infer_from_title(self, title: str) -> Optional[List[str]]:
        """Infers hierarchy from page title like 'Module - Submodule'."""
        # Common separators in Doc titles
        separators = [' - ', ' | ', ' » ', ' : ']
        for sep in separators:
            if sep in title:
                parts = title.split(sep)
                # Usually titles are 'Page Title - Doc Title' or reversed
                # Heuristic: The shorter part is likely the Module/category
                # Or the one that doesn't change across many pages.
                # Since we don't have global context here easily, let's take the last part if many,
                # or the first part.
                return [p.strip() for p in parts if p.strip()][:2]
        return None

    def _format_segment(self, segment: str) -> str:
        """Converts 'getting-started' to 'Getting Started'."""
        # Remove version numbers like v1, v2
        if re.match(r'^v\d+$', segment.lower()):
            return segment.upper()
        return segment.replace('-', ' ').replace('_', ' ').replace('.html', '').title()
