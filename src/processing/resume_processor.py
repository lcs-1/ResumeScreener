import time
import logging
import pandas as pd
from pathlib import Path
import os

from src.api.client import analyze_resume
from src.processing.file_reader import read_resume_file

logger = logging.getLogger(__name__)

def parse_analysis_to_dict(analysis_text, jd_title):
    default_result = {
        "Candidate Name": "Unknown",
        "Years of Experience": "Unknown",
        "JD Analyzed Against": jd_title,
        "Fitment Score": "N/A",
        "Relevant Skills Matching JD": "Unknown",
        "Education Level": "Not specified",
        "Most Recent Role": "Unknown",
        "Strengths": "Not specified",
        "Gaps/Weaknesses": "Not specified"
    }
    if not analysis_text:
        return default_result

    result = default_result.copy()
    lines = [line.strip() for line in analysis_text.split('\n') if line.strip() and ':' in line]
    for line in lines:
        try:
            key, value = [part.strip() for part in line.split(':', 1)]
            if "Candidate Name" in key:
                result["Candidate Name"] = value
            elif "Years of Experience" in key:
                result["Years of Experience"] = value
            elif "Education Level" in key:
                result["Education Level"] = value if value.lower() != "n/a" and value else "Not specified"
            elif "Relevant Skills" in key:
                result["Relevant Skills Matching JD"] = value
            elif "Most Recent Role" in key:
                result["Most Recent Role"] = value
            elif "Fitment Score" in key:
                result["Fitment Score"] = value
            elif "Strengths" in key:
                result["Strengths"] = value if value.lower() != "n/a" and value else "Not specified"
            elif "Gaps/Weaknesses" in key:
                result["Gaps/Weaknesses"] = value if value.lower() != "n/a" and value else "Not specified"
        except ValueError:
            logger.debug(f"Skipping malformed line: {line}")
    return result

def process_resumes(uploaded_files, selected_jd, job_descriptions, api_url, headers, max_file_size_mb, request_delay):
    results = []
    jd_title = job_descriptions[selected_jd]["title"]
    jd_requirements = job_descriptions[selected_jd]["requirements"]

    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.read()
        file_path = Path(uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        logger.info(f"Processing {file_path.name} against {jd_title}...")
        resume_text = read_resume_file(file_path, max_file_size_mb)
        if resume_text:
            analysis = analyze_resume(resume_text, jd_title, jd_requirements, api_url, headers)
            if analysis:
                parsed_data = parse_analysis_to_dict(analysis, jd_title)
                parsed_data["File Name"] = file_path.name
                results.append(parsed_data)
                logger.info(f"Successfully analyzed {file_path.name} for {jd_title}")
            else:
                logger.warning(f"Failed to analyze {file_path.name} for {jd_title}")
        time.sleep(request_delay)
        os.remove(file_path)  # Clean up temporary file

    if results:
        df = pd.DataFrame(results)
        fieldnames = ["File Name", "Candidate Name", "Years of Experience", "JD Analyzed Against", 
                      "Fitment Score", "Relevant Skills Matching JD", "Education Level", 
                      "Most Recent Role", "Strengths", "Gaps/Weaknesses"]
        df = df[fieldnames]
        return df
    return None