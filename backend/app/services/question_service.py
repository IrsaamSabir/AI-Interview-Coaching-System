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
You are an expert technical interviewer.

Generate 6 high-quality technical interview questions.

Candidate Role: {stack}
Candidate Skills: {skills_text}

Strict Guidelines:

Questions must directly test core concepts and fundamental understanding of the given skills
Focus on logic, reasoning, and how things work internally
Avoid debugging, system design, and real-world scenario-based questions
Avoid generic prompts like "define" or "explain"
Questions should require thinking, not memorization
Keep questions clear, specific, and concept-focused

Output Rules:

One question per line
No numbering
No explanations
Each question must be concise (10-20 words)
Ensure questions feel like real interview conceptual questions
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