import json
from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent.parent
SKILLS_PATH = BASE_DIR / "data" / "skills.json"

with open(SKILLS_PATH, "r", encoding="utf-8") as f:
    SKILLS_DB = json.load(f)

# Higher weight = more domain-specific signal
DOMAIN_WEIGHTS = {
    "ai_ml":          3,
    "cybersecurity":  1,
    "data":           2,
    "devops_cloud":   2,
    "mobile":         2,
    "backend":        2,
    "frontend":       2,
    "fullstack":      2,
}

def rule_based_domain(skills: list):
    scores = {domain: 0 for domain in SKILLS_DB}
    skills_lower = [s.lower() for s in skills]

    # Compute scores per domain
    for skill in skills_lower:
        for domain, domain_skills in SKILLS_DB.items():
            if domain == "fullstack":  # ignore fullstack in raw scoring
                continue
            if skill in [s.lower() for s in domain_skills]:
                scores[domain] += DOMAIN_WEIGHTS.get(domain, 1)

    print("DOMAIN SCORES:", scores)

    # Determine top domain(s)
    sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_domain, best_score = sorted_domains[0]

    # Derive fullstack only if backend + frontend BOTH are strong
    backend_score = scores.get("backend", 0)
    frontend_score = scores.get("frontend", 0)
    FULLSTACK_THRESHOLD = 5  # increase threshold to avoid false positives
    if backend_score >= FULLSTACK_THRESHOLD and frontend_score >= FULLSTACK_THRESHOLD:
        return "fullstack", backend_score + frontend_score, scores

    return best_domain, best_score, scores