import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Scraper settings
MAX_DEPTH = 3
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 2  # seconds
CONCURRENT_REQUESTS = 5

# Storage settings
MEDIA_STORAGE = os.path.join(BASE_DIR, 'storage/media')
DATA_STORAGE = os.path.join(BASE_DIR, 'storage/data')
LOG_STORAGE = os.path.join(BASE_DIR, 'storage/logs')

# Authentication settings (for authorized scraping only)
AUTH_CREDENTIALS = {
    'username': None,
    'password': None,
    'api_key': None
}

# Legal compliance
USER_AGENT_ROTATION = True
RESPECT_ROBOTS_TXT = False

# Legal compliance settings
RESPECT_ROBOTS_TXT = False  # Whether to check robots.txt at all
RESPECT_CRAWL_DELAY = True  # Whether to honor crawl-delay directives
BYPASS_STRATEGY = None  # None or one of: "user_agent_rotation", "subdomain", "delay_adjustment"

# config/settings.py (Secure Settings)
# Authentication security settings
MAX_LOGIN_ATTEMPTS = 3  # Maximum attempts before lockout
LOCKOUT_TIME = 300  # 5 minutes in seconds
DELAY_BETWEEN_ATTEMPTS = 5  # Seconds between attempts