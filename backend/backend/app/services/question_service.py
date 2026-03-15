from app.services.llm_service import call_llm


def generate_multi_layer_questions(stack: str, top_skills: list):

    if not top_skills:

        return [
            {"layer": "core", "question": "Explain object oriented programming."},
            {"layer": "core", "question": "What is REST API?"},
            {"layer": "core", "question": "What is version control?"},
            {"layer": "core", "question": "What is Git?"},
            {"layer": "core", "question": "Explain MVC architecture."},
            {"layer": "core", "question": "What is debugging?"}
        ]

    skills_text = ", ".join(top_skills)

    prompt = f"""
Generate 6 technical interview questions.

Candidate Role: {stack}
Candidate Skills: {skills_text}

Rules:
- Questions must relate to the role
- Maximum 10 words
- One question per line
- No numbering
- No explanation
"""

    response = call_llm(prompt, model="phi3", max_tokens=120)

    print("LLM RESPONSE:", response)

    if "raw_response" not in response:
        return []

    text = response["raw_response"]

    questions = []

    for line in text.split("\n"):

        q = line.strip()

        if len(q) < 6:
            continue

        q = q.replace("-", "").replace("*", "").strip()

        questions.append({
            "layer": "core",
            "question": q
        })

        if len(questions) == 6:
            break

    return questions