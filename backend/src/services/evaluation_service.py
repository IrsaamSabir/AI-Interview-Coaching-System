import json
import re

from src.services.llm_service import call_llm
from src.prompts.evaluation_prompts import build_evaluation_prompt


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


def _pre_check(question: str, answer: str):
    a = answer.strip()
    if not a:
        return {"score": 0, "feedback": "No answer was provided."}
    word_count = len(a.split())
    if word_count < 8:
        return {"score": 1, "feedback": f"Answer is too short ({word_count} words). Please provide a proper explanation."}
    unique_ratio = len(set(a.lower().split())) / word_count
    if unique_ratio < 0.35 and word_count > 10:
        return {"score": 1, "feedback": "Answer appears repetitive. Please provide a clear explanation."}
    q_words = set(question.lower().split())
    a_words = set(a.lower().split())
    if q_words and (len(q_words & a_words) / len(q_words)) >= 0.85:
        return {"score": 0, "feedback": "Answer mirrors the question too closely. Please explain in your own words."}
    return None


def evaluate_answer(question: str, answer: str) -> dict:
    rejection = _pre_check(question, answer)
    if rejection:
        print(f"[PRE-CHECK] {rejection['feedback']}")
        return rejection

    prompt = build_evaluation_prompt(question, answer)

    response = call_llm(prompt=prompt, max_tokens=150)
    raw      = response.get("raw_response", "")
    print(f"[EVAL] raw: {raw[:200]}")
    result   = extract_json(raw)

    if result and "score" in result and "feedback" in result:
        result["score"] = max(0, min(10, float(result["score"])))
        return result

    return {"score": 5, "feedback": "Answer received but evaluation could not be parsed."}
