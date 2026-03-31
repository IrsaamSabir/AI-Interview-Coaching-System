import json
import re
from app.services.llm_service import call_llm


# -------------------------------------------------
# JSON extractor
# -------------------------------------------------
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


# -------------------------------------------------
# Pre-check: catch bad answers BEFORE calling phi3
# Returns a rejection dict or None if answer is ok
# -------------------------------------------------
def _pre_check(question: str, answer: str) -> dict | None:

    q = question.strip().lower()
    a = answer.strip().lower()

    # 1. Empty or whitespace only
    if not a:
        return {
            "score": 0,
            "feedback": "No answer was provided."
        }

    # 2. Answer is too short (less than 8 words)
    word_count = len(answer.strip().split())
    if word_count < 8:
        return {
            "score": 1,
            "feedback": (
                f"Answer is too short ({word_count} words). "
                "Please provide a proper explanation with at least a few sentences."
            )
        }

    # 3. Answer is identical or nearly identical to the question
    q_words = set(q.split())
    a_words = set(a.split())
    if q_words and len(q_words) > 0:
        overlap = len(q_words & a_words) / len(q_words)
        if overlap >= 0.85 and word_count <= len(q.split()) + 3:
            return {
                "score": 0,
                "feedback": (
                    "Your answer appears to be a copy of the question. "
                    "Please explain the concept in your own words."
                )
            }

    # 4. Answer is a single repeated word / gibberish
    unique_words = set(a.split())
    if len(unique_words) <= 2 and word_count >= 5:
        return {
            "score": 1,
            "feedback": "Answer does not contain meaningful content. Please try again."
        }

    return None  # answer passed all checks - send to phi3


# -------------------------------------------------
# Main evaluation function
# -------------------------------------------------
def evaluate_answer(question: str, answer: str) -> dict:

    # Run pre-check first - no LLM call wasted on bad input
    rejection = _pre_check(question, answer)
    if rejection:
        print(f"[PRE-CHECK] Rejected answer: {rejection['feedback']}")
        return rejection

    # Build a strict evaluation prompt
    prompt = f"""You are a strict senior software engineering interviewer.

Question:
{question}

Candidate Answer:
{answer}

Evaluate strictly. A good answer must:
- Directly address the question
- Show actual technical understanding
- Contain specific details, not just keywords

Penalise heavily if the answer:
- Just repeats the question words
- Is vague with no technical depth
- Shows no real understanding

Return ONLY this JSON, nothing else:

{{
"score": <integer 0 to 10>,
"feedback": "<2 sentences: what was good and what was missing>"
}}"""

    response = call_llm(prompt=prompt, model="phi3", max_tokens=150)
    raw      = response.get("raw_response", "")
    result   = extract_json(raw)

    if result and "score" in result and "feedback" in result:
        # Clamp score to valid range
        result["score"] = max(0, min(10, float(result["score"])))
        return result

    # Fallback if phi3 returns unparseable response
    return {
        "score":    5,
        "feedback": "Answer received but evaluation could not be parsed."
    }