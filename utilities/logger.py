import logging
import os
from pathlib import Path
from ..config import settings

def setup_logger(name):
    """Configure and return a logger instance"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Ensure log directory exists
    Path(settings.LOG_STORAGE).mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
    # File handler
    log_file = os.path.join(settings.LOG_STORAGE, 'scraper.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger