#!/usr/bin/env python3
import argparse
import os
import time
from typing import Dict, List, Optional, Set, Tuple
from core.url_discovery import URLDiscoverer
from core.content_extractor import ContentExtractor
from core.download_manager import DownloadManager
from core.auth_handler import AuthHandler
from core.api_discovery import APIDiscoverer
from core.robots_handler import RobotsHandler
from core.js_renderer import JSRenderer
from storage.database import DatabaseManager
from storage.file_manager import FileManager
from exporters.csv_exporter import CSVExporter
from exporters.json_exporter import JSONExporter
from exporters.sql_exporter import SQLExporter
from utilities.logger import setup_logger
from utilities.validator import is_valid_url
from config import settings

logger = setup_logger(__name__)

class EthicalScraper:
    def __init__(self, base_url: str, use_js: bool = False, export_formats: Optional[List[str]] = None):
        """
        Initialize the web scraper with configuration options
        
        Args:
            base_url: The root URL to start scraping from
            use_js: Whether to use JavaScript rendering (default: False)
            export_formats: List of export formats (e.g., ['csv', 'json'])
        """
        if not is_valid_url(base_url):
            raise ValueError(f"Invalid base URL: {base_url}")

        self.base_url = base_url.rstrip('/')
        self.use_js = use_js
        self.export_formats = export_formats or ['json']
        self.db = DatabaseManager()
        self.file_manager = FileManager()
        self.download_manager = DownloadManager()
        self.auth_handler = AuthHandler()
        self.robots = RobotsHandler(self.base_url, respect_robots=settings.RESPECT_ROBOTS_TXT)
        
        # Initialize JavaScript renderer if needed
        self.js_renderer = None
        if self.use_js:
            self.js_renderer = JSRenderer(headless=True)
        
        # Apply bypass strategy if configured
        if settings.BYPASS_STRATEGY:
            self.robots.bypass_restrictions(settings.BYPASS_STRATEGY)

    def _check_scrape_permission(self, url: str) -> bool:
        """Verify if we're allowed to scrape the given URL"""
        allowed, reason = self.robots.is_allowed(url)
        if not allowed:
            logger.error(f"Scraping blocked by robots.txt for {url}: {reason}")
            if settings.BYPASS_STRATEGY:
                logger.warning(f"Attempting bypass using {settings.BYPASS_STRATEGY} strategy")
                return self.robots.bypass_restrictions(settings.BYPASS_STRATEGY)
            return False
        return True

    def discover_urls(self) -> Set[str]:
        """Discover all URLs within the domain with robots.txt checking"""
        if not self._check_scrape_permission(self.base_url):
            return set()

        logger.info(f"Starting URL discovery for {self.base_url}")
        discoverer = URLDiscoverer(self.base_url)
        urls = discoverer.get_all_urls()
        
        # Filter URLs through robots.txt
        filtered_urls = set()
        for url in urls:
            if self._check_scrape_permission(url):
                self.db.save_url(url, discoverer.get_domain(url))
                filtered_urls.add(url)
        
        logger.info(f"Discovered {len(filtered_urls)} allowed URLs")
        return filtered_urls
        
    def discover_api_endpoints(self) -> Set[str]:
        """Discover and log API endpoints with robots.txt checking"""
        if not self._check_scrape_permission(self.base_url):
            return set()

        logger.info("Starting API endpoint discovery")
        discoverer = APIDiscoverer(self.base_url)
        endpoints = discoverer.discover_api_endpoints()
        
        # Filter endpoints through robots.txt
        filtered_endpoints = set()
        for endpoint in endpoints:
            if self._check_scrape_permission(endpoint):
                self.db.save_url(endpoint, discoverer.get_domain(self.base_url), 
                               visited=False, status=None)
                filtered_endpoints.add(endpoint)
        
        logger.info(f"Discovered {len(filtered_endpoints)} allowed API endpoints")
        return filtered_endpoints
        
    def extract_content(self, urls: Optional[Set[Tuple[int, str]]] = None) -> None:
        """
        Extract content from discovered URLs with rate limiting
        
        Args:
            urls: Optional set of (id, url) tuples to extract
        """
        if not urls:
            # Get unvisited URLs from database
            cursor = self.db.connection.cursor()
            cursor.execute('SELECT id, url FROM urls WHERE visited = 0')
            urls = cursor.fetchall()

        for url_id, url in urls:
            if not self._check_scrape_permission(url):
                continue

            logger.info(f"Extracting content from {url}")
            
            # Respect crawl delay
            delay = self.robots.get_crawl_delay()
            if delay > 0:
                time.sleep(delay)

            extractor = ContentExtractor(self.base_url, use_js=self.use_js)
            content = extractor.extract_from_page(url)
            
            if not content:
                self._mark_url_visited(url_id, 404)
                continue
                
            if content['type'] == 'html':
                # Save text content
                content_id = self.db.save_content(url_id, 'html', content['text'])
                    
                # Save media references
                for media_type, media_url in content['media']:
                    if self._check_scrape_permission(media_url):
                        download_result = self.download_manager.download_file(media_url)
                        if download_result:
                            self.db.save_media(
                                url_id,
                                media_url,
                                download_result['media_type'],
                                download_result['local_path'],
                                download_result['size'])
                            
                self._mark_url_visited(url_id, 200)
            else:
                # Handle non-HTML content
                download_result = self.download_manager.download_file(url)
                if download_result:
                    self.db.save_media(
                        url_id,
                        url,
                        download_result['media_type'],
                        download_result['local_path'],
                        download_result['size'])
                self._mark_url_visited(url_id, 200)

    def _mark_url_visited(self, url_id: int, status: int) -> None:
        """Mark URL as visited in database"""
        cursor = self.db.connection.cursor()
        cursor.execute(
            'UPDATE urls SET visited = 1, http_status = ? WHERE id = ?',
            (status, url_id))
        self.db.connection.commit()

    def export_data(self, data_type: str = 'all') -> Dict[str, Optional[str]]:
        """
        Export scraped data in specified formats
        
        Args:
            data_type: What to export ('all', 'urls', or 'content')
            
        Returns:
            Dictionary of export paths keyed by format and type
        """
        exporters = {
            'csv': CSVExporter(),
            'json': JSONExporter(),
            'sql': SQLExporter()
        }
        
        results = {}
        
        if data_type in ['all', 'urls']:
            cursor = self.db.connection.cursor()
            cursor.execute('SELECT url, domain, visited FROM urls')
            urls_data = [dict(zip(['url', 'domain', 'visited'], row)) 
                        for row in cursor.fetchall()]
            
            for fmt in self.export_formats:
                if fmt in exporters:
                    results[f'urls_{fmt}'] = exporters[fmt].export_urls(
                        urls_data,
                        filename=f'urls_export.{fmt}'
                    )
        
        if data_type in ['all', 'content']:
            cursor = self.db.connection.cursor()
            cursor.execute('''
                SELECT u.url, c.content_type, c.text_content 
                FROM content c
                JOIN urls u ON c.url_id = u.id
            ''')
            content_data = [dict(zip(['url', 'type', 'content'], row)) 
                          for row in cursor.fetchall()]
            
            for fmt in self.export_formats:
                if fmt in exporters:
                    results[f'content_{fmt}'] = exporters[fmt].export_content(
                        content_data,
                        filename=f'content_export.{fmt}'
                    )
        
        return results

    def run(self) -> bool:
        """Run the complete scraping process with error handling"""
        try:
            # Step 1: Initial robots.txt check
            if not self._check_scrape_permission(self.base_url):
                logger.error("Scraping not allowed by robots.txt and bypass failed")
                return False

            # Step 2: URL discovery
            urls = self.discover_urls()
            
            # Step 3: API endpoint discovery
            api_endpoints = self.discover_api_endpoints()
            all_urls = urls.union(api_endpoints)
            
            # Step 4: Content extraction
            if all_urls:
                self.extract_content([(None, url) for url in all_urls])
            
            # Step 5: Data export
            export_results = self.export_data()
            logger.info(f"Export results: {export_results}")
            
            logger.info("Scraping process completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Scraping process failed: {str(e)}", exc_info=True)
            return False
        finally:
            if self.js_renderer:
                self.js_renderer.close()
            self.db.close()

