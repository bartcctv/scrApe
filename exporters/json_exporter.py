import json
import os
from pathlib import Path
from ..config import settings
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)

class JSONExporter:
    def __init__(self):
        self.output_dir = os.path.join(settings.DATA_STORAGE, 'exports')
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
    def export_data(self, data, filename='export.json', indent=2):
        """Export data to JSON file"""
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            logger.info(f"Exported data to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"JSON export failed: {str(e)}")
            return None