import json
import re
from app.services.llm_service import call_llm


def extract_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return None


def generate_report(
    domain: str,
    skills: list,
    answers: list,
    average_score: float
) -> dict:

    if not answers:
        return _fallback_report(domain, skills, answers, average_score)

    skills_text   = ", ".join(skills[:5]) if skills else "general"
    score_summary = ", ".join([f"Q{i+1}:{a['score']}" for i, a in enumerate(answers)])

    # Build per-answer context so the LLM can make meaningful strengths/weaknesses
    qa_lines = []
    for i, a in enumerate(answers):
        qa_lines.append(f"Q{i+1}: {a['question']}")
        qa_lines.append(f"A{i+1}: {a['answer'][:200]}")
        qa_lines.append(f"Score: {a['score']}/10 | Feedback: {a.get('feedback', '')[:120]}")
    qa_text = "\n".join(qa_lines)

    # Build skill_scores template — one entry per skill so LLM fills real values
    skill_keys   = skills[:5] if skills else ["general"]
    skill_schema = ", ".join([f'"{s}": <0-10>' for s in skill_keys])

    prompt = f"""You are a technical interviewer. Write a concise evaluation report.

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

    response = call_llm(prompt=prompt, max_tokens=400)
    raw      = response.get("raw_response", "")
    result   = extract_json(raw)

    if result and _is_valid_report(result):
        result["overall_score"] = average_score
        # Ensure skill_scores only contains numeric values
        result["skill_scores"] = _sanitise_skill_scores(
            result.get("skill_scores", {}), average_score
        )
        return result

    print("[LLM report parsing failed] — using rule-based fallback")
    return _fallback_report(domain, skills, answers, average_score)


def _is_valid_report(data: dict) -> bool:
    required = {"level", "strengths", "weaknesses", "skill_scores", "recommendation", "summary"}
    if not required.issubset(data.keys()):
        return False
    if not isinstance(data["strengths"], list) or not data["strengths"]:
        return False
    if not isinstance(data["weaknesses"], list) or not data["weaknesses"]:
        return False
    return True


def _sanitise_skill_scores(raw: dict, fallback: float) -> dict:
    """Ensure every value in skill_scores is a plain float between 0 and 10."""
    cleaned = {}
    for k, v in raw.items():
        try:
            cleaned[k] = round(min(10.0, max(0.0, float(v))), 1)
        except (TypeError, ValueError):
            cleaned[k] = round(fallback, 1)
    return cleaned


def _fallback_report(domain: str, skills: list, answers: list, average_score: float) -> dict:
    if average_score >= 8.5:
        level = "Expert"
    elif average_score >= 7:
        level = "Advanced"
    elif average_score >= 5:
        level = "Intermediate"
    else:
        level = "Beginner"

    if not answers:
        return {
            "overall_score":  average_score,
            "level":          level,
            "strengths":      ["Interview not completed — no data available."],
            "weaknesses":     ["Interview not completed — no data available."],
            "skill_scores":   {s: round(average_score, 1) for s in (skills[:5] or ["general"])},
            "recommendation": f"Please complete at least one question to receive a meaningful report.",
            "summary":        "No answers were submitted during this session.",
        }

    sorted_answers = sorted(answers, key=lambda x: x["score"], reverse=True)

    top    = sorted_answers[:2]
    bottom = sorted_answers[-2:]

    strengths  = list({f"Good understanding: {a['question'][:80]}" for a in top})
    weaknesses = list({f"Needs improvement: {a['question'][:80]}"  for a in bottom})
    skill_scores = {s: round(average_score, 1) for s in (skills[:5] or ["general"])}

    if average_score >= 7:
        recommendation = f"Candidate is ready for a {domain} role at {level} level."
    elif average_score >= 5:
        recommendation = f"Candidate shows potential for {domain} but needs further preparation."
    else:
        recommendation = f"Candidate needs significant improvement before a {domain} interview."

    summary = (
        f"The candidate completed a {domain} interview covering {len(answers)} question(s) "
        f"with an average score of {average_score}/10. "
        f"Overall performance is at {level} level."
    )

    return {
        "overall_score":  average_score,
        "level":          level,
        "strengths":      strengths,
        "weaknesses":     weaknesses,
        "skill_scores":   skill_scores,
        "recommendation": recommendation,
        "summary":        summary,
    }