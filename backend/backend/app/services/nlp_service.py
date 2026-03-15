import json
from pathlib import Path

# ---------------- LOAD SKILLS ----------------

BASE_DIR = Path(__file__).resolve().parent.parent
SKILLS_PATH = BASE_DIR / "data" / "skills.json"

with open(SKILLS_PATH, "r", encoding="utf-8") as f:
    SKILLS_DB = json.load(f)


# ---------------- EXTRACT SKILLS SECTION ----------------

def extract_skills_section(text: str):

    text_lower = text.lower()

    start_keywords = ["skills", "technical skills"]
    end_keywords = ["education", "experience", "projects", "courses"]

    start = -1
    end = len(text_lower)

    for keyword in start_keywords:
        idx = text_lower.find(keyword)
        if idx != -1:
            start = idx
            break

    if start == -1:
        return ""

    for keyword in end_keywords:
        idx = text_lower.find(keyword, start)
        if idx != -1:
            end = idx
            break

    return text_lower[start:end]

# ---------------- SKILL EXTRACTION ----------------

def extract_skills(text: str):

    text = text.lower()

    skills_section = extract_skills_section(text)

    found = set()

    # 1️⃣ extract from skills section
    for domain_skills in SKILLS_DB.values():
        for skill in domain_skills:
            if skill.lower() in skills_section:
                found.add(skill.lower())

    # 2️⃣ add additional valid skills from whole CV
    for domain_skills in SKILLS_DB.values():
        for skill in domain_skills:
            if skill.lower() in text:
                found.add(skill.lower())

    return sorted(list(found))

# ---------------- EDUCATION EXTRACTION ----------------

def extract_education(text: str):

    text = text.lower()

    if "phd" in text:
        return "PhD"

    if "master" in text or "msc" in text:
        return "Masters"

    if "bachelor" in text or "bs" in text:
        return "Bachelors"

    return "Unknown"