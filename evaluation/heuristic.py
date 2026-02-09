import json
import pandas as pd
from collections import defaultdict

def analyze_logs(file_path):
    records = []
    
    # Storage for quiz validation
    # Structure: { 'Question Text': { 'original': 'A', 'verified': 'B' } }
    quiz_pairs = defaultdict(dict)

    try:
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    # 1. Parse JSON
                    data = json.loads(line.strip())
                    records.append(data)
                    
                    # 2. Logic for Quiz Accuracy Extraction
                    if data.get('type') == 'json_gen':
                        input_payload = data.get('input', {})
                        system_prompt = input_payload.get('system_prompt', '')
                        output_payload = data.get('output')

                        if not output_payload:
                            continue

                        # --- FIX: Handle both List and Dict outputs ---
                        if isinstance(output_payload, list):
                            quiz_items = output_payload
                        elif isinstance(output_payload, dict):
                            quiz_items = [output_payload]
                        else:
                            continue # Skip strings or other types

                        # Case A: This is the Generator (Creator)
                        if "quiz creator" in system_prompt.lower():
                            for item in quiz_items:
                                # Ensure item is a dict before accessing .get()
                                if isinstance(item, dict):
                                    q_text = item.get('question')
                                    ans = item.get('correct_answer')
                                    
                                    if q_text:
                                        clean_q = q_text.strip()
                                        quiz_pairs[clean_q]['original'] = ans
                                
                        # Case B: This is the Verifier
                        elif "quiz verifier" in system_prompt.lower():
                            # The verifier usually only verifies one question at a time
                            # Extract the question text from the prompt
                            try:
                                start_marker = "Question: "
                                end_marker = "Options:"
                                
                                start_idx = system_prompt.find(start_marker)
                                end_idx = system_prompt.find(end_marker)
                                
                                if start_idx != -1 and end_idx != -1:
                                    # Extract question text from prompt
                                    q_part = system_prompt[start_idx + len(start_marker) : end_idx]
                                    clean_q = q_part.strip()
                                    
                                    # Get the verifier's answer
                                    # We take the first item if it's a list, or the dict itself
                                    verifier_response = quiz_items[0] if isinstance(quiz_items, list) and quiz_items else quiz_items[0]
                                    
                                    if isinstance(verifier_response, dict):
                                        verified_ans = verifier_response.get('correct_answer')
                                        quiz_pairs[clean_q]['verified'] = verified_ans
                            except Exception:
                                continue
                                
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None, None, None

    # --- Part 1: Latency Metrics ---
    df = pd.DataFrame(records)
    
    if not df.empty and 'latency_seconds' in df.columns:
        latency_stats = df.groupby('model')['latency_seconds'].agg(
            Average='mean', 
            Count='count', 
            Min='min', 
            Max='max'
        ).round(4)
    else:
        latency_stats = "No latency data found."
    
    # --- Part 2: Accuracy Calculation ---
    correct_count = 0
    total_validated = 0
    
    for q_text, answers in quiz_pairs.items():
        if 'original' in answers and 'verified' in answers:
            if answers['verified']:
                total_validated += 1
                # Check if matches
                if answers['original'] == answers['verified']:
                    correct_count += 1
    
    accuracy = (correct_count / total_validated * 100) if total_validated > 0 else 0.0

    return latency_stats, accuracy, total_validated

# --- Execution ---
stats, acc, total = analyze_logs('evaluation/logs.jsonl')

if stats is not None:
    print("## Latency Statistics by Model")
    print(stats)
    print("\n" + "="*40 + "\n")
    print(f"## Quiz Validation Accuracy")
    print(f"Total Quizzes Validated: {total}")
    print(f"Accuracy (Model vs Validator): {acc:.2f}%")