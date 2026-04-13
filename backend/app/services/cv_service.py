import json
import re
from datetime import datetime
from app.utils.pdf_reader import extract_text
from app.services.llm_service import call_llm


def _build_prompt(cv_text: str) -> str:
    today = datetime.now().strftime("%B %Y")
    return f"""You are a CV parser. First determine if the document is a CV/resume.

A CV/resume typically contains: name, contact info, work experience or education, and skills.
A certificate, transcript, letter, or other document is NOT a CV.

Document:
{cv_text}

If this is NOT a CV/resume, return exactly:
{{"is_cv": false}}

If this IS a CV/resume, return ONLY valid JSON:
{{
  "is_cv": true,
  "skills": ["all technical skills from Skills section, Projects, and Work Experience"],
  "education": "exact degree and field e.g. Bachelors in Computer Science",
  "domain": "infer the main domain from the overall profile e.g. Backend Developer, Data Scientist",
  "years_experience": "Estimate total professional experience in years based on work history. Today is {today}."
}}

Rules:
- For skills, read every section — if a project says 'built with X' or experience says 'used Y', include X and Y.
- Return ONLY the JSON, no extra text."""


def _extract_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return None


def analyze_cv(path: str) -> dict:
    raw      = extract_text(path)
    prompt   = _build_prompt(raw[:3000])
    response = call_llm(prompt=prompt, max_tokens=500)

    raw_response = response.get("raw_response", "")
    print("[CV LLM Response]:", raw_response[:300])

    result = _extract_json(raw_response)
    if not result:
        raise RuntimeError("Failed to parse document. Please upload a valid CV/resume.")

    if not result.get("is_cv", True):
        raise RuntimeError("The uploaded document does not appear to be a CV or resume. Please upload your resume.")

    skills    = [s.lower().strip() for s in result.get("skills", [])]
    education = result.get("education", "Unknown")
    domain    = result.get("domain", "Unknown").strip()
    years     = result.get("years_experience", 0)

    if not skills:
        raise RuntimeError("No skills found in the document. Please upload a proper CV/resume.")

    return {
        "skills":           skills,
        "education":        education,
        "domain":           domain,
        "years_experience": years,
        "message":          f"CV analysed successfully. Domain: {domain}."
    }
