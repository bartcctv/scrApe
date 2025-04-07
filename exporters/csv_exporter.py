import csv
import os
from pathlib import Path
from ..config import settings
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)

class CSVExporter:
    def __init__(self):
        self.output_dir = os.path.join(settings.DATA_STORAGE, 'exports')
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
    def export_urls(self, urls_data, filename='urls_export.csv'):
        """Export discovered URLs to CSV"""
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=urls_data[0].keys())
                writer.writeheader()
                writer.writerows(urls_data)
            logger.info(f"Exported {len(urls_data)} URLs to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"CSV export failed: {str(e)}")
            return None
            
    def export_content(self, content_data, filename='content_export.csv'):
        """Export extracted content to CSV"""
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=content_data[0].keys())
                writer.writeheader()
                writer.writerows(content_data)
            logger.info(f"Exported {len(content_data)} content items to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Content export failed: {str(e)}")
            return None