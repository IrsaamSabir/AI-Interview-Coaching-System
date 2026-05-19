import json
import re

from src.services.llm_service import call_llm
from src.prompts.feedback_prompts import build_feedback_prompt


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
    average_score: float,
) -> dict:
    coaching_metrics = _aggregate_coaching_metrics(answers or [])
    coaching_note    = "These are guidance indicators, not strict grading."

    if not answers:
        fallback = _fallback_report(domain, skills, answers, average_score)
        fallback["coaching_metrics"] = coaching_metrics
        fallback["coaching_note"]    = coaching_note
        return fallback

    skills_text   = ", ".join(skills[:5]) if skills else "general"
    score_summary = ", ".join([f"Q{i+1}:{a['score']}" for i, a in enumerate(answers)])

    qa_lines = []
    for i, a in enumerate(answers):
        qa_lines.append(f"Q{i+1}: {a['question']}")
        qa_lines.append(f"A{i+1}: {a['answer'][:200]}")
        qa_lines.append(f"Score: {a['score']}/10 | Feedback: {a.get('feedback', '')[:120]}")
    qa_text = "\n".join(qa_lines)

    skill_keys   = skills[:5] if skills else ["general"]
    skill_schema = ", ".join([f'"{s}": <0-10>' for s in skill_keys])

    prompt = build_feedback_prompt(
        domain=domain,
        skills_text=skills_text,
        score_summary=score_summary,
        qa_text=qa_text,
        average_score=average_score,
        skill_schema=skill_schema,
    )

    response = call_llm(prompt=prompt, max_tokens=400)
    raw      = response.get("raw_response", "")
    result   = extract_json(raw)

    if result and _is_valid_report(result):
        result["overall_score"] = average_score
        result["skill_scores"]  = _sanitise_skill_scores(
            result.get("skill_scores", {}), average_score
        )
        result["coaching_metrics"] = coaching_metrics
        result["coaching_note"]    = coaching_note
        return result

    print("[LLM report parsing failed] — using rule-based fallback")
    fallback = _fallback_report(domain, skills, answers, average_score)
    fallback["coaching_metrics"] = coaching_metrics
    fallback["coaching_note"]    = coaching_note
    return fallback


def _aggregate_coaching_metrics(answers: list) -> dict:
    face_samples   = []
    speech_samples = []
    emotion_totals = {}

    for item in answers or []:
        coaching = item.get("coaching_metrics") or {}
        face     = coaching.get("face") or {}
        speech   = coaching.get("speech") or {}

        if isinstance(face, dict):
            face_samples.append(face)
        if isinstance(speech, dict):
            speech_samples.append(speech)
            for emo in speech.get("top_emotions", []) or []:
                name = str(emo.get("name", "")).strip().lower()
                try:
                    score = float(emo.get("score", 0))
                except Exception:
                    score = 0.0
                if name:
                    emotion_totals[name] = emotion_totals.get(name, 0.0) + score

    def pct(numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100, 1)

    face_total    = len(face_samples)
    face_detected = sum(1 for f in face_samples if bool(f.get("face_detected")))
    eye_contact   = sum(1 for f in face_samples if bool(f.get("eye_contact")))
    focus         = sum(1 for f in face_samples if not bool(f.get("looking_away")))
    head_center   = sum(1 for f in face_samples if str(f.get("head_pose", "")).lower() == "center")
    eyebrow_raise = sum(1 for f in face_samples if bool(f.get("eyebrow_raise")))
    smile_avg     = round(
        (
            sum(float(f.get("smile_score", 0.0)) for f in face_samples if f.get("smile_score") is not None)
            / face_total
        ) * 100,
        1,
    ) if face_total else 0.0

    speech_total      = len(speech_samples)
    speech_signal_avg = round(
        (
            sum(float(s.get("signal_strength", 0.0)) for s in speech_samples if s.get("signal_strength") is not None)
            / speech_total
        ) * 100,
        1,
    ) if speech_total else 0.0

    top_emotions = sorted(
        (
            {"name": name, "score": round((total / max(1, speech_total)) * 100, 1)}
            for name, total in emotion_totals.items()
        ),
        key=lambda x: x["score"],
        reverse=True,
    )[:5]

    return {
        "face": {
            "sample_count":      face_total,
            "face_detected_pct": pct(face_detected, face_total),
            "eye_contact_pct":   pct(eye_contact, face_total),
            "focus_pct":         pct(focus, face_total),
            "head_center_pct":   pct(head_center, face_total),
            "smile_avg_pct":     smile_avg,
            "eyebrow_raise_pct": pct(eyebrow_raise, face_total),
        },
        "speech": {
            "sample_count":       speech_total,
            "signal_strength_pct": speech_signal_avg,
            "top_emotions":       top_emotions,
        },
    }


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
            "recommendation": "Please complete at least one question to receive a meaningful report.",
            "summary":        "No answers were submitted during this session.",
        }

    sorted_answers = sorted(answers, key=lambda x: x["score"], reverse=True)
    top    = sorted_answers[:2]
    bottom = sorted_answers[-2:]

    strengths    = list({f"Good understanding: {a['question'][:80]}" for a in top})
    weaknesses   = list({f"Needs improvement: {a['question'][:80]}"  for a in bottom})
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
