from src.services.llm_service import call_llm
from src.prompts.question_prompts import build_first_question_prompt, build_next_question_prompt


def _skill_context(skills: list, priority_skills: list | None = None) -> tuple[str, str]:
    base_skills   = skills or []
    priority      = priority_skills or []
    skills_text   = ", ".join(base_skills[:6]) if base_skills else ""
    priority_text = ", ".join(priority[:5]) if priority else ""
    return skills_text, priority_text


def _experience_block(experience_context: str | None) -> str:
    text = (experience_context or "").strip()
    if not text:
        return ""
    return f"""Candidate background (use to calibrate depth and realism; do not ask them to recite dates):
{text}

"""


def generate_first_question(
    domain: str,
    skills: list,
    priority_skills: list | None = None,
    experience_context: str | None = None,
) -> dict:
    """Generate a warm-up opening question based on domain and skills."""
    skills_text, priority_text = _skill_context(skills, priority_skills)
    displayed_skills = skills_text or domain
    priority_block   = f"Priority Skills To Focus More On: {priority_text}\n" if priority_text else ""
    exp_block        = _experience_block(experience_context)

    prompt = build_first_question_prompt(
        domain=domain,
        displayed_skills=displayed_skills,
        priority_block=priority_block,
        exp_block=exp_block,
    )

    response = call_llm(prompt=prompt, max_tokens=80)
    raw      = response.get("raw_response", "").strip()
    question = _clean_question(raw)

    return {"question": question, "layer": "basic"}


def generate_next_question(
    domain: str,
    skills: list,
    priority_skills: list | None,
    prev_question: str,
    prev_answer: str,
    score: float,
    question_count: int,
    experience_context: str | None = None,
) -> dict:
    """Generate the next question dynamically based on the previous answer and score."""
    skills_text, priority_text = _skill_context(skills, priority_skills)
    displayed_skills = skills_text or domain
    priority_block   = f"Priority Skills To Focus More On: {priority_text}\n" if priority_text else ""
    exp_block        = _experience_block(experience_context)

    if question_count <= 2:
        layer       = "basic"
        instruction = "Ask a slightly deeper follow-up or move to another core concept from the candidate's skills, preferring priority skills when appropriate."
    elif score >= 7:
        layer       = "advanced"
        instruction = "The candidate answered well. Ask a more advanced or nuanced question on the same topic or a closely related skill, with extra focus on priority skills when appropriate."
    elif score >= 4:
        layer       = "intermediate"
        instruction = "The candidate partially answered. Ask a clarifying or related question to probe their understanding further, preferring priority skills when appropriate."
    else:
        layer       = "basic"
        instruction = "The candidate struggled. Pivot to a different skill from their list and ask a simpler foundational question, preferring priority skills when appropriate."

    prompt = build_next_question_prompt(
        domain=domain,
        displayed_skills=displayed_skills,
        priority_block=priority_block,
        exp_block=exp_block,
        prev_question=prev_question,
        prev_answer=prev_answer,
        score=score,
        instruction=instruction,
    )

    response = call_llm(prompt=prompt, max_tokens=80)
    raw      = response.get("raw_response", "").strip()
    question = _clean_question(raw)

    return {"question": question, "layer": layer}


def _clean_question(text: str) -> str:
    """Strip numbering, bullets, and surrounding quotes from LLM output."""
    text = text.strip().strip('"').strip("'")
    text = text.lstrip("0123456789.-) ").strip()
    text = text.replace("**", "").strip()
    if text.startswith("-"):
        text = text[1:].strip()
    return text if len(text) > 6 else "Can you walk me through a core concept from your primary skill?"
