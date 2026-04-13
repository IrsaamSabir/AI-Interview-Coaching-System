from app.services.llm_service import call_llm


def generate_first_question(domain: str, skills: list) -> dict:
    """Generate a warm-up opening question based on domain and skills."""
    skills_text = ", ".join(skills[:6]) if skills else domain

    prompt = f"""You are a senior technical interviewer starting an interview.

Candidate Role: {domain}
Candidate Skills: {skills_text}

Generate ONE warm-up opening question to start the interview.
- Should be a basic concept question to ease the candidate in
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
    prev_question: str,
    prev_answer: str,
    score: float,
    question_count: int,
) -> dict:
    """Generate the next question dynamically based on the previous answer and score."""

    skills_text = ", ".join(skills[:6]) if skills else domain

    # question_count is the number already answered when this is called,
    # so question_count == 1 means we just finished Q1 and are generating Q2.
    if question_count <= 2:
        layer       = "basic"
        instruction = "Ask a slightly deeper follow-up or move to another core concept from the candidate's skills."
    elif score >= 7:
        layer       = "advanced"
        instruction = "The candidate answered well. Ask a more advanced or nuanced question on the same topic or a closely related skill."
    elif score >= 4:
        layer       = "intermediate"
        instruction = "The candidate partially answered. Ask a clarifying or related question to probe their understanding further."
    else:
        layer       = "basic"
        instruction = "The candidate struggled. Pivot to a different skill from their list and ask a simpler foundational question."

    prompt = f"""You are a senior technical interviewer conducting a live interview.

Candidate Role: {domain}
Candidate Skills: {skills_text}

Previous Question: {prev_question}
Candidate Answer: {prev_answer}
Score given: {score}/10

{instruction}

Rules:
- Do NOT repeat or rephrase the previous question
- One question only, no numbering, no explanation
- Clear and concise (10-20 words)

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