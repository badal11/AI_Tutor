from typing import List
from domain.models import Question

class QuizSession:
    def __init__(self, questions: List[Question]):
        self.questions = questions
        self.score = 0
        self.current_index = 0

    @property
    def current_question(self) -> Question:
        return self.questions[self.current_index]

    def process_answer(self, user_choice: str) -> bool:
        correct = user_choice.strip().upper() == self.current_question.correct_answer.upper()
        if correct:
            self.score += 1
        return correct

    def next_question(self):
        self.current_index += 1

    def is_complete(self) -> bool:
        return self.current_index >= len(self.questions)