import re
import json
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from ..config import settings
from ..utilities.logger import setup_logger
from .request_manager import RequestManager

logger = setup_logger(__name__)

class APIDiscoverer:
    def __init__(self, base_url):
        self.base_url = base_url
        self.request_manager = RequestManager()
        self.common_api_paths = [
            'api', 'graphql', 'rest', 'v1', 'v2',
            'endpoint', 'service', 'data', 'ajax'
        ]
        
    def discover_from_html(self, html_content):
        """Find API endpoints mentioned in HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        endpoints = set()
        
        # Check for common JavaScript patterns
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Find fetch/AJAX calls
                patterns = [
                    r'fetch\(["\'](.*?)["\']\)',
                    r'\.get\(["\'](.*?)["\']\)',
                    r'\.post\(["\'](.*?)["\']\)',
                    r'ajax\(.*?url: ["\'](.*?)["\']',
                    r'axios\.get\(["\'](.*?)["\']\)'
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, script.string)
                    for match in matches:
                        absolute_url = urljoin(self.base_url, match)
                        endpoints.add(absolute_url)
                        
        # Check for links that might be API endpoints
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(api_path in href.lower() for api_path in self.common_api_paths):
                absolute_url = urljoin(self.base_url, href)
                endpoints.add(absolute_url)
                
        return endpoints
        
    def discover_from_js(self, js_content):
        """Find API endpoints in JavaScript files"""
        endpoints = set()
        
        # Look for common API URL patterns
        patterns = [
            r'https?://[^"\'\s]+/api/[^"\'\s]+',
            r'https?://[^"\'\s]+/v\d/[^"\'\s]+',
            r'baseURL:\s*["\'](.*?)["\']',
            r'apiEndpoint:\s*["\'](.*?)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, js_content)
            for match in matches:
                absolute_url = urljoin(self.base_url, match)
                endpoints.add(absolute_url)
                
        return endpoints
        
    def discover_from_network(self, url):
        """Analyze network traffic (requires Selenium or browser dev tools)"""
        # This would require integration with Selenium or a proxy
        # For now, we'll just return an empty set
        return set()
        
    def discover_api_endpoints(self):
        """Main method to discover all API endpoints"""
        logger.info(f"Starting API endpoint discovery for {self.base_url}")
        
        # First get the main page
        response = self.request_manager.make_request(self.base_url)
        if not response:
            return set()
            
        endpoints = set()
        
        # Discover from HTML
        if 'text/html' in response.headers.get('content-type', ''):
            html_endpoints = self.discover_from_html(response.text)
            endpoints.update(html_endpoints)
            
            # Find JavaScript files
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup.find_all('script', src=True):
                js_url = urljoin(self.base_url, script['src'])
                js_response = self.request_manager.make_request(js_url)
                if js_response and 'javascript' in js_response.headers.get('content-type', ''):
                    js_endpoints = self.discover_from_js(js_response.text)
                    endpoints.update(js_endpoints)
                    
        # Check common API paths directly
        for api_path in self.common_api_paths:
            test_url = urljoin(self.base_url, api_path)
            test_response = self.request_manager.make_request(test_url)
            if test_response and test_response.status_code == 200:
                endpoints.add(test_url)
                
        # Filter out non-API-looking endpoints
        filtered_endpoints = set()
        for endpoint in endpoints:
            parsed = urlparse(endpoint)
            path_parts = parsed.path.lower().split('/')
            
            # Check if path contains API indicators
            if any(api_indicator in path_parts for api_indicator in self.common_api_paths):
                filtered_endpoints.add(endpoint)
            # Or if response looks like JSON
            elif endpoint.endswith(('.json', '.xml')):
                filtered_endpoints.add(endpoint)
                
        logger.info(f"Discovered {len(filtered_endpoints)} API endpoints")
        return filtered_endpoints