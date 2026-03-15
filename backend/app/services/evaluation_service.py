import json
import re
from app.services.llm_service import call_llm


def extract_json(text: str):
    """
    Extract JSON object from LLM response safely
    """
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass

    return None


def evaluate_answer(question: str, answer: str):

    prompt = f"""
You are a senior software engineering interviewer.

Question:
{question}

Candidate Answer:
{answer}

Evaluate the answer.

Return ONLY JSON like this:

{{
"score": number between 0 and 10,
"feedback": "short explanation"
}}
"""

    response = call_llm(
        prompt=prompt,
        model="phi3",
        max_tokens=150
    )

    raw = response.get("raw_response", "")

    result = extract_json(raw)

    if result:
        return result

    return {
        "score": 5,
        "feedback": "Answer received but evaluation parsing failed."
    }