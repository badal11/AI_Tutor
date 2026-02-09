import json
import pandas as pd
from collections import defaultdict

def analyze_logs(file_path):
    records = []
    
    # Storage for quiz validation
    # Key: Question text, Value: { 'original': 'A', 'verified': None }
    quiz_pairs = defaultdict(dict)

    with open(file_path, 'r') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                records.append(data)
                
                # Logic for Quiz Accuracy
                if data['type'] == 'json_gen':
                    # Check if this is a generator or verifier
                    input_prompt = data['input'].get('system_prompt', '')
                    
                    if "quiz creator" in input_prompt.lower():
                        q_text = data['output'].get('question')
                        ans = data['output'].get('correct_answer')
                        if q_text:
                            quiz_pairs[q_text]['original'] = ans
                            
                    elif "quiz verifier" in input_prompt.lower():
                        # Extract the question from the system prompt to match
                        # Usually, verifiers repeat the question in the prompt
                        q_start = input_prompt.find("Question: ") + len("Question: ")
                        q_end = input_prompt.find("\nOptions:")
                        q_text = input_prompt[q_start:q_end].strip()
                        
                        verified_ans = data['output'].get('correct_answer')
                        if q_text:
                            quiz_pairs[q_text]['verified'] = verified_ans
            except Exception as e:
                continue

    # 1. Calculate Latency Metrics using Pandas
    df = pd.DataFrame(records)
    latency_stats = df.groupby('model')['latency_seconds'].agg(['mean', 'count', 'min', 'max'])
    
    # 2. Calculate Accuracy
    correct_count = 0
    total_matched = 0
    
    for q, results in quiz_pairs.items():
        if 'original' in results and 'verified' in results and results['verified'] is not None:
            total_matched += 1
            if results['original'] == results['verified']:
                correct_count += 1
    
    accuracy = (correct_count / total_matched) * 100 if total_matched > 0 else 0

    return latency_stats, accuracy, total_matched

# --- Execution ---
# Save your logs to 'logs.jsonl'
stats, acc, total = analyze_logs('evaluation/logs.jsonl')

print("## Latency Statistics by Model")
print(stats)
print("\n---")
print(f"## Quiz Validation Accuracy")
print(f"Total Quizzes Verified: {total}")
print(f"Accuracy: {acc:.2f}%")