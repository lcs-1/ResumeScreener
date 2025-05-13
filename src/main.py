import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))  # Adds C:\stealth\Resume_Screener to sys.path

from src.utils.logger import setup_logging
from src.config.config_loader import load_config
from src.models.job_descriptions import JOB_DESCRIPTIONS
from src.ui.app import run_ui
from src.api.client import test_api_connectivity, analyze_resume
from src.processing.file_reader import read_resume_file
from src.processing.resume_processor import process_resumes

if __name__ == "__main__":
    setup_logging()
    api_config, processing_config = load_config()
    run_ui(
        JOB_DESCRIPTIONS,
        process_resumes,
        test_api_connectivity,
        api_config,
        processing_config
    )