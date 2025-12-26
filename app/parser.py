from bs4 import BeautifulSoup, Tag, NavigableString
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("module_extractor")

class DocParser:
    """
    Parses HTML content to extract meaningful documentation text and structure.
    """

    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self._clean_soup()

    def _clean_soup(self):
        """Removes common non-content elements like navbars, footers, and scripts."""
        for tag_name in ['nav', 'footer', 'script', 'style', 'noscript', 'iframe', 'header', 'aside']:
            for tag in self.soup.find_all(tag_name):
                tag.decompose()
        
        # Remove elements by common classes/ids used for navigation or useless extras
        # This is a heuristic approach and might need tuning for specific docs
        common_noise_selectors = [
            '.navigation', '.sidebar', '.menu', '#menu', '.footer', '#footer', 
            '.cookie-banner', '.ad', '.advertisement', '.social-share', 
            '.breadcrumb', '.toc'
        ]
        for selector in common_noise_selectors:
            for tag in self.soup.select(selector):
                tag.decompose()

    def get_title(self) -> str:
        """Extracts the page title."""
        if self.soup.title:
            return self.soup.title.get_text(strip=True)
        h1 = self.soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        return "Untitled Document"

    def extract_content(self) -> List[Dict[str, str]]:
        """
        Extracts content preserving hierarchy (H1-H4).
        Returns a list of content blocks with 'level', 'heading', and 'text'.
        """
        content_blocks = []
        
        # Find the main content area if possible, otherwise use body
        main_content = self.soup.find('main') or self.soup.find('article') or self.soup.find('div', role='main') or self.soup.body
        
        if not main_content:
            logger.warning("Could not find body or main content area.")
            return []

        current_heading = "Introduction"
        current_level = 0
        current_text = []

        for element in main_content.descendants:
            if isinstance(element, Tag):
                if element.name in ['h1', 'h2', 'h3', 'h4']:
                    # Finish previous block
                    if current_text:
                        content_blocks.append({
                            "level": current_level,
                            "heading": current_heading,
                            "text": " ".join(current_text).strip()
                        })
                        current_text = []
                    
                    current_heading = element.get_text(strip=True)
                    current_level = int(element.name[1]) # 1, 2, 3, or 4
                
                elif element.name in ['p', 'li', 'td', 'div', 'span', 'pre', 'code']:
                    # Extract text from these structural elements, but ensure we don't duplicate
                    # descendants loop handles deep nesting, so we need to be careful.
                    # Text extraction from block-level elements is safer.
                    # Strategy: If it's a leaf node or contains only strings, take it.
                    # Easier strategy: Get direct text stripped.
                    
                    # Better approach for linear text extraction:
                    # Iterate direct children? No, structure is deep.
                    pass

            if isinstance(element, NavigableString):
                text = element.strip()
                if text:
                    # Avoid adding text that is within the heading itself (handled by heading switch)
                    parent = element.parent
                    if parent.name not in ['h1', 'h2', 'h3', 'h4', 'script', 'style']:
                         current_text.append(text)

        # Append final block
        if current_text:
            content_blocks.append({
                "level": current_level,
                "heading": current_heading,
                "text": " ".join(current_text).strip()
            })

        return content_blocks

    def get_raw_text(self) -> str:
        """Returns the full flattened text of the cleaned content."""
        blocks = self.extract_content()
        return "\n\n".join([f"{b['heading']}\n{b['text']}" for b in blocks])
