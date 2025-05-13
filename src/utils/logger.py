import logging
from pathlib import Path

def setup_logging():
    LOG_DIR = Path('logs')
    LOG_DIR.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_DIR / 'resume_processor.log'),
            logging.StreamHandler()
        ]
    )