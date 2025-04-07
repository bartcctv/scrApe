import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from ..utilities.logger import setup_logger
from .request_manager import RequestManager

logger = setup_logger(__name__)

class ContentExtractor:
    def __init__(self, base_url):
        self.base_url = base_url
        self.request_manager = RequestManager()
        
    def extract_media_links(self, html_content):
        """Extract all media links from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        media_links = set()
        
        # Images
        for img in soup.find_all('img', src=True):
            src = img['src'].strip()
            absolute_url = urljoin(self.base_url, src)
            media_links.add(('image', absolute_url))
            
        # Videos
        for video in soup.find_all('video', src=True):
            src = video['src'].strip()
            absolute_url = urljoin(self.base_url, src)
            media_links.add(('video', absolute_url))
            
        # Audio
        for audio in soup.find_all('audio', src=True):
            src = audio['src'].strip()
            absolute_url = urljoin(self.base_url, src)
            media_links.add(('audio', absolute_url))
            
        # Embedded content (iframes)
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src'].strip()
            absolute_url = urljoin(self.base_url, src)
            media_links.add(('embedded', absolute_url))
            
        # CSS background images
        for element in soup.find_all(style=True):
            style = element['style']
            urls = re.findall(r'url\([\'"]?(.*?)[\'"]?\)', style)
            for url in urls:
                absolute_url = urljoin(self.base_url, url.strip())
                media_links.add(('background_image', absolute_url))
                
        return media_links
        
    def extract_text_content(self, html_content):
        """Extract and clean text content from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'head']):
            element.decompose()
            
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up multiple newlines
        text = '\n'.join(line for line in text.split('\n') if line.strip())
        
        return text
        
    def extract_from_page(self, url):
        """Extract all content from a specific page"""
        response = self.request_manager.make_request(url)
        if not response:
            return None
            
        content_type = response.headers.get('content-type', '')
        if 'text/html' in content_type:
            return {
                'url': url,
                'type': 'html',
                'text': self.extract_text_content(response.text),
                'media': list(self.extract_media_links(response.text))
            }
        else:
            return {
                'url': url,
                'type': content_type.split(';')[0],
                'content': response.content
            }
            
    def __init__(self, base_url, use_js=False):
        self.base_url = base_url
    self.request_manager = RequestManager()
    self.use_js = use_js
    if use_js:
        from .js_renderer import JSRenderer
        self.js_renderer = JSRenderer()

def extract_from_page(self, url):
    """Extract all content from a specific page"""
    if self.use_js:
        html_content = self.js_renderer.render_page(url)
        if not html_content:
            return None
        # Process with JS-rendered content
    else:
        # Original request-based processing    if self.use_js:
                html_content = self.js_renderer.render_page(url)
                if not html_content:
                    return None
                # Process with JS-rendered content
            else:
                response = self.request_manager.make_request(url)
                if not response:
                    return None
                # Process the response