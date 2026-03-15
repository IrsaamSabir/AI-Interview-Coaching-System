# backend/app/services/interview_service.py


class InterviewSession:

    def __init__(self, questions: list):
        self.questions = questions
        self.current_index = 0
        self.answers = []
        self.scores = []

    # ----------------------------------------
    # Get next question
    # ----------------------------------------
    def next_question(self):

        if self.current_index >= len(self.questions):
            return None

        question = self.questions[self.current_index]
        self.current_index += 1

        return question

    # ----------------------------------------
    # Save candidate answer
    # ----------------------------------------
    def save_answer(self, answer_data):

        self.answers.append(answer_data)

    # ----------------------------------------
    # Save evaluation score
    # ----------------------------------------
    def save_score(self, score_data):

        self.scores.append(score_data)

    # ----------------------------------------
    # Check if interview finished
    # ----------------------------------------
    def is_completed(self):

        return len(self.answers) >= len(self.questions)

    # ----------------------------------------
    # Calculate average score
    # ----------------------------------------
    def average_score(self):

        if not self.scores:
            return 0

        return round(sum(self.scores) / len(self.scores), 2)

    # ----------------------------------------
    # Final interview results
    # ----------------------------------------
    def get_results(self):

        avg_score = self.average_score()

        if avg_score >= 8:
            level = "Advanced"
        elif avg_score >= 6:
            level = "Intermediate"
        elif avg_score >= 4:
            level = "Beginner"
        else:
            level = "Needs Improvement"

        return {
            "total_questions": len(self.questions),
            "answered_questions": len(self.answers),
            "average_score": avg_score,
            "level": level,
            "answers": self.answers,
            "scores": self.scores
        }