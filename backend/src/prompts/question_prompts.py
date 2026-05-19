def build_first_question_prompt(
    domain: str,
    displayed_skills: str,
    priority_block: str,
    exp_block: str,
) -> str:
    return f"""You are a senior technical interviewer starting an interview.

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


def build_next_question_prompt(
    domain: str,
    displayed_skills: str,
    priority_block: str,
    exp_block: str,
    prev_question: str,
    prev_answer: str,
    score: float,
    instruction: str,
) -> str:
    return f"""You are a senior technical interviewer conducting a live interview.

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
