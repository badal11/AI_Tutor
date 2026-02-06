# core/prompts.py
def quiz_prompt(level: int) -> str:
    return (
        "You are a quiz creator. Return ONLY valid JSON. "
        f"Difficulty: Level {level}/10. "
        "Return a JSON array with:\n"
        "{ question, options {A,B,C,D}, correct_answer, explanation }"
    )
