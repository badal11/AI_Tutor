# models.py
from dataclasses import dataclass
from typing import Dict

@dataclass
class Question:
    question: str
    options: Dict[str, str]
    correct_answer: str
    explanation: str