def build_feedback_prompt(
    domain: str,
    skills_text: str,
    score_summary: str,
    qa_text: str,
    average_score: float,
    skill_schema: str,
) -> str:
    return f"""You are a technical interviewer. Write a concise evaluation report.

Domain: {domain} | Average Score: {average_score}/10
Skills assessed: {skills_text}
Score breakdown: {score_summary}

Interview transcript:
{qa_text}

Return ONLY valid JSON with no extra text:
{{
  "level": "<Beginner|Intermediate|Advanced|Expert>",
  "strengths": ["<specific strength from the answers>", "<specific strength>"],
  "weaknesses": ["<specific weakness from the answers>", "<specific weakness>"],
  "skill_scores": {{{skill_schema}}},
  "recommendation": "<one actionable sentence>",
  "summary": "<2 sentences summarising overall performance>"
}}"""
