from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from ..config import settings
from ..utilities.validator import is_valid_url
from ..utilities.logger import setup_logger
from .request_manager import RequestManager

logger = setup_logger(__name__)

class URLDiscoverer:
    def __init__(self, base_url):
        self.base_url = base_url
        self.request_manager = RequestManager()
        self.visited_urls = set()
        self.discovered_urls = set()
        
    def get_domain(self, url):
        """Extract domain from URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
        
    def is_same_domain(self, url):
        """Check if URL belongs to the same domain"""
        return self.get_domain(url) == self.get_domain(self.base_url)
        
    def extract_links(self, html_content):
        """Extract all links from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()
        
        for tag in soup.find_all(['a', 'link'], href=True):
            url = tag['href'].strip()
            if url.startswith('#'):
                continue
                
            absolute_url = urljoin(self.base_url, url)
            if is_valid_url(absolute_url):
                links.add(absolute_url)
                
        for tag in soup.find_all(['img', 'script', 'iframe'], src=True):
            url = tag['src'].strip()
            absolute_url = urljoin(self.base_url, url)
            if is_valid_url(absolute_url):
                links.add(absolute_url)
                
        return links
        
    def discover_urls(self, current_url, depth=0):
        """Recursively discover URLs up to a certain depth"""
        if depth > settings.MAX_DEPTH:
            return
            
        if current_url in self.visited_urls:
            return
            
        self.visited_urls.add(current_url)
        logger.info(f"Discovering URLs at depth {depth}: {current_url}")
        
        response = self.request_manager.make_request(current_url)
        if not response:
            return
            
        content_type = response.headers.get('content-type', '')
        if 'text/html' not in content_type:
            return
            
        links = self.extract_links(response.text)
        for link in links:
            if link not in self.discovered_urls and self.is_same_domain(link):
                self.discovered_urls.add(link)
                self.discover_urls(link, depth + 1)
                
    def get_all_urls(self):
        """Start discovery and return all found URLs"""
        self.discover_urls(self.base_url)
        return self.discovered_urls
    
    # Can be used in URL discovery
sitemaps = self.robots.get_sitemaps()
if sitemaps:
    logger.info(f"Found {len(sitemaps)} sitemaps for alternative discovery")
    