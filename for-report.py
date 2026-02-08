import json
import sys
import os
import requests
from dataclasses import dataclass
from typing import List, Dict

# Rich UI imports
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown

# --- Configuration ---
MODELS = {
    "tutor": "llama3.2:3b",
    "generator": "gemma2:2b",
    "coder": "qwen2.5:3b",
    "explainer": "llama3.2:3b"
}

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_GEN_URL = "http://localhost:11434/api/generate"

# --- 1. Data Models ---
@dataclass
class Question:
    question: str
    options: Dict[str, str]
    correct_answer: str
    explanation: str

# --- 2. Progress Tracking ---
class ProgressManager:
    """Handles saving and loading user performance data."""
    def __init__(self, filename="user_progress.json"):
        self.filename = filename
        self.data = self._load_data()

    def _load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except:
                return {"topics": {}}
        return {"topics": {}}

    def get_topic_stats(self, topic: str):
        topic = topic.lower().strip()
        return self.data["topics"].get(topic, {"level": 1, "history": []})

    def update_progress(self, topic: str, is_correct: bool):
        topic = topic.lower().strip()
        if topic not in self.data["topics"]:
            self.data["topics"][topic] = {"level": 1, "history": []}
        
        stats = self.data["topics"][topic]
        stats["history"].append(is_correct)
        
        # Adaptive Logic: 3 correct in a row = Level Up. 2 wrong in a row = Level Down (min 1).
        recent = stats["history"][-3:]
        if recent == [True, True, True]:
            stats["level"] += 1
            stats["history"] = [] 
        elif recent[-2:] == [False, False] and stats["level"] > 1:
            stats["level"] -= 1
            stats["history"] = []

        self._save_data()

    def _save_data(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

# --- 3. API Client ---
class OllamaClient:
    """Handles communication with the Ollama local API."""
    
    def chat(self, model: str, messages: List[Dict[str, str]]) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7}
        }
        try:
            response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=60)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "")
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}"

    def generate_json(self, model: str, topic: str, system_prompt: str):
        payload = {
            "model": model,
            "prompt": f"System: {system_prompt}\n\nUser: {topic}",
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2}
        }
        try:
            response = requests.post(OLLAMA_GEN_URL, json=payload, timeout=60)
            response.raise_for_status()
            raw_output = response.json().get("response", "")
            data = json.loads(raw_output)
            if isinstance(data, dict):
                data = [data]
            return data
        except Exception as e:
            return None

# --- 4. Session Management ---
class QuizSession:
    def __init__(self, questions: List[Question]):
        self.questions = questions
        self.score = 0
        self.current_index = 0

    @property
    def current_question(self) -> Question:
        return self.questions[self.current_index]

    def process_answer(self, user_choice: str) -> bool:
        is_correct = user_choice.strip().upper() == self.current_question.correct_answer.upper()
        if is_correct:
            self.score += 1
        return is_correct

    def next_question(self):
        self.current_index += 1

    def is_complete(self) -> bool:
        return self.current_index >= len(self.questions)

