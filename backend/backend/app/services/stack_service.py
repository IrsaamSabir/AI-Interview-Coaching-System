
# backend/app/services/stack_service.py

PYTHON_BACKEND = ["python", "fastapi", "django", "flask"]
JAVA_BACKEND = ["java", "spring"]
NODE_BACKEND = ["node", "express"]

FRONTEND_STACK = ["react", "javascript", "html", "css", "vue"]
AI_STACK = ["pytorch", "tensorflow", "machine learning", "deep learning", "opencv", "nlp"]
DATA_STACK = ["pandas", "numpy", "matplotlib", "seaborn", "scikit-learn"]

def detect_stack(domain: str, skills: list):

    skills_lower = [s.lower() for s in skills]

    # ---------------- BACKEND ----------------
    if domain.lower() == "backend":

        if any(s in skills_lower for s in PYTHON_BACKEND):
            return "python_backend"

        if any(s in skills_lower for s in JAVA_BACKEND):
            return "java_backend"

        if any(s in skills_lower for s in NODE_BACKEND):
            return "node_backend"

        return "generic_backend"

    # ---------------- FRONTEND ----------------
    if domain.lower() == "frontend":

        if any(s in skills_lower for s in FRONTEND_STACK):
            return "frontend"

        return "generic_frontend"

    # ---------------- AI ----------------
    if domain.lower() == "ai":

        if any(s in skills_lower for s in AI_STACK):
            return "ai_engineer"

        return "generic_ai"

    # ---------------- DATA ----------------
    if domain.lower() == "data":

        if any(s in skills_lower for s in DATA_STACK):
            return "data_scientist"

        return "generic_data"

    # ---------------- FULLSTACK ----------------
    if domain.lower() == "fullstack":

        if any(s in skills_lower for s in PYTHON_BACKEND) and any(s in skills_lower for s in FRONTEND_STACK):
            return "python_fullstack"

        if any(s in skills_lower for s in NODE_BACKEND) and any(s in skills_lower for s in FRONTEND_STACK):
            return "node_fullstack"

        return "generic_fullstack"

    # ---------------- FALLBACK ----------------
    return "generic"