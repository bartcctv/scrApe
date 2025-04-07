import sqlite3
from sqlite3 import Error
from pathlib import Path
from ..config import settings
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_file = os.path.join(settings.DATA_STORAGE, 'scraper.db')
        self.connection = None
        self.connect()
        self.initialize_database()
        
    def connect(self):
        """Create a database connection"""
        try:
            self.connection = sqlite3.connect(self.db_file)
            logger.info(f"Connected to database at {self.db_file}")
        except Error as e:
            logger.error(f"Database connection error: {str(e)}")
            
    def initialize_database(self):
        """Initialize database tables if they don't exist"""
        try:
            cursor = self.connection.cursor()
            
            # Create URLs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    domain TEXT,
                    visited BOOLEAN DEFAULT 0,
                    visit_timestamp DATETIME,
                    http_status INTEGER
                )
            ''')
            
            # Create content table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url_id INTEGER,
                    content_type TEXT,
                    text_content TEXT,
                    FOREIGN KEY (url_id) REFERENCES urls (id)
                )
            ''')
            
            # Create media table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url_id INTEGER,
                    media_url TEXT,
                    media_type TEXT,
                    local_path TEXT,
                    file_size INTEGER,
                    FOREIGN KEY (url_id) REFERENCES urls (id)
                )
            ''')
            
            self.connection.commit()
        except Error as e:
            logger.error(f"Database initialization error: {str(e)}")
            
    def save_url(self, url, domain, visited=False, status=None):
        """Save URL to database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO urls (url, domain, visited, visit_timestamp, http_status)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (url, domain, visited, status))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            logger.error(f"Failed to save URL {url}: {str(e)}")
            return None
            
    def save_content(self, url_id, content_type, text_content):
        """Save content to database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO content (url_id, content_type, text_content)
                VALUES (?, ?, ?)
            ''', (url_id, content_type, text_content))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            logger.error(f"Failed to save content for URL ID {url_id}: {str(e)}")
            return None
            
    def save_media(self, url_id, media_url, media_type, local_path, file_size):
        """Save media information to database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO media (url_id, media_url, media_type, local_path, file_size)
                VALUES (?, ?, ?, ?, ?)
            ''', (url_id, media_url, media_type, local_path, file_size))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            logger.error(f"Failed to save media {media_url}: {str(e)}")
            return None
            
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
            