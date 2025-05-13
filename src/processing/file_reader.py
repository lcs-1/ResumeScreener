from pathlib import Path
import logging
import pdfplumber
from docx import Document

logger = logging.getLogger(__name__)

def read_resume_file(file_path, max_file_size_mb):
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_file_size_mb:
        logger.warning(f"File {file_path} exceeds max size ({file_size_mb:.2f}MB > {max_file_size_mb}MB).")
        return None

    if suffix == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read() if file.read().strip() else None
        except Exception as e:
            logger.error(f"Error reading TXT {file_path}: {e}")
            return None
    elif suffix == '.pdf':
        try:
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                logger.debug(f"Extracted PDF text sample: {text[:500]}")
                return text if text.strip() else None
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return None
    elif suffix == '.docx':
        try:
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            logger.debug(f"Extracted DOCX text sample: {text[:500]}")
            return text if text.strip() else None
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {e}")
            return None
    logger.warning(f"Unsupported file format: {file_path}")
    return None