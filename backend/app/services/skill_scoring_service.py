# backend/app/services/skill_scoring_service.py

def score_skills(skills: list, domain: str):

    scored = []

    for skill in skills:

        score = 0

        # Base weight
        score += 1

        # Domain relevance weight
        if domain.lower() in skill.lower():
            score += 2

        # Backend important skills
        if skill.lower() in ["python", "fastapi", "django", "postgresql"]:
            score += 3

        scored.append({
            "skill": skill,
            "score": score
        })

    # Sort descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    return scored