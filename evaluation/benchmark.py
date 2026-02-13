import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from math import pi
import google.generativeai as genai

# ==========================================
# 1. CONFIGURATION
# ==========================================

# API_KEY = "AIzaSyCg8NWG7pH5vp4nqfaMCgILb9sb64BY1yM"
API_KEY = "AIzaSyDEnGeUejIwiJDB-YFKdpvWqXvKEoNi1-4"
JUDGE_MODEL = "gemini-2.5-flash" 
LOG_FILE_PATH = "evaluation/logs.jsonl" # Path to your input file

# ==========================================
# 2. THE JUDGE ENGINE
# ==========================================

class GeminiJudge:
    def __init__(self, api_key, model_name=JUDGE_MODEL):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def _get_gemini_response(self, prompt):
        try:
            response = self.model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            return response.text
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            return None

    def evaluate_log(self, log_entry, category):
        prompts = {
            "tutor": """
            Evaluate based on Socratic Tutoring:
            Input: {input_data}
            Output: {output_data}
            Score (1-5): socratic, scaffolding, adaptivity, retention, safety.
            Return JSON: {{"scores": {{"socratic": int, "scaffolding": int, "adaptivity": int, "retention": int, "safety": int}}, "reasoning": "string"}}
            """,
            "code": """
            Evaluate Code Review:
            Input: {input_data}
            Output: {output_data}
            Score (1-5): bug_detection, false_positives, explanation, refactoring, context.
            Return JSON: {{"scores": {{"bug_detection": int, "false_positives": int, "explanation": int, "refactoring": int, "context": int}}, "reasoning": "string"}}
            """,
            "quiz": """
            Evaluate Quiz Gen:
            Input: {input_data}
            Output: {output_data}
            Score (1-5): relevance, uniqueness, distractors, clarity.
            Return JSON: {{"scores": {{"relevance": int, "uniqueness": int, "distractors": int, "clarity": int}}, "reasoning": "string"}}
            """
        }
        
        input_str = json.dumps(log_entry.get('input', ''))
        output_str = json.dumps(log_entry.get('output', ''))
        formatted_prompt = prompts[category].format(input_data=input_str, output_data=output_str)
        
        response_text = self._get_gemini_response(formatted_prompt)
        if response_text:
            try:
                clean_json = response_text.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
            except: return None
        return None

# ==========================================
# 3. LOG PROCESSOR (JSONL)
# ==========================================

class LogProcessor:
    def __init__(self, judge_engine):
        self.judge = judge_engine
        self.results = []

    def identify_category(self, entry):
        inp_dump = str(entry.get('input', '')).lower()
        if "socratic" in inp_dump: return "tutor"
        if "quiz" in inp_dump: return "quiz"
        if "def " in inp_dump or "code" in inp_dump: return "code"
        return "unknown"

    def process_jsonl(self, file_path):
        if not os.path.exists(file_path):
            print(f"File {file_path} not found.")
            return pd.DataFrame()

        with open(file_path, 'r') as f:
            for line in f:
                if not line.strip(): continue
                entry = json.loads(line)

                # Skip Validator Rules
                if entry.get('type') == 'json_gen' and 'llama' in entry.get('model', '').lower():
                    continue

                category = self.identify_category(entry)
                if category == "unknown": continue

                print(f"Judging {entry.get('model')} on {category}...")
                evaluation = self.judge.evaluate_log(entry, category)
                
                if evaluation:
                    self.results.append({
                        "model": entry.get('model', 'SLLM'), # Default name if missing
                        "category": category,
                        "scores": evaluation['scores']
                    })
        
        return pd.DataFrame(self.results)

# ==========================================
# 4. RADAR CHART VISUALIZATION
# ==========================================

def generate_radar_comparison(df):
    if df.empty: return

    categories = df['category'].unique()
    for cat in categories:
        subset = df[df['category'] == cat].copy()
        
        # Flatten scores
        scores_df = pd.json_normalize(subset['scores'])
        subset = pd.concat([subset.reset_index(drop=True), scores_df], axis=1)
        
        # Aggregate by model
        metrics = scores_df.columns.tolist()
        agg = subset.groupby('model')[metrics].mean().reset_index()

        # Radar setup
        num_vars = len(metrics)
        angles = [n / float(num_vars) * 2 * pi for n in range(num_vars)]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        
        # Define specific colors for models
        colors = {"gemini-flash": "#4285F4", "sllm": "#EA4335"} # Blue vs Red
        
        for i, row in agg.iterrows():
            model_label = row['model'].lower()
            color = colors.get(next((k for k in colors if k in model_label), None), np.random.rand(3,))
            
            values = row[metrics].tolist()
            values += values[:1]
            
            ax.plot(angles, values, linewidth=2, label=row['model'], color=color)
            ax.fill(angles, values, color=color, alpha=0.1)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics)
        ax.set_ylim(0, 5)
        plt.title(f"Comparison: {cat.upper()}", size=20, y=1.1)
        plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
        
        plt.savefig(f"radar_{cat}_comparison.png")
        plt.show()

# ==========================================
# EXECUTION
# ==========================================

if __name__ == "__main__":
    judge = GeminiJudge(API_KEY)
    processor = LogProcessor(judge)
    
    results = processor.process_jsonl(LOG_FILE_PATH)
    if not results.empty:
        generate_radar_comparison(results)