import json
import re
from datetime import datetime

from src.utils.pdf_reader import extract_text
from src.utils.experience_calculator import format_experience_label, total_months_from_jobs
from src.services.llm_service import call_llm
from src.prompts.cv_prompts import build_cv_parse_prompt


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
    prompt = build_cv_parse_prompt(raw[:8000])
    response = call_llm(prompt=prompt, max_tokens=1600)

    raw_response = response.get("raw_response", "")
    print("[CV LLM Response]:", raw_response[:300])

    result = _extract_json(raw_response)
    if not result:
        raise RuntimeError("Failed to parse document. Please upload a valid CV/resume.")

    if result.get("is_cv") is not True:
        raise RuntimeError("The uploaded document does not appear to be a CV or resume. Please upload your resume.")

    skills    = [s.lower().strip() for s in result.get("skills", [])]
    education = result.get("education", "Unknown")
    domain    = result.get("domain", "Unknown").strip()
    ref       = datetime.now()
    jobs      = result.get("jobs")

    total_months: int | None = None
    years_label: str | None  = None

    if isinstance(jobs, list):
        computed = total_months_from_jobs(jobs, ref=ref)
        if computed is not None:
            total_months = computed
            years_label  = format_experience_label(total_months)

    if total_months is None:
        total_months = result.get("total_experience_months")
        if total_months is not None:
            try:
                total_months = int(total_months)
            except (TypeError, ValueError):
                total_months = None

    if years_label is None:
        years_raw   = result.get("years_experience", 0)
        years_label = str(years_raw).strip() if years_raw is not None else ""
        if not years_label and total_months is not None:
            years_label = format_experience_label(total_months)
        if not years_label:
            years_label = "0 months"

    if len(skills) < 3:
        raise RuntimeError("No skills found in the document. Please upload a proper CV/resume.")

    out = {
        "skills":           skills,
        "education":        education,
        "domain":           domain,
        "years_experience": years_label,
        "message":          f"CV analysed successfully. Domain: {domain}.",
    }
    if isinstance(jobs, list):
        out["jobs"] = jobs
    if total_months is not None:
        out["total_experience_months"] = total_months
    return out
