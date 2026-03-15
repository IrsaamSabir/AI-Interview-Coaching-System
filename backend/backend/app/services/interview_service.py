# backend/app/services/interview_service.py

class InterviewSession:

    def __init__(self, questions: list):
        self.questions = questions
        self.current_index = 0
        self.answers = []
        self.scores = []

    def next_question(self):

        if self.current_index >= len(self.questions):
            return None

        q = self.questions[self.current_index]
        self.current_index += 1

        return q

    def save_answer(self, answer_data):
        self.answers.append(answer_data)

    def save_score(self, score_data):
        self.scores.append(score_data)

    def get_results(self):

        return {
            "answers": self.answers,
            "scores": self.scores
        }