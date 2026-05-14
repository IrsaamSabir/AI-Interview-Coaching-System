MAX_QUESTIONS = 10


class InterviewSession:

    def __init__(
        self,
        domain: str,
        skills: list = None,
        priority_skills: list = None,
        experience_context: str = "",
    ):
        self.domain = domain
        self.skills = skills or []
        self.priority_skills = priority_skills or []
        self.experience_context = (experience_context or "").strip()
        self.current_question = None
        self.question_count   = 0
        self.answers          = []
        self.scores           = []
        self.report           = None

    def set_question(self, q: dict):
        self.current_question = q
        self.question_count  += 1

    def save_answer(self, answer: str, score: float, feedback: str, coaching_metrics: dict | None = None):
        self.answers.append({
            "question": self.current_question["question"],
            "answer":   answer,
            "score":    score,
            "feedback": feedback,
            "layer":    self.current_question.get("layer", "basic"),
            "coaching_metrics": coaching_metrics or {},
        })
        self.scores.append(score)

    def is_completed(self) -> bool:
        return len(self.answers) >= MAX_QUESTIONS

    def answered_count(self) -> int:
        return len(self.answers)

    def remaining_count(self) -> int:
        return max(0, MAX_QUESTIONS - len(self.answers))

    def average_score(self) -> float:
        if not self.scores:
            return 0.0
        return round(sum(self.scores) / len(self.scores), 2)

    def level(self) -> str:
        avg = self.average_score()
        if avg >= 8.5: return "Expert"
        if avg >= 7:   return "Advanced"
        if avg >= 5:   return "Intermediate"
        return "Beginner"

    def get_transcript(self) -> list:
        return self.answers

    def last_answer(self) -> dict | None:
        return self.answers[-1] if self.answers else None
