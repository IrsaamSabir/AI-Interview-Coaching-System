import sys
from app.utils.pdf_reader   import extract_text
from app.utils.text_cleaner import clean_text
from app.services.nlp_service    import extract_skills, extract_education
from app.services.domain_service import rule_based_domain
from app.services.llm_service    import llm_domain_prediction


def _safe_print(label: str, value: str = "") -> None:
    """Print to console safely - replaces unencodable chars instead of crashing."""
    msg = f"{label}{value}"
    safe = msg.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")
    print(safe)


def analyze_cv(path: str) -> dict:

    # 1 - Extract raw text (paragraphs + tables)
    raw = extract_text(path)
    _safe_print("\n[CV TEXT SAMPLE]\n", raw[:500])   # - was crashing here

    # 2 - Light clean (preserves . - / # +)
    text = clean_text(raw)

    # 3 - Extract skills and education from cleaned text
    skills    = extract_skills(text)
    education = extract_education(text)

    _safe_print(f"\n[Skills found ({len(skills)})]: ", str(skills))
    _safe_print(f"[Education]: ", str(education))

    # 4 - Rule-based domain detection
    domain, confidence, scores = rule_based_domain(skills)

    # 5 - LLM fallback if confidence is too low
    if confidence < 2:
        _safe_print("[Low confidence] - trying LLM domain prediction")
        llm_domain = llm_domain_prediction(skills, education)
        if llm_domain and llm_domain != "Other":
            domain = llm_domain
        else:
            domain = "non_tech"

    _safe_print(f"[Domain]: {domain}  (confidence: {confidence})")

    # 6 - Return clean
    return {
        "skills":    skills,
        "education": education,
        "domain":    domain,
        "message":   _domain_message(domain, skills)
    }


def _domain_message(domain: str, skills: list) -> str:
    if domain == "non_tech":
        return (
            "No tech skills detected in this CV. "
            "This system is designed for software/tech interviews. "
            "Please upload a CV with technical skills."
        )
    if not skills:
        return "Domain detected but skill list is thin. Interview questions will be general."
    return f"CV analysed successfully. Domain: {domain}."