# --- 5. CLI Interface & Main App ---
class AITutorApp:
    def __init__(self):
        self.client = OllamaClient()
        self.console = Console()
        self.progress = ProgressManager()

    def show_header(self, title: str):
        self.console.clear()
        self.console.print(Panel(f"[bold blue]{title}[/bold blue]", expand=False))

    def enter_explainer_mode(self, context: str):
        self.console.print(Panel("[bold magenta]EXPLORER MODE ACTIVATED[/]\n[dim]Ask follow-up questions about the topic. Type 'back' to return.[/]", border_style="magenta"))
        
        history = [
            {"role": "system", "content": f"You are a helpful assistant. Provide deep explanations for this context: {context}. Use Markdown for formatting."},
        ]

        while True:
            user_input = self.console.input("[bold magenta]Explain Mode > [/bold magenta]")
            if user_input.lower() in ['back', 'exit', 'quit']:
                break
            
            history.append({"role": "user", "content": user_input})
            
            with Live(Spinner("dots", text="Exploring concepts...")):
                response = self.client.chat(MODELS["explainer"], history)
            
            history.append({"role": "assistant", "content": response})
            self.console.print(Panel(Markdown(response), title="Explanation", border_style="magenta"))

    def run_explainer_mode(self):
        self.show_header("CONCEPT EXPLAINER")
        topic = self.console.input("[bold magenta]What concept or topic should I explain? [/bold magenta]")
        if topic.strip():
            self.enter_explainer_mode(topic)

    def run_quiz_mode(client, progress):
        show_header("PRACTICE QUIZ GENERATOR")
        topic = console.input("[bold yellow]What topic do you want to practice? [/bold yellow]")

        stats = progress.get_topic_stats(topic)
        current_level = stats["level"]
        console.print(f"[dim]Current Proficiency Level for {topic}: {current_level}/10[/dim]")

        while True:
            try:
                num_questions = int(console.input("[bold yellow]How many questions do you want? [/bold yellow]"))
                if num_questions > 0:
                    break
                console.print("[red]Please enter a positive number.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Enter a number.[/red]")

        all_questions = []
        previous_questions = set()

        with Live(Spinner("dots", text=f"Generating {num_questions} questions..."), refresh_per_second=10):
            while len(all_questions) < num_questions:
                # Prompt variation for diversity
                if not previous_questions:
                    prompt_variation = topic
                else:
                    prompt_variation = f"{topic}. Ask a different question than: {list(previous_questions)[-3:]}"

                # System prompt with descriptive difficulty
                sys_prompt = quiz_system_prompt(topic, current_level)

                # Generate question(s)
                data = client.generate_json(MODELS["generator"], prompt_variation, sys_prompt)
                if not data:
                    break

                for q in data:
                    if q["question"] in previous_questions:
                        continue

                    verif_prompt = verification_prompt(q["question"], q["options"], q["correct_answer"])
                    verification = client.generate_json(MODELS["explainer"], "", verif_prompt)
                    if verification and isinstance(verification, list) and "correct_answer" in verification[0]:
                        q["correct_answer"] = verification[0]["correct_answer"]
                    # Add to quiz
                    all_questions.append(q)
                    previous_questions.add(q["question"])

                    if len(all_questions) >= num_questions:
                        break

        all_questions = all_questions[:num_questions]

        # Convert JSON to Question objects
        try:
            questions = [Question(**q) for q in all_questions]
        except TypeError:
            console.print("[red]Error: Invalid question format from model[/red]")
            return


    def run_tutor_mode(self):
        self.show_header("SOCRATIC TUTOR")
        self.console.print("[dim]Type 'explain' to switch to direct explanations or 'menu' to quit.[/dim]\n")
        
        history = [{"role": "system", "content": "Socratic tutor. Ask questions, don't give answers."}]

        while True:
            user_input = self.console.input("[bold green]You: [/bold green]")
            if user_input.lower() == 'menu': break
            
            if user_input.lower() == 'explain':
                last_msg = history[-1]["content"] if len(history) > 1 else "the current topic"
                self.enter_explainer_mode(last_msg)
                continue

            history.append({"role": "user", "content": user_input})
            with Live(Spinner("dots", text="Tutor is thinking...")):
                response = self.client.chat(MODELS["tutor"], history)
            
            history.append({"role": "assistant", "content": response})
            self.console.print(Panel(Markdown(response), title="Tutor", border_style="blue"))

    def run_code_mode(self):
        self.show_header("CODE ANALYZER")
        self.console.print("[yellow]Paste code (Ctrl+D/Ctrl+Z to submit):[/yellow]")
        code = sys.stdin.read()
        if not code.strip(): return

        history = [
            {"role": "system", "content": "Analyze bugs and concepts in this code."},
            {"role": "user", "content": code}
        ]

        with Live(Spinner("dots", text="Analyzing code...")):
            result = self.client.chat(MODELS["coder"], history)
        
        self.console.print(Panel(Markdown(result), title="Analysis", border_style="magenta"))
        
        while True:
            action = self.console.input("\n[dim][Enter] Menu | [E]xplain Code deeply: [/dim]").lower()
            if action == 'e':
                self.enter_explainer_mode(f"Code Snippet:\n{code}\n\nAnalysis Provided:\n{result}")
            else:
                break

    def main_menu(self):
        while True:
            self.show_header("AI TUTOR v5.0 (ADAPTIVE)")
            menu = Table(show_header=False, box=None)
            menu.add_row("[cyan]1.[/]", "Practice Quiz Mode (Level-Aware)")
            menu.add_row("[cyan]2.[/]", "Socratic Tutoring")
            menu.add_row("[cyan]3.[/]", "Code Analysis")
            menu.add_row("[cyan]4.[/]", "Concept Explainer")
            menu.add_row("[red]5.[/]", "Exit")
            self.console.print(menu)

            choice = self.console.input("\n[bold]Select option: [/bold]")
            if choice == '1': self.run_quiz_mode()
            elif choice == '2': self.run_tutor_mode()
            elif choice == '3': self.run_code_mode()
            elif choice == '4': self.run_explainer_mode()
            elif choice == '5': break

if __name__ == "__main__":
    app = AITutorApp()
    app.main_menu()