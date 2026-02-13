# evaluation/engine.py
import json
import os
import time
import google.generativeai as genai
from rich.console import Console
from rich.table import Table
from rich.progress import track
from dotenv import load_dotenv

# Import our specific prompts
from evaluation.prompts import (
    get_mcq_eval_prompt, 
    get_tutor_eval_prompt, 
    get_code_eval_prompt
)

load_dotenv()
console = Console()

class EvaluationEngine:
    def __init__(self, log_file="evaluation/logs.jsonl"):
        self.log_file = log_file
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY missing")
        
        genai.configure(api_key=api_key)
        # We use a smart model as the Judge
        self.judge_model = genai.GenerativeModel("gemini-2.5-flash")

    def _call_judge(self, prompt: str):
        try:
            response = self.judge_model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json", "temperature": 0.1}
            )
            return json.loads(response.text)
        except Exception as e:
            console.print(f"[red]Judge Error:[/red] {e}")
            return None

    def evaluate_entry(self, entry: dict):
        interaction_type = entry.get("type", "")
        model_output = entry.get("output", "")
        inputs = entry.get("input", "")

        # 1. QUIZ EVALUATION (MCQ)
        if interaction_type == "json_gen" and isinstance(model_output, list):
            # Assuming input was a dict with 'topic'
            topic = inputs.get("topic", "General") if isinstance(inputs, dict) else "Unknown"
            
            # Evaluate the first question generated (usually one per call in your logic)
            if not model_output: return None
            mcq_str = json.dumps(model_output[0])
            
            prompt = get_mcq_eval_prompt(topic, mcq_str)
            score = self._call_judge(prompt)
            return {"mode": "Quiz", **score} if score else None

        # 2. TUTOR EVALUATION (Chat)
        elif interaction_type == "chat":
            # Heuristic: Check system prompt to see if it was Tutor or Code
            # In your logger, input is a list of messages. 
            # We look at the first system message.
            system_msg = ""
            if isinstance(inputs, list) and len(inputs) > 0:
                if inputs[0].get("role") == "system":
                    system_msg = inputs[0].get("content", "").lower()

            if "socratic" in system_msg or "tutor" in system_msg:
                # Format history for the judge
                history_text = "\n".join([f"{m['role']}: {m['content']}" for m in inputs])
                prompt = get_tutor_eval_prompt(history_text, str(model_output))
                score = self._call_judge(prompt)
                return {"mode": "Tutor", **score} if score else None

            # 3. CODE EVALUATION
            elif "code" in system_msg or "bug" in system_msg or "analyze" in system_msg:
                # The user code is usually the last user message
                user_code = inputs[-1]['content'] if inputs else "No code found"
                prompt = get_code_eval_prompt(user_code, str(model_output))
                score = self._call_judge(prompt)
                return {"mode": "Code", **score} if score else None

        return None

    def run(self):
        if not os.path.exists(self.log_file):
            console.print("[red]No logs found![/red]")
            return

        results = []
        
        # Load logs
        with open(self.log_file, 'r') as f:
            lines = f.readlines()

        console.print(f"[bold cyan]Running Evaluation on {len(lines)} log entries...[/bold cyan]")

        for line in track(lines, description="Judging..."):
            try:
                entry = json.loads(line)
                # Don't evaluate the Judge itself if it ends up in logs
                if "gemini" in entry['model'].lower():
                    continue 

                eval_result = self.evaluate_entry(entry)
                
                if eval_result:
                    eval_result["model_evaluated"] = entry["model"]
                    results.append(eval_result)
                    
            except json.JSONDecodeError:
                continue

        self._print_report(results)

    def _print_report(self, results):
        if not results:
            console.print("No valid interactions found to evaluate.")
            return

        # Separate results by mode
        modes = ["Quiz", "Tutor", "Code"]
        
        for mode in modes:
            mode_results = [r for r in results if r["mode"] == mode]
            if not mode_results:
                continue

            table = Table(title=f"Evaluation Report: {mode} Mode")
            table.add_column("Model", style="cyan")
            
            # Dynamic columns based on keys
            keys = [k for k in mode_results[0].keys() if k not in ["mode", "model_evaluated", "critique", "reasoning", "summary"]]
            
            for k in keys:
                table.add_column(k.replace("_", " ").title(), justify="center")
            
            table.add_column("Notes", style="green")

            for r in mode_results:
                row_data = [r["model_evaluated"]]
                for k in keys:
                    row_data.append(str(r[k]))
                
                # Pick the text field
                note = r.get("critique") or r.get("reasoning") or r.get("summary") or ""
                row_data.append(note[:50]+"..." if len(note)>50 else note)
                
                table.add_row(*row_data)

            console.print(table)
            console.print("\n")

if __name__ == "__main__":
    engine = EvaluationEngine()
    engine.run()