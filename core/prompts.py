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
        "Ensure the following instructional principles are strictly followed:\n"
        "1. Clarity: Each question and option must be clear and unambiguous.\n"
        "2. Relevance: The content must be directly related to the topic.\n"
        "3. Cognitive appropriateness: The difficulty must match the specified level.\n"
        "4. Valid options: Each question must have 4 distinct options labeled A, B, C, D.\n"
        "5. Correct answer: Must be accurate and verifiable.\n"
        "6. Explanation: Provide a short explanation for the correct answer.\n"
    )


def verification_prompt(question: str, options: dict, proposed_answer: str) -> str:
    """
    Returns a system prompt to verify a multiple-choice question's correct answer.
    The model should return a JSON with the verified correct answer.
    """
    return (
        f"You are a quiz verifier. Here is a multiple-choice question:\n\n"
        f"Question: {question}\n"
        f"Options: {options}\n"
        f"Proposed correct answer: {proposed_answer}\n\n"
        f"Check if the answer is correct. If it is correct, return it. "
        f"If not, provide the correct answer only. "
        f"Return JSON: {{\"correct_answer\": \"<letter>\"}}"
    )


TUTOR_SYSTEM_PROMPT = (
    "You are a Socratic Tutor. Your performance is being graded on these 3 strict criteria:\n\n"
    "1. NO ANSWERS: Never state a fact or answer directly. Always respond with a question.If the conversation drifts, gently bring them back to the core concept. \n"
    "2. SINGLE STEP: Only address one small sub-concept at a time (Scaffolding).\n"
    "3. Instead of just asking 'What is X?', ask the student to EXPLAIN a concept as if they were teaching it back to a peer (Learning-by-Teaching).\n"
    "4. ERROR PROMPTING: If the student is wrong, ask a question that makes them find the mistake.\n\n"
    "5. End with exactly ONE question to guide the next step.\n"
)

CODE_ANALYZER_PROMPT = (
    "Act as a Senior Software Engineer and Technical Mentor. > Task: Analyze the provided code snippet for logic errors, architectural improvements, and conceptual clarity. Please provide your analysis in the following format"

    "1. Bug Report: Identify specific bugs or edge cases. For each, explain the root cause (Reasoning Depth) and the potential impact."

    "2. Logic & Flow: Explain 'the what' and 'the why' of this code (Concept Explanation) as if teaching a junior developer (Pedagogical Clarity)."

    "3. Refactoring Roadmap: Provide actionable suggestions to improve performance, readability, or maintainability. Explain how these changes benefit the overall structure (Refactoring/Context Handling)."

    "4. Integrity Check: If the code is already optimal or a suspected 'bug' is actually intended behavior, explain why (False Positive mitigation)."
)