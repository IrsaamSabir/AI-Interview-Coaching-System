import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SKILLS_PATH = BASE_DIR / "data" / "skills.json"

with open(SKILLS_PATH, "r", encoding="utf-8") as f:
    SKILLS_DB = json.load(f)


def rule_based_domain(skills):

    scores = {domain: 0 for domain in SKILLS_DB}

    weights = {
        "ai": 3,
        "data": 2,
        "backend": 1,
        "frontend": 1,
        "mobile": 1
    }

    for skill in skills:

        for domain, domain_skills in SKILLS_DB.items():

            if skill in domain_skills:

                scores[domain] += weights.get(domain, 1)

    print("DOMAIN SCORES:", scores)

    best_domain = max(scores, key=scores.get)
    confidence = scores[best_domain]

    # Detect full stack
    if scores.get("frontend", 0) >= 2 and scores.get("backend", 0) >= 2:
        best_domain = "fullstack"

    return best_domain, confidence