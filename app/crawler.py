import requests
from urllib.parse import urlparse, urljoin, urlunparse
from typing import Set, Dict, List, Optional
from app.parser import DocParser
from app.utils import setup_logger, JSONCache
import time

logger = setup_logger()

class Crawler:
    def __init__(self, start_urls: List[str], max_depth: int = 2, max_pages: int = 50, use_cache: bool = True):
        self.start_urls = start_urls
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited: Set[str] = set()
        self.results: List[Dict] = []
        self.base_domains: Set[str] = {urlparse(url).netloc for url in start_urls}
        self.cache = JSONCache() if use_cache else None

    def is_valid_url(self, url: str) -> bool:
        parsed = urlparse(url)
        # Check if internal link (same domain) and http/https
        return (parsed.scheme in ['http', 'https'] and 
                parsed.netloc in self.base_domains and 
                not any(ext in parsed.path.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.pdf', '.css', '.js', '.zip', '.svg', '.woff', '.ttf']))

    def normalize_url(self, url: str) -> str:
        """Removes query params and fragments to avoid duplicate crawling of same page."""
        parsed = urlparse(url)
        return urlunparse(parsed._replace(fragment="", query=""))

    def crawl(self):
        queue = [(url, 0) for url in self.start_urls]
        
        while queue and len(self.visited) < self.max_pages:
            current_url, depth = queue.pop(0)
            normalized_url = self.normalize_url(current_url)

            if normalized_url in self.visited or depth > self.max_depth:
                continue

            if not self.is_valid_url(normalized_url):
                continue

            # Check Cache
            if self.cache:
                cached_data = self.cache.get(normalized_url)
                if cached_data:
                    logger.info(f"Cache hit: {normalized_url}")
                    self.results.append(cached_data)
                    self.visited.add(normalized_url)
                    # We still need to find links if depth allows, but if it's cached we might have links too?
                    # For simplicity, we just process cached page's content for links if needed.
                    # Implementing link discovery from cached content:
                    parser = DocParser(cached_data.get('html', '')) # We should store HTML in cache
                    self._discover_links(parser, normalized_url, depth, queue)
                    continue

            logger.info(f"Crawling: {normalized_url} (Depth: {depth})")
            
            try:
                response = requests.get(normalized_url, timeout=10)
                response.raise_for_status()
                
                # Mark visited immediately
                self.visited.add(normalized_url)
                
                # Parse content
                parser = DocParser(response.text)
                title = parser.get_title()
                content = parser.extract_content()
                
                page_data = {
                    "url": normalized_url,
                    "title": title,
                    "content": content,
                    "html": response.text # Store HTML for cache-based link discovery
                }
                
                self.results.append(page_data)
                
                if self.cache:
                    self.cache.set(normalized_url, page_data)

                # Find links for recursion
                self._discover_links(parser, normalized_url, depth, queue)
                
                # Be polite
                time.sleep(0.5)

            except requests.RequestException as e:
                logger.error(f"Failed to fetch {normalized_url}: {e}")
            except Exception as e:
                logger.error(f"Error processing {normalized_url}: {e}")

        logger.info(f"Crawling finished. Visited {len(self.visited)} pages.")
        return self.results

    def _discover_links(self, parser, current_url, depth, queue):
        if depth < self.max_depth:
            for link in parser.soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(current_url, href)
                normalized_link = self.normalize_url(absolute_url)
                
                if normalized_link not in self.visited and self.is_valid_url(normalized_link):
                   # Check if already in queue to avoid duplicates
                   if not any(item[0] == absolute_url for item in queue):
                        queue.append((absolute_url, depth + 1))

def run_crawler(urls: List[str], max_depth: int = 2, use_cache: bool = True) -> List[Dict]:
    crawler = Crawler(start_urls=urls, max_depth=max_depth, use_cache=use_cache)
    return crawler.crawl()
