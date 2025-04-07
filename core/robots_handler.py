import urllib.robotparser
from urllib.parse import urlparse, urljoin
import requests
import time
from typing import Dict, List, Optional, Tuple
from ..config import settings
from ..utilities.logger import setup_logger
from .request_manager import RequestManager

logger = setup_logger(__name__)

class RobotsHandler:
    def __init__(self, base_url: str, respect_robots: bool = True):
        """
        Initialize robots.txt handler
        
        Args:
            base_url: The base URL of the site being scraped
            respect_robots: Whether to honor robots.txt rules (default: True)
        """
        self.base_url = base_url
        self.respect_robots = respect_robots
        self.parser = urllib.robotparser.RobotFileParser()
        self.request_manager = RequestManager()
        self.crawl_delays: Dict[str, float] = {}
        self.disallowed_paths: Dict[str, List[str]] = {}
        
        # Initialize with domain's robots.txt
        self._fetch_robots_txt()
        
    def _fetch_robots_txt(self) -> None:
        """Fetch and parse the robots.txt file for the domain"""
        robots_url = urljoin(self.base_url, '/robots.txt')
        
        try:
            response = self.request_manager.make_request(robots_url)
            if response and response.status_code == 200:
                # Decode with fallback for encoding issues
                content = response.content.decode('utf-8', errors='replace')
                self.parser.parse(content.splitlines())
                
                # Additional parsing for extended features
                self._parse_extended_rules(content)
                logger.info(f"Successfully parsed robots.txt from {robots_url}")
            else:
                logger.warning(f"No robots.txt found at {robots_url} or inaccessible")
                self.parser.allow_all = True
        except Exception as e:
            logger.error(f"Error fetching robots.txt: {str(e)}")
            self.parser.allow_all = True
    
    def _parse_extended_rules(self, content: str) -> None:
        """Parse additional rules beyond standard RobotFileParser capabilities"""
        for line in content.splitlines():
            line = line.strip()
            
            # Parse crawl-delay directives
            if line.lower().startswith('crawl-delay:'):
                try:
                    delay = float(line.split(':', 1)[1].strip())
                    # Apply to all user agents (*) unless specified otherwise
                    self.crawl_delays['*'] = delay
                    logger.debug(f"Found crawl-delay: {delay} seconds")
                except (IndexError, ValueError):
                    pass
                    
            # Parse sitemap locations
            elif line.lower().startswith('sitemap:'):
                pass  # Could be used for alternative scraping
            
            # Parse custom disallow rules
            elif line.lower().startswith('disallow:'):
                pass  # Standard parser handles this
    
    def is_allowed(self, url: str, user_agent: str = '*') -> Tuple[bool, Optional[str]]:
        """
        Check if URL is allowed by robots.txt with bypass options
        
        Args:
            url: The URL to check
            user_agent: The user agent to check against
            
        Returns:
            Tuple of (is_allowed, reason) where reason explains any blocking
        """
        if not self.respect_robots:
            return True, "robots.txt checking disabled"
            
        if not self.parser:
            return True, "no robots.txt parser available"
            
        # Check standard rules first
        allowed = self.parser.can_fetch(user_agent, url)
        reason = None
        
        if not allowed:
            reason = f"Blocked by robots.txt for {user_agent}"
            
        # Apply crawl delay if configured to respect it
        if settings.RESPECT_CRAWL_DELAY and '*' in self.crawl_delays:
            delay = self.crawl_delays['*']
            if delay > settings.DELAY_BETWEEN_REQUESTS:
                settings.DELAY_BETWEEN_REQUESTS = delay
                logger.info(f"Adjusted crawl delay to {delay} seconds as per robots.txt")
                
        return allowed, reason
    
    def get_crawl_delay(self, user_agent: str = '*') -> float:
        """Get the crawl delay for a specific user agent"""
        return self.crawl_delays.get(user_agent, 0)
        
    def bypass_restrictions(self, strategy: str = "user_agent_rotation") -> bool:
        """
        Attempt to bypass robots.txt restrictions using ethical methods
        
        Args:
            strategy: The bypass strategy to use
                     Options: "user_agent_rotation", "subdomain", "delay_adjustment"
                     
        Returns:
            bool: True if bypass was successful/applied
        """
        if not self.respect_robots:
            return False
            
        if strategy == "user_agent_rotation":
            logger.warning("Using user agent rotation to potentially bypass restrictions")
            return True
            
        elif strategy == "delay_adjustment":
            if '*' in self.crawl_delays:
                new_delay = max(1, self.crawl_delays['*'] - 1)
                settings.DELAY_BETWEEN_REQUESTS = new_delay
                logger.warning(f"Adjusted delay to {new_delay}s (below robots.txt recommendation)")
                return True
                
        elif strategy == "subdomain":
            parsed = urlparse(self.base_url)
            if parsed.netloc.startswith('www.'):
                new_domain = parsed.netloc[4:]
                self.base_url = f"{parsed.scheme}://{new_domain}"
                logger.warning(f"Trying alternate domain: {self.base_url}")
                self._fetch_robots_txt()  # Re-check for new domain
                return True
                
        return False
    
    def get_sitemaps(self) -> List[str]:
        """Extract sitemap URLs from robots.txt (alternative scraping approach)"""
        if not self.parser:
            return []
            
        # Standard parser doesn't expose sitemaps, so we need to reparse
        sitemaps = []
        robots_url = urljoin(self.base_url, '/robots.txt')
        
        try:
            response = self.request_manager.make_request(robots_url)
            if response and response.status_code == 200:
                for line in response.text.splitlines():
                    line = line.strip()
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        sitemaps.append(sitemap_url)
        except Exception as e:
            logger.error(f"Error fetching sitemaps: {str(e)}")
            
        return sitemaps