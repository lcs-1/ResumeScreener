import time
import requests
import logging

logger = logging.getLogger(__name__)

def test_api_connectivity(api_url, headers, retries=2, backoff=2):
    payload = {
        "model": "amazon.nova-lite-v1:0",
        "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Test connectivity"}],
        "max_tokens": 10
    }
    for attempt in range(retries + 1):
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            logger.info("API connectivity test successful.")
            return True
        except requests.RequestException as e:
            logger.error(f"API connectivity test failed (attempt {attempt + 1}/{retries + 1}): {e}")
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
    return False

def analyze_resume(resume_text, jd_title, jd_requirements, api_url, headers):
    if not resume_text.strip():
        logger.warning("Resume text is empty; skipping analysis.")
        return None

    logger.debug(f"Resume text sample: {resume_text[:500]}")

    prompt = f"""You are an expert resume analysis agent. Follow these steps to analyze the resume against the job description:

Extract:
   - Name: Look for headers or common name formats of the candidate.
   - Years of Experience: Sum durations of roles (estimate if dates are missing).
   - Education: Find highest degree and field (infer from skills if absent, e.g., Java suggests CS degree).
   - Skills: Match to job requirements.
   - Recent Role: Latest job title.
Evaluate:
   - Score fitment (0-10) based on skill/experience match.
Analyze:
   - Strengths: Key matching skills/experiences.
   - Gaps: Missing requirements.
Verify:
   - Ensure all fields are filled (use 'Unknown' only if no inference possible).
   - Skills must be comma-separated.

Job: {jd_title}
Requirements: {jd_requirements}
Resume: {resume_text[:1500]}

Return:
- Candidate Name: [name]
- Years of Experience: [years]
- Education Level: [degree, field]
- Relevant Skills: [skills, comma-separated]
- Most Recent Role: [role]
- Fitment Score: [number]/10
- Strengths: [strengths]
- Gaps/Weaknesses: [gaps]
"""
    payload = {
        "model": "amazon.nova-lite-v1:0",
        "messages": [{"role": "system", "content": "You are a resume analysis expert. Provide responses in the exact format requested, ensuring education level is extracted accurately."}, {"role": "user", "content": prompt}],
        "max_tokens": 250,
        "temperature": 0.5,
        "top_p": 0.9
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        response_json = response.json()
        logger.debug(f"Raw API response: {response_json}")
        if "choices" in response_json and response_json["choices"]:
            return response_json["choices"][0]["message"]["content"].strip()
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
    return None