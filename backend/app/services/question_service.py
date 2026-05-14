from app.services.llm_service import call_llm


def _skill_context(skills: list, priority_skills: list | None = None) -> tuple[str, str]:
    base_skills = skills or []
    priority = priority_skills or []
    skills_text = ", ".join(base_skills[:6]) if base_skills else ""
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
    priority_block = f"Priority Skills To Focus More On: {priority_text}\n" if priority_text else ""
    exp_block = _experience_block(experience_context)

    prompt = f"""You are a senior technical interviewer starting an interview.

Candidate Role: {domain}
Candidate Skills: {displayed_skills}
{priority_block}{exp_block}
Generate ONE warm-up opening question to start the interview.
- Should be a basic concept question to ease the candidate in
- Prefer starting from the priority skills if they are relevant
- Match difficulty to their experience level (e.g. shorter tenure: foundational; longer tenure: still warm-up but can assume they have shipped real work)
- Clear and concise (10-20 words)
- No numbering, no explanation, just the question

Output: one question only"""

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
    priority_block = f"Priority Skills To Focus More On: {priority_text}\n" if priority_text else ""
    exp_block = _experience_block(experience_context)

    # question_count is the number already answered when this is called,
    # so question_count == 1 means we just finished Q1 and are generating Q2.
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

    prompt = f"""You are a senior technical interviewer conducting a live interview.

Candidate Role: {domain}
Candidate Skills: {displayed_skills}
{priority_block}{exp_block}
Previous Question: {prev_question}
Candidate Answer: {prev_answer}
Score given: {score}/10

{instruction}

Rules:
- Do NOT repeat or rephrase the previous question
- One question only, no numbering, no explanation
- Clear and concise (10-20 words)
- Where appropriate, ask in a way that fits someone with their stated experience (depth and expectations), without quoting dates back to them

Output: one question only"""

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