# core/prompts.py
def map_level_to_difficulty(level: int) -> str:
    """
    Converts a numeric level (1-10) to a descriptive difficulty string
    that the model can understand.
    """
    if level < 1:
        level = 1
    elif level > 10:
        level = 10

    difficulty_map = {
        1: "very basic recall question, suitable for beginners",
        2: "simple question, tests fundamental understanding",
        3: "slightly challenging question requiring basic reasoning",
        4: "moderate difficulty, requires understanding and application",
        5: "medium-level question with multi-step reasoning",
        6: "moderately hard, involves combining multiple concepts",
        7: "hard question, requires analytical thinking",
        8: "very hard, challenging problem requiring deep understanding",
        9: "extremely hard, multi-step reasoning and complex problem-solving",
        10: "expert-level question, requires advanced knowledge and critical thinking"
    }
    return difficulty_map[level]

def quiz_system_prompt(topic: str, level: int) -> str:
    """
    Returns a system prompt for generating quiz questions for a given topic and numeric level.
    The level is converted to a descriptive word for the LLM.
    """
    difficulty = map_level_to_difficulty(level)

    return (
        f"You are a quiz creator. Generate multiple-choice questions about the topic: '{topic}'. "
        f"Make the questions {difficulty}. "
        "Return ONLY valid JSON. Return a JSON ARRAY of multiple-choice questions. "
        "Format:\n"
        "{\n"
        "  \"question\": \"...\",\n"
        "  \"options\": {\"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\"},\n"
        "  \"correct_answer\": \"A\",\n"
        "  \"explanation\": \"...\"\n"
        "}\n"
        "Do NOT return a single object. Do NOT add any extra text."
    )