# backend/app/services/evaluation_service.py

from app.services.llm_service import call_gemini

def evaluate_answer(question: str, transcript: str):

    prompt = f"""
    Evaluate this answer.

    Question:
    {question}

    Answer:
    {transcript}

    Score:
    - Technical accuracy (0-10)
    - Depth (0-10)
    - Clarity (0-10)

    Return JSON:
    {{
      "technical": number,
      "depth": number,
      "clarity": number,
      "overall": number,
      "strengths": "...",
      "weaknesses": "..."
    }}
    """

    return call_gemini(prompt)