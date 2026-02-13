# evaluation/prompts.py

def get_mcq_eval_prompt(topic: str, mcq_json: str) -> str:
    return f"""
    You are an expert educational content evaluator.
    Evaluate the following Multiple Choice Question (MCQ) generated for the topic '{topic}'.
    
    MCQ Content:
    {mcq_json}
    
    Score the MCQ on these specific dimensions (0-2 scale):
    1. Relevance to topic: (0=Irrelevant, 1=Tangential, 2=Highly Relevant)
    2. Uniqueness/Non-Redundancy: (0=Cliché/Copy, 1=Standard, 2=Novel/Insightful)
    3. Quality of distractors: (0=Obvious, 1=Okay, 2=Plausible/Tricky)
    4. Clarity and unambiguity: (0=Confusing, 1=Readable, 2=Crystal Clear)

    Return ONLY valid JSON in this format:
    {{
        "relevance": int,
        "uniqueness": int,
        "distractors": int,
        "clarity": int,
        "critique": "short explanation"
    }}
    """

def get_tutor_eval_prompt(conversation_history: str, latest_response: str) -> str:
    return f"""
    You are a pedagogical expert evaluating an AI Tutor's response.
    
    Context (Student-Tutor History):
    {conversation_history}
    
    AI Tutor's Latest Response:
    {latest_response}
    
    Evaluate the response on these dimensions (1-5 scale, where 5 is best):
    1. Socratic Questioning: (1=Lectures/Gives answer, 5=Asks perfect guiding questions)
    2. Scaffolding: (1=Huge leaps, 5=Builds step-by-step)
    3. Adaptivity: (1=Ignores misconceptions, 5=Directly addresses specific student errors)
    4. Context Retention: (1=Amnesic, 5=Explicitly references earlier student claims)
    5. Hallucination Safety: (1=Major falsehoods, 5=Completely factual)

    Return ONLY valid JSON in this format:
    {{
        "socratic_score": int,
        "scaffolding_score": int,
        "adaptivity_score": int,
        "context_score": int,
        "safety_score": int,
        "reasoning": "short explanation"
    }}
    """

def get_code_eval_prompt(code_snippet: str, analysis_output: str) -> str:
    return f"""
    You are a Senior Software Engineer evaluating an AI Code Reviewer.
    
    Original Code:
    {code_snippet}
    
    AI's Analysis:
    {analysis_output}
    
    Evaluate the analysis on these dimensions (1-5 scale, 5 is best):
    1. Bug Detection Accuracy: (1=Missed obvious bugs, 5=Caught all critical issues)
    2. False Positive Rate: (1=Hallucinated many bugs, 5=No false positives)
    3. Concept Explanation: (1=Jargon soup, 5=Clear, educational 'why')
    4. Refactoring Suggestions: (1=Useless/Wrong, 5=Actionable, modern, idiomatic)
    5. Context Handling: (1=Line-by-line tunnel vision, 5=Understands full logic flow)

    Return ONLY valid JSON in this format:
    {{
        "bug_detection": int,
        "false_positives": int,
        "explanation_quality": int,
        "refactoring": int,
        "context_handling": int,
        "summary": "short summary"
    }}
    """