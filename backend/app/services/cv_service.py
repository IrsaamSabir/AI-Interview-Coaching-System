import json
import re
from datetime import datetime
from app.utils.pdf_reader import extract_text
from app.utils.experience_calculator import format_experience_label, total_months_from_jobs
from app.services.llm_service import call_llm


def _build_prompt(cv_text: str) -> str:
    today = datetime.now().strftime("%B %Y")
    return f"""You are an expert CV/resume parser for technical hiring.

Reference date for roles ending "Present" or with no end date: {today}

Document text:
{cv_text}

If this is NOT a CV/resume (certificate, transcript, letter, etc.), return only:
{{"is_cv": false}}

If it IS a CV, return ONLY valid JSON (no markdown, no extra text):

{{
  "is_cv": true,
  "skills": ["..."],
  "education": "degree + field or Unknown",
  "domain": "one short inferred role e.g. Backend Developer",
  "jobs": [
    {{"company": "Employer Inc", "start": "MM/YYYY", "end": "MM/YYYY"}},
    {{"company": "Other Co", "start": "03/2024", "end": null}}
  ]
}}

Skills: Extract concrete tools, languages, frameworks, databases, platforms, and technical skills from Skills, Experience, Projects, and certifications. Deduplicate. Max 40 items.

jobs (required):
- One entry per paid role, clearly labeled internship, or explicit freelance engagement with dates in the CV Experience section.
- Use "start" and "end" as strings in MM/YYYY format (e.g. "07/2025", "03/2024"). Leading zeros optional on month.
- If a role is ongoing, set "end" to null (the system uses today's month as the end).
- Do NOT list education-only lines, student projects without employment dates, certifications, or training without real job dates.
- If the candidate has no qualifying jobs, use "jobs": [].

Do NOT return years_experience or total_experience_months; experience length is computed from jobs in code.

Return ONLY the JSON."""


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
    raw = extract_text(path)
    prompt = _build_prompt(raw[:8000])
    response = call_llm(prompt=prompt, max_tokens=1600)

    raw_response = response.get("raw_response", "")
    print("[CV LLM Response]:", raw_response[:300])

    result = _extract_json(raw_response)
    if not result:
        raise RuntimeError("Failed to parse document. Please upload a valid CV/resume.")

    if not result.get("is_cv", True):
        raise RuntimeError("The uploaded document does not appear to be a CV or resume. Please upload your resume.")

    skills = [s.lower().strip() for s in result.get("skills", [])]
    education = result.get("education", "Unknown")
    domain = result.get("domain", "Unknown").strip()
    ref = datetime.now()
    jobs = result.get("jobs")
    total_months: int | None = None
    years_label: str | None = None

    if isinstance(jobs, list):
        computed = total_months_from_jobs(jobs, ref=ref)
        if computed is not None:
            total_months = computed
            years_label = format_experience_label(total_months)

    if total_months is None:
        total_months = result.get("total_experience_months")
        if total_months is not None:
            try:
                total_months = int(total_months)
            except (TypeError, ValueError):
                total_months = None

    if years_label is None:
        years_raw = result.get("years_experience", 0)
        years_label = str(years_raw).strip() if years_raw is not None else ""
        if not years_label and total_months is not None:
            years_label = format_experience_label(total_months)
        if not years_label:
            years_label = "0 months"

    if not skills:
        raise RuntimeError("No skills found in the document. Please upload a proper CV/resume.")

    out = {
        "skills": skills,
        "education": education,
        "domain": domain,
        "years_experience": years_label,
        "message": f"CV analysed successfully. Domain: {domain}.",
    }
    if isinstance(jobs, list):
        out["jobs"] = jobs
    if total_months is not None:
        out["total_experience_months"] = total_months
    return out
