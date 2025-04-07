# core/auth_handler.py (Secure Implementation)
import time
from typing import Optional, Tuple
from ..config import settings
from ..utilities.logger import setup_logger
from .request_manager import RequestManager

logger = setup_logger(__name__)

class SecureAuthHandler:
    def __init__(self):
        self.request_manager = RequestManager()
        self.failed_attempts = 0
        self.lockout_until = 0
        
    def attempt_login(self, url: str, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Securely attempt login with rate limiting
        
        Args:
            url: Login endpoint URL
            username: Username to try
            password: Password to try
            
        Returns:
            Tuple of (success, message)
        """
        # Check if we're in lockout period
        if time.time() < self.lockout_until:
            wait_time = self.lockout_until - time.time()
            return False, f"Account locked. Try again in {wait_time:.1f} seconds"
        
        # Implement rate limiting
        if self.failed_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            self.lockout_until = time.time() + settings.LOCKOUT_TIME
            self.failed_attempts = 0
            return False, "Too many attempts. Account temporarily locked"
        
        # Make the login attempt
        response = self.request_manager.make_request(
            url,
            method='POST',
            data={'username': username, 'password': password}
        )
        
        if response and response.status_code == 200:
            self.failed_attempts = 0
            return True, "Login successful"
        
        self.failed_attempts += 1
        remaining_attempts = settings.MAX_LOGIN_ATTEMPTS - self.failed_attempts
        return False, f"Login failed. {remaining_attempts} attempts remaining"