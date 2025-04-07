import sqlite3
import os
from pathlib import Path
from ..config import settings
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)

class SQLExporter:
    def __init__(self):
        self.output_dir = os.path.join(settings.DATA_STORAGE, 'exports')
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
    def export_to_sql(self, db_path, output_filename='export.sql'):
        """Export SQLite database to SQL dump file"""
        output_path = os.path.join(self.output_dir, output_filename)
        try:
            conn = sqlite3.connect(db_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            logger.info(f"Exported SQL dump to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"SQL export failed: {str(e)}")
            return None