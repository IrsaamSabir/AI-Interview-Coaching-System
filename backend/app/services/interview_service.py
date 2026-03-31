class InterviewSession:

    def __init__(self, questions: list, domain: str, stack: str, skills: list = None):
        self.questions     = questions     # list of {"layer": ..., "question": ...}
        self.domain        = domain
        self.stack         = stack
        self.skills        = skills or []  # original CV skills - used in report
        self.current_index = 0
        self.answers       = []            # {"question", "answer", "score", "feedback"}
        self.scores        = []            # float scores
        self.report        = None          # cached final report once generated

    # -- Current question (no advance) -------------
    def current_question(self) -> dict | None:
        if self.current_index >= len(self.questions):
            return None
        return self.questions[self.current_index]

    # -- Advance pointer after answer saved --------
    def advance(self):
        self.current_index += 1

    # -- Save evaluated answer ---------------------
    def save_answer(self, question: str, answer: str, score: float, feedback: str):
        self.answers.append({
            "question": question,
            "answer":   answer,
            "score":    score,
            "feedback": feedback
        })
        self.scores.append(score)

    # -- Completion check --------------------------
    def is_completed(self) -> bool:
        return len(self.answers) >= len(self.questions)

    # -- Progress helpers --------------------------
    def answered_count(self) -> int:
        return len(self.answers)

    def remaining_count(self) -> int:
        return len(self.questions) - len(self.answers)

    # -- Average score -----------------------------
    def average_score(self) -> float:
        if not self.scores:
            return 0.0
        return round(sum(self.scores) / len(self.scores), 2)

    # -- Level from average score ------------------
    def level(self) -> str:
        avg = self.average_score()
        if avg >= 8.5:
            return "Expert"
        elif avg >= 7:
            return "Advanced"
        elif avg >= 5:
            return "Intermediate"
        return "Beginner"

    # -- Full transcript for report generation -----
    def get_transcript(self) -> list:
        return self.answers

    # -- Raw results dict (used by /status) --------
    def get_results(self) -> dict:
        return {
            "domain":          self.domain,
            "stack":           self.stack,
            "skills":          self.skills,
            "total_questions": len(self.questions),
            "answered":        len(self.answers),
            "average_score":   self.average_score(),
            "level":           self.level(),
            "status":          "completed" if self.is_completed() else "in_progress",
            "answers":         self.answers,
            "scores":          self.scores
        }