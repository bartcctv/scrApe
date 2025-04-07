import re
from urllib.parse import urlparse

def is_valid_url(url):
    """Check if a URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
        
def is_media_url(url):
    """Check if URL points to a media file"""
    media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp',
                       '.mp4', '.webm', '.mov', '.mp3', '.wav', '.ogg']
    return any(url.lower().endswith(ext) for ext in media_extensions)
    
def sanitize_filename(filename):
    """Sanitize a string to be used as a filename"""
    # Remove invalid characters
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    return filename[:255]