def parse_args() -> argparse.Namespace:
    """Parse and validate command line arguments"""
    parser = argparse.ArgumentParser(
        description='Ethical Web Scraper with JavaScript rendering and API discovery',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('url', help='Base URL to scrape')
    parser.add_argument('--js', action='store_true', 
                       help='Enable JavaScript rendering')
    parser.add_argument('--export', nargs='+', choices=['csv', 'json', 'sql'],
                       default=['json'], help='Export formats')
    parser.add_argument('--auth', help='Authentication type', 
                       choices=['basic', 'form'])
    parser.add_argument('--username', help='Username for authentication')
    parser.add_argument('--password', help='Password for authentication')
    parser.add_argument('--ignore-robots', action='store_true',
                       help='Disable robots.txt checking (not recommended)')
    parser.add_argument('--bypass-strategy', 
                       choices=['user_agent_rotation', 'subdomain', 'delay_adjustment'],
                       help='Strategy to attempt if blocked by robots.txt')
    
    args = parser.parse_args()
    
    # Validate URL format
    if not is_valid_url(args.url):
        parser.error(f"Invalid URL format: {args.url}")
    
    # Validate authentication arguments
    if args.auth == 'basic' and not (args.username and args.password):
        parser.error("Basic authentication requires both --username and --password")
    
    return args

def configure_settings(args: argparse.Namespace) -> None:
    """Update settings based on command line arguments"""
    settings.RESPECT_ROBOTS_TXT = not args.ignore_robots
    if args.bypass_strategy:
        settings.BYPASS_STRATEGY = args.bypass_strategy

def main() -> None:
    """Main entry point for the scraper"""
    args = parse_args()
    configure_settings(args)
    
    scraper = EthicalScraper(
        args.url,
        use_js=args.js,
        export_formats=args.export
    )
    
    # Handle authentication if provided
    if args.auth == 'basic' and args.username and args.password:
        if not scraper.auth_handler.basic_auth(args.url, args.username, args.password):
            logger.error("Authentication failed")
            exit(1)
        logger.info("Authentication successful")
    
    success = scraper.run()
    exit(0 if success else 1)

if __name__ == '__main__':
    main()
    