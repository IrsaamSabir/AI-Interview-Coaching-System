# app/services/cv_parse.py

from app.utils.pdf_reader import extract_text
from app.utils.text_cleaner import clean_text

from app.services.nlp_service import (
    extract_skills,
    extract_education
)

from app.services.domain_service import rule_based_domain
from app.services.llm_service import llm_domain_prediction


def analyze_cv(path):

    # ---------------- EXTRACT RAW TEXT ----------------
    raw = extract_text(path)

    print("\n📄 CV TEXT SAMPLE:")
    print(raw[:500])

    # ---------------- CLEAN TEXT ----------------
    text = clean_text(raw)
    text_lower = text.lower()

    # ---------------- SKILLS & EDUCATION ----------------
    skills = extract_skills(text_lower)
    education = extract_education(text_lower)

    # ---------------- DOMAIN (RULE BASED FIRST) ----------------
    domain, confidence = rule_based_domain(skills)

    # ---------------- LLM FALLBACK ----------------
    if confidence < 3:
        domain = llm_domain_prediction(skills, education)

    return {
        "skills": skills,
        "education": education,
        "domain": domain
    }