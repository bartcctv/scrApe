import os
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from ..config import settings
from ..utilities.logger import setup_logger
from .request_manager import RequestManager

logger = setup_logger(__name__)

class DownloadManager:
    def __init__(self):
        self.request_manager = RequestManager()
        Path(settings.MEDIA_STORAGE).mkdir(parents=True, exist_ok=True)
        
    def get_filename_from_url(self, url):
        """Extract filename from URL"""
        path = urlparse(url).path
        filename = os.path.basename(path)
        
        if not filename:
            # If URL ends with slash, use domain name
            domain = urlparse(url).netloc
            filename = f"{domain}_content"
            
        return filename
        
    def get_media_type(self, url, content_type=None):
        """Determine media type from URL or content-type"""
        if content_type:
            return content_type.split('/')[0]
            
        extension = os.path.splitext(url)[1].lower()
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            return 'image'
        elif extension in ['.mp4', '.webm', '.mov']:
            return 'video'
        elif extension in ['.mp3', '.wav', '.ogg']:
            return 'audio'
        else:
            return 'other'
            
    def download_file(self, url, save_path=None):
        """Download a file from URL to local storage"""
        if not save_path:
            filename = self.get_filename_from_url(url)
            save_path = os.path.join(settings.MEDIA_STORAGE, filename)
            
        response = self.request_manager.make_request(url, stream=True)
        if not response:
            return None
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Handle potential filename conflicts
        counter = 1
        original_save_path = save_path
        while os.path.exists(save_path):
            base, ext = os.path.splitext(original_save_path)
            save_path = f"{base}_{counter}{ext}"
            counter += 1
            
        try:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            logger.info(f"Successfully downloaded {url} to {save_path}")
            return {
                'url': url,
                'local_path': save_path,
                'size': os.path.getsize(save_path),
                'media_type': self.get_media_type(url, response.headers.get('content-type'))
            }
        except Exception as e:
            logger.error(f"Failed to download {url}: {str(e)}")
            return None
        