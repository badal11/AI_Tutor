import json
import os
import re
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from math import pi

# Placeholder for the actual library interaction
# In a real scenario, ensure you have: pip install google-generativeai
import google.generativeai as genai

# ==========================================
# 1. CONFIGURATION & MOCK DATA
# ==========================================

# Replace with your actual API Key
API_KEY = "AIzaSyCg8NWG7pH5vp4nqfaMCgILb9sb64BY1yM"
MODEL_NAME = "gemini-2.5-flash"  # Adjust to valid model version if 2.5 is not yet public

# The sample logs provided in your prompt
SAMPLE_LOGS = [

]

# ==========================================
# 2. THE JUDGE ENGINE
# ==========================================

class GeminiJudge:
    def __init__(self, api_key, model_name="gemini-1.5-flash"):
        if api_key == "YOUR_GEMINI_API_KEY":
            print("⚠️ WARNING: No API Key provided. Using Mock Mode.")
            self.mock_mode = True
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            self.mock_mode = False

    def _get_gemini_response(self, prompt):
        if self.mock_mode:
            # Return dummy JSON for demonstration if no API key
            return """
            {
                "scores": {"criteria_1": 4, "criteria_2": 5, "criteria_3": 3, "criteria_4": 4, "criteria_5": 5},
                "reasoning": "Mock evaluation reasoning."
            }
            """
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
        """Dispatches to specific evaluation logic based on category."""
        
        prompts = {
            "tutor": """
            Evaluate the following AI interaction based on Socratic Tutoring principles.
            
            Input Context: {input_data}
            Model Output: {output_data}
            
            Score (1-5) on:
            1. Socratic Questioning (1=Lectures, 5=Guiding questions)
            2. Scaffolding (1=Huge leaps, 5=Step-by-step)
            3. Adaptivity (1=Ignores misconceptions, 5=Addresses errors)
            4. Context Retention (1=Amnesic, 5=References earlier claims)
            5. Hallucination Safety (1=Falsehoods, 5=Factual)
            
            Return JSON: {{ "scores": {{ "socratic": int, "scaffolding": int, "adaptivity": int, "retention": int, "safety": int }}, "reasoning": "string" }}
            """,
            
            "quiz": """
            Evaluate the following generated Quiz Question.
            
            Context/Prompt: {input_data}
            Generated Quiz JSON: {output_data}
            
            Score (1-5) on:
            1. Relevance (1=Off-topic, 5=Highly relevant)
            2. Uniqueness (1=Redundant/Cliche, 5=Novel)
            3. Distractor Quality (1=Obvious/Ambiguous, 5=Challenging & Clear)
            4. Clarity (1=Confusing, 5=Crystal Clear)
            
            Return JSON: {{ "scores": {{ "relevance": int, "uniqueness": int, "distractors": int, "clarity": int }}, "reasoning": "string" }}
            """,
            
            "code": """
            Evaluate the following Code Analysis/Code Review.
            
            Code/Prompt: {input_data}
            Model Analysis: {output_data}
            
            Score (1-5) on:
            1. Bug Detection (1=Missed bugs, 5=Caught criticals)
            2. False Positives (1=Many hallucinations, 5=None)
            3. Explanation (1=Jargon, 5=Educational)
            4. Refactoring (1=Bad advice, 5=Idiomatic/Modern)
            5. Context Handling (1=Tunnel vision, 5=Full logic flow)
            
            Return JSON: {{ "scores": {{ "bug_detection": int, "false_positives": int, "explanation": int, "refactoring": int, "context": int }}, "reasoning": "string" }}
            """
        }
        
        # Prepare data string
        input_str = json.dumps(log_entry.get('input', ''))
        output_str = json.dumps(log_entry.get('output', ''))
        
        formatted_prompt = prompts[category].format(input_data=input_str, output_data=output_str)
        
        response_text = self._get_gemini_response(formatted_prompt)
        
        if response_text:
            try:
                # Clean markdown code blocks if present
                clean_json = response_text.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
            except json.JSONDecodeError:
                print("Failed to parse JSON response from Judge")
                return None
        return None

# ==========================================
# 3. LOG PROCESSOR
# ==========================================

