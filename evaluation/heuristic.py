import json
import pandas as pd
from collections import defaultdict

def analyze_logs(file_path):
    records = []
    
    # Storage for quiz validation
    # Structure: { 'Question Text': { 'original': 'A', 'verified': 'B', 'model': 'llama3.2' } }
    quiz_pairs = defaultdict(dict)

    try:
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    records.append(data)
                    
                    if data.get('type') == 'json_gen':
                        input_payload = data.get('input', {})
                        system_prompt = input_payload.get('system_prompt', '')
                        output_payload = data.get('output')
                        model_name = data.get('model', 'unknown') # Capture the model name

                        if not output_payload:
                            continue

                        # Normalize output to list
                        if isinstance(output_payload, list):
                            quiz_items = output_payload
                        elif isinstance(output_payload, dict):
                            quiz_items = [output_payload]
                        else:
                            continue

                        # --- CASE A: Generator (The Quiz Creator) ---
                        if "quiz creator" in system_prompt.lower():
                            for item in quiz_items:
                                if isinstance(item, dict):
                                    q_text = item.get('question')
                                    ans = item.get('correct_answer')
                                    
                                    if q_text:
                                        clean_q = q_text.strip()
                                        quiz_pairs[clean_q]['original'] = ans
                                        # Tag the question with the model that CREATED it
                                        quiz_pairs[clean_q]['model'] = model_name
                                
                        # --- CASE B: Verifier (The Validator) ---
                        elif "quiz verifier" in system_prompt.lower():
                            try:
                                start_marker = "Question: "
                                end_marker = "Options:"
                                start_idx = system_prompt.find(start_marker)
                                end_idx = system_prompt.find(end_marker)
                                
                                if start_idx != -1 and end_idx != -1:
                                    q_part = system_prompt[start_idx + len(start_marker) : end_idx]
                                    clean_q = q_part.strip()
                                    
                                    verifier_response = quiz_items[0] if quiz_items else {}
                                    if isinstance(verifier_response, dict):
                                        verified_ans = verifier_response.get('correct_answer')
                                        quiz_pairs[clean_q]['verified'] = verified_ans
                            except Exception:
                                continue
                                
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None, None

    # --- Part 1: Latency Metrics (Global) ---
    df = pd.DataFrame(records)
    latency_stats = None
    if not df.empty and 'latency_seconds' in df.columns:
        latency_stats = df.groupby('model')['latency_seconds'].agg(
            ['mean', 'count', 'min', 'max']
        ).round(4)
    
    # --- Part 2: Accuracy Calculation (Per Model) ---
    # Structure: { 'llama3.2': {'correct': 10, 'total': 20}, ... }
    model_accuracy_stats = defaultdict(lambda: {'correct': 0, 'total': 0})
    
    for q_text, data in quiz_pairs.items():
        # Only process if we have both the original creation AND a verification
        if 'original' in data and 'verified' in data:
            gen_model = data.get('model', 'unknown')
            
            # Ensure verification is valid (not None)
            if data['verified']:
                model_accuracy_stats[gen_model]['total'] += 1
                
                # Check if the Generator's answer matches the Verifier's answer
                if data['original'] == data['verified']:
                    model_accuracy_stats[gen_model]['correct'] += 1
    
    return latency_stats, model_accuracy_stats

# --- Execution ---
log_file = 'evaluation/logs.jsonl'
latency, accuracy_data = analyze_logs(log_file)

if latency is not None:
    print("## 1. Latency Statistics")
    print(latency)
    print("\n" + "="*50 + "\n")
    
    print("## 2. Validation Accuracy by Generator Model")
    print(f"{'Model Name':<20} | {'Total Quizzes':<15} | {'Correct':<10} | {'Accuracy':<10}")
    print("-" * 65)
    
    for model, stats in accuracy_data.items():
        total = stats['total']
        correct = stats['correct']
        acc_pct = (correct / total * 100) if total > 0 else 0.0
        
        print(f"{model:<20} | {total:<15} | {correct:<10} | {acc_pct:.2f}%")