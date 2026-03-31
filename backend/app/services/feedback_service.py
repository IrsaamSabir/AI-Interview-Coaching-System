import json
import re
from app.services.llm_service import call_llm


# -----------------------------------------------------
# JSON extractor  (reused from evaluation_service)
# -----------------------------------------------------
def extract_json(text: str):
    try:
        # Try direct parse first
        return json.loads(text)
    except Exception:
        pass
    try:
        # Find first {...} block (handles extra prose around JSON)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return None


# -----------------------------------------------------
# Build a readable transcript from session answers
# -----------------------------------------------------
def build_transcript(answers: list) -> str:
    lines = []
    for i, entry in enumerate(answers, 1):
        lines.append(f"Q{i}: {entry['question']}")
        lines.append(f"A{i}: {entry['answer']}")
        lines.append(f"Score: {entry['score']}/10  |  Feedback: {entry['feedback']}")
        lines.append("")
    return "\n".join(lines)


# -----------------------------------------------------
# Generate final report via phi3
# -----------------------------------------------------
def generate_report(
    domain: str,
    stack: str,
    skills: list,
    answers: list,
    average_score: float
) -> dict:

    transcript  = build_transcript(answers)
    skills_text = ", ".join(skills) if skills else "general"
    total       = len(answers)

    prompt = f"""You are a senior technical interviewer writing a final evaluation report.

Candidate Domain : {domain}
Tech Stack       : {stack}
Skills Listed    : {skills_text}
Questions Asked  : {total}
Average Score    : {average_score}/10

--- Interview Transcript ---
{transcript}
----------------------------

Write a structured evaluation. Return ONLY valid JSON, no extra text:

{{
  "overall_score": <average score as float>,
  "level": "<Beginner | Intermediate | Advanced | Expert>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>"],
  "skill_scores": {{
    "<skill_name>": <score 0-10>,
    "<skill_name>": <score 0-10>
  }},
  "recommendation": "<one clear hiring recommendation sentence>",
  "summary": "<2-3 sentence overall summary of the candidate>"
}}"""

    print("\n[Generating final report via phi3...]")

    response = call_llm(
        prompt     = prompt,
        model      = "phi3",
        max_tokens = 500       # report needs more tokens than a single answer
    )

    raw = response.get("raw_response", "")
    print("[Raw report response]:", raw[:300])

    result = extract_json(raw)

    if result and _is_valid_report(result):
        # Ensure overall_score matches what we computed
        result["overall_score"] = average_score
        return result

    # -- Fallback: build report from existing scores without LLM --
    print("[LLM report parsing failed] - using rule-based fallback")
    return _fallback_report(domain, stack, skills, answers, average_score)


# -----------------------------------------------------
# Validate the LLM returned a usable report
# -----------------------------------------------------
def _is_valid_report(data: dict) -> bool:
    required = {"overall_score", "level", "strengths",
                "weaknesses", "recommendation", "summary"}
    return required.issubset(data.keys())


# -----------------------------------------------------
# Rule-based fallback if phi3 fails to return valid JSON
# -----------------------------------------------------
def _fallback_report(
    domain: str,
    stack: str,
    skills: list,
    answers: list,
    average_score: float
) -> dict:

    # Determine level
    if average_score >= 8.5:
        level = "Expert"
    elif average_score >= 7:
        level = "Advanced"
    elif average_score >= 5:
        level = "Intermediate"
    else:
        level = "Beginner"

    # Find best and worst answered questions
    sorted_answers = sorted(answers, key=lambda x: x["score"], reverse=True)
    best   = sorted_answers[:2]   if len(sorted_answers) >= 2 else sorted_answers
    worst  = sorted_answers[-2:]  if len(sorted_answers) >= 2 else sorted_answers

    strengths  = [f"Good understanding of: {a['question'][:60]}" for a in best]
    weaknesses = [f"Needs improvement on: {a['question'][:60]}"  for a in worst]

    # Skill scores: assign each skill the average score (we don't track per-skill)
    skill_scores = {skill: round(average_score, 1) for skill in skills[:5]}

    # Recommendation
    if average_score >= 7:
        recommendation = f"Candidate is ready for a {domain} role at {level} level."
    elif average_score >= 5:
        recommendation = f"Candidate shows potential for {domain} but needs more preparation."
    else:
        recommendation = f"Candidate needs significant improvement before a {domain} interview."

    summary = (
        f"The candidate completed a {domain} interview covering {len(answers)} questions "
        f"with an average score of {average_score}/10. "
        f"Overall performance is at {level} level."
    )

    return {
        "overall_score": average_score,
        "level":         level,
        "strengths":     strengths,
        "weaknesses":    weaknesses,
        "skill_scores":  skill_scores,
        "recommendation": recommendation,
        "summary":       summary
    }