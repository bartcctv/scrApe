import os
import json
from pathlib import Path
from ..config import settings
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)

class FileManager:
    def __init__(self):
        # Ensure storage directories exist
        Path(settings.DATA_STORAGE).mkdir(parents=True, exist_ok=True)
        Path(settings.MEDIA_STORAGE).mkdir(parents=True, exist_ok=True)
        
    def save_text(self, content, filename):
        """Save text content to file"""
        filepath = os.path.join(settings.DATA_STORAGE, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Text content saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save text content: {str(e)}")
            return False
            
    def save_json(self, data, filename):
        """Save data as JSON file"""
        filepath = os.path.join(settings.DATA_STORAGE, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON data saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON data: {str(e)}")
            return False
            
    def save_binary(self, data, filename):
        """Save binary data to file"""
        filepath = os.path.join(settings.MEDIA_STORAGE, filename)
        try:
            with open(filepath, 'wb') as f:
                f.write(data)
            logger.info(f"Binary data saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save binary data: {str(e)}")
            return False