class LogProcessor:
    def __init__(self, judge_engine):
        self.judge = judge_engine
        self.results = []

    def identify_category(self, entry):
        # Heuristics to determine category based on content
        inp_dump = json.dumps(entry.get('input', ''))
        
        if "Socratic Tutor" in inp_dump:
            return "tutor"
        elif "Quiz creator" in inp_dump or (entry.get('type') == 'json_gen' and "quiz" in inp_dump.lower()):
            return "quiz"
        elif "Senior Software Engineer" in inp_dump or "def " in inp_dump:
            return "code"
        return "unknown"

    def process_logs(self, logs):
        for entry in logs:
            # 1. Validator Skip Rule
            # "if the json object has type as json_gen and model as llama - it’s a validator and skip that"
            if entry.get('type') == 'json_gen' and 'llama' in entry.get('model', '').lower():
                print(f"Skipping Validator Model: {entry['model']}")
                continue

            # 2. Identify Category
            category = self.identify_category(entry)
            if category == "unknown":
                continue

            print(f"Evaluating {entry['model']} on task: {category}...")
            
            # 3. Evaluate
            evaluation = self.judge.evaluate_log(entry, category)
            
            if evaluation:
                self.results.append({
                    "model": entry['model'],
                    "category": category,
                    "scores": evaluation['scores'],
                    "reasoning": evaluation['reasoning']
                })
        
        return pd.DataFrame(self.results)

# ==========================================
# 4. VISUALIZATION ENGINE
# ==========================================

def generate_charts(df):
    if df.empty:
        print("No data to plot.")
        return

    sns.set_theme(style="whitegrid")
    
    # Process each category separately (Tutor vs Code vs Quiz)
    categories = df['category'].unique()
    
    for cat in categories:
        subset = df[df['category'] == cat].copy()
        
        # --- FIX: ROBUST FLATTENING OF SCORES ---
        # 1. Flatten the 'scores' dictionary into separate columns
        # This turns [{'socratic': 5}, {'socratic': 3}] into a proper DataFrame
        scores_expanded = pd.json_normalize(subset['scores'])
        
        # 2. Reset indices to ensure they align for concatenation
        subset = subset.reset_index(drop=True)
        scores_expanded = scores_expanded.reset_index(drop=True)
        
        # 3. Concatenate model info with the new score columns
        # We drop the original 'scores' column and 'reasoning' to clean up
        subset_expanded = pd.concat([subset[['model']], scores_expanded], axis=1)
        
        # 4. Identify the metric columns (all columns that came from the scores dict)
        metric_cols = scores_expanded.columns.tolist()
        
        # 5. Group by model and calculate mean for the metrics
        agg = subset_expanded.groupby('model')[metric_cols].mean().reset_index()

        # --- PLOTTING LOGIC ---
        
        # Radar Chart for multi-dimensional metrics (Usually Tutor/Code)
        if len(metric_cols) > 2:
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
            
            # Setup angles
            angles = [n / float(len(metric_cols)) * 2 * pi for n in range(len(metric_cols))]
            angles += angles[:1] # Close the loop
            
            # Create a color palette
            colors = sns.color_palette("husl", len(agg))
            
            for idx, row in agg.iterrows():
                # Fix: Access values directly from the columns, NOT row['scores'][m]
                values = row[metric_cols].tolist() 
                values += values[:1] # Close the loop
                
                ax.plot(angles, values, linewidth=2, linestyle='solid', label=row['model'], color=colors[idx])
                ax.fill(angles, values, color=colors[idx], alpha=0.1)
            
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(metric_cols)
            
            # Set fixed scale for 1-5 evaluation
            ax.set_yticks([1, 2, 3, 4, 5])
            ax.set_ylim(0, 5)
            
            ax.set_title(f"Evaluation: {cat.upper()}", y=1.08)
            ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
            
            filename = f"benchmark_{cat}_radar.png"
            plt.savefig(filename, bbox_inches='tight')
            print(f"Generated {filename}")
            plt.close()
            
        # Bar Chart for simpler metrics (Usually Quiz)
        else:
            # Melt the aggregated data for seaborn barplot
            melted = agg.melt(id_vars='model', value_vars=metric_cols, var_name='Metric', value_name='Score')
            
            plt.figure(figsize=(10, 6))
            sns.barplot(data=melted, x='Metric', y='Score', hue='model')
            plt.ylim(0, 5)
            plt.title(f"Evaluation: {cat.upper()}")
            
            filename = f"benchmark_{cat}_bar.png"
            plt.savefig(filename)
            print(f"Generated {filename}")
            plt.close()

# ==========================================
# MAIN EXECUTION
# ==========================================

if __name__ == "__main__":
    # Initialize Engine
    judge = GeminiJudge(API_KEY, MODEL_NAME)
    processor = LogProcessor(judge)
    
    # Run Evaluation
    results_df = processor.process_logs(SAMPLE_LOGS)
    
    # Output Report
    print("\n" + "="*40)
    print("       GEMINI JUDGE EVALUATION REPORT       ")
    print("="*40)
    
    if not results_df.empty:
        for idx, row in results_df.iterrows():
            print(f"\nModel: {row['model']} | Task: {row['category'].upper()}")
            print("-" * 20)
            print(f"Scores: {row['scores']}")
            print(f"Judge Reasoning: {row['reasoning'][:150]}...") 
        
        # Generate Visuals
        generate_charts(results_df)
        print("\nAll charts generated successfully.")
    else:
        print("No results generated.")