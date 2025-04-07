from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
import time
from ..config import settings
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)

class JSRenderer:
    def __init__(self, headless=True):
        self.options = Options()
        if headless:
            self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        
        # Configure user agent rotation
        if settings.USER_AGENT_ROTATION:
            from ..config.user_agents import USER_AGENTS
            import random
            self.options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
        
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.set_page_load_timeout(settings.REQUEST_TIMEOUT)
        
    def render_page(self, url, wait_for=None, wait_time=5):
        """Render a page with JavaScript execution"""
        try:
            logger.info(f"Rendering JavaScript page: {url}")
            self.driver.get(url)
            
            # Wait for specific element if requested
            if wait_for:
                if isinstance(wait_for, str):
                    # CSS selector or XPath
                    WebDriverWait(self.driver, wait_time).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                    )
                elif isinstance(wait_for, dict):
                    # More complex wait conditions
                    if wait_for.get('type') == 'xpath':
                        WebDriverWait(self.driver, wait_time).until(
                            EC.presence_of_element_located((By.XPATH, wait_for['value']))
            
            # Optional: Scroll to bottom to trigger lazy-loaded content
            if settings.SCROLL_TO_BOTTOM:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # Allow time for loading
            
            return self.driver.page_source
            
        except Exception as e:
            logger.error(f"JavaScript rendering failed for {url}: {str(e)}")
            return None
            
    def extract_dynamic_links(self, url):
        """Extract links from dynamically loaded content"""
        page_source = self.render_page(url, wait_for="a")
        if not page_source:
            return set()
            
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        links = set()
        
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if href and not href.startswith(('javascript:', '#')):
                absolute_url = urljoin(url, href)
                links.add(absolute_url)
                
        return links
        
    def close(self):
        """Clean up the browser instance"""
        self.driver.quit()
        