import random
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ..config import settings, user_agents
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)

class RequestManager:
    def __init__(self):
        self.session = requests.Session()
        self.setup_retry_strategy()
        self.last_request_time = 0
        
    def setup_retry_strategy(self):
        retry_strategy = Retry(
            total=settings.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[408, 429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
    
    def get_random_user_agent(self):
        if settings.USER_AGENT_ROTATION:
            return random.choice(user_agents.USER_AGENTS)
        return user_agents.USER_AGENTS[0]
    
    def make_request(self, url, method='GET', **kwargs):
        # Respect crawl delay
        elapsed = time.time() - self.last_request_time
        if elapsed < settings.DELAY_BETWEEN_REQUESTS:
            time.sleep(settings.DELAY_BETWEEN_REQUESTS - elapsed)
        
        headers = kwargs.get('headers', {})
        headers['User-Agent'] = self.get_random_user_agent()
        kwargs['headers'] = headers
        kwargs['timeout'] = settings.REQUEST_TIMEOUT
        
        try:
            response = self.session.request(method, url, **kwargs)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response
            else:
                logger.warning(f"Request to {url} returned status code {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            return None