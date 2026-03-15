import ollama


# ---------------------------------------------------
# FAST DOMAIN PREDICTION (RULE BASED)
# ---------------------------------------------------

def llm_domain_prediction(skills: list, education: str) -> str:

    skills = [s.lower() for s in skills]

    scores = {
        "AI": 0,
        "Backend": 0,
        "Frontend": 0,
        "Data": 0,
        "Mobile": 0
    }

    ai_keywords = [
        "machine learning", "deep learning", "tensorflow",
        "pytorch", "opencv", "nlp", "transformer",
        "computer vision", "speech recognition"
    ]

    backend_keywords = [
        "django", "flask", "fastapi", "node", "spring",
        "api", "backend", "database"
    ]

    frontend_keywords = [
        "react", "html", "css", "javascript", "vue"
    ]

    data_keywords = [
        "pandas", "numpy", "analytics", "data analysis",
        "sql", "scikit-learn"
    ]

    mobile_keywords = [
        "flutter", "android", "ios", "kotlin", "swift"
    ]

    for skill in skills:

        if skill in ai_keywords:
            scores["AI"] += 2

        if skill in backend_keywords:
            scores["Backend"] += 1

        if skill in frontend_keywords:
            scores["Frontend"] += 1

        if skill in data_keywords:
            scores["Data"] += 1

        if skill in mobile_keywords:
            scores["Mobile"] += 1

    best_domain = max(scores, key=scores.get)

    if scores[best_domain] == 0:
        return "Other"

    return best_domain

# ---------------------------------------------------
# GENERIC OLLAMA CALL (FAST VERSION)
# ---------------------------------------------------

def call_llm(prompt: str, model: str = "phi3", max_tokens: int = 120):
    """
    Generic LLM call using Ollama.
    Optimized for speed.
    """

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.3,
                "num_predict": max_tokens,
                "num_ctx": 2048
            }
        )

        return {
            "raw_response": response["message"]["content"].strip()
        }

    except Exception as e:
        print("⚠️ Ollama Error:", e)
        return {"error": str(e)}