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

    prompt = (
        "You are a fair and practical technical interviewer evaluating a candidate's live answer.\n\n"

f"Question: {question}\n\n"
f"Candidate Answer: {answer}\n\n"

"Scoring rubric (be slightly lenient and realistic):\n"
"  0-2: No understanding or completely incorrect\n"
"  3-5: Basic attempt, some relevant ideas but mostly unclear or incorrect\n"
"  6-7: Acceptable answer, generally correct but missing clarity, depth, or examples\n"
"  7-8: Good answer, correct with reasonable explanation or examples\n"
"  9-10: Strong answer, clear, confident, and shows practical understanding\n\n"

"Evaluation guidelines:\n"
"- Focus on the main concept asked in the question\n"
"- Do NOT expect perfect or textbook definitions\n"
"- Reward partial understanding if the core idea is correct\n"
"- Do NOT penalize for minor mistakes, wording issues, or missing edge cases\n"
"- Be forgiving if the answer is practical but not deeply theoretical\n\n"

"Feedback style:\n"
"- First mention what the candidate did correctly\n"
"- Then briefly mention what could be improved\n"
"- Keep feedback concise and constructive\n\n"

'Return ONLY this JSON:\n{"score": <integer 0-10>, "feedback": "<short constructive feedback>"}'
    )

    response = call_llm(prompt=prompt, max_tokens=150)
    raw      = response.get("raw_response", "")
    print(f"[EVAL] raw: {raw[:200]}")
    result   = extract_json(raw)

    if result and "score" in result and "feedback" in result:
        result["score"] = max(0, min(10, float(result["score"])))
        return result

    return {"score": 5, "feedback": "Answer received but evaluation could not be parsed."}
