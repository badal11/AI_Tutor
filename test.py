import json
import sys
import requests
from dataclasses import dataclass, field
from typing import List, Dict, Optional

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
    "coder": "qwen2.5:3b"
}
OLLAMA_URL = "http://localhost:11434/api/generate"

# --- 1. Data Models ---
@dataclass
class Question:
    question: str
    options: Dict[str, str]  # Format: {"A": "Choice 1", "B": "Choice 2", ...}
    correct_answer: str      # Format: "A"
    explanation: str

# --- 2. API Client ---
class OllamaClient:
    """Handles communication with the Ollama local API."""
    def __init__(self, url: str):
        self.url = url

    def generate(self, model: str, prompt: str, system_prompt: str = "") -> str:
        payload = {
            "model": model,
            "prompt": f"System: {system_prompt}\n\nUser: {prompt}",
            "stream": False,
            "options": {"temperature": 0.2} # Low temperature for consistent JSON
        }
        try:
            response = requests.post(self.url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_json(self, model: str, topic: str, system_prompt: str):
        """Helper to specifically handle JSON responses from the AI."""
        raw_output = self.generate(model, topic, system_prompt)
        # Clean markdown code blocks if the AI includes them
        clean_json = raw_output.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean_json)
        except json.JSONDecodeError:
            return None

# --- 3. Session Management ---
class QuizSession:
    """Tracks score and progress for an active quiz."""
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
        self.current_index += 1
        return is_correct

    def is_complete(self) -> bool:
        return self.current_index >= len(self.questions)

# --- 4. CLI Interface & Main App ---
class AITutorApp:
    def __init__(self):
        self.client = OllamaClient(OLLAMA_URL)
        self.console = Console()

    def show_header(self, title: str):
        self.console.clear()
        self.console.print(Panel(f"[bold blue]{title}[/bold blue]", expand=False))

    def run_quiz_mode(self):
        self.show_header("PRACTICE QUIZ GENERATOR")
        topic = self.console.input("[bold yellow]What topic do you want to practice? [/bold yellow]")
        
        sys_prompt = (
            "You are a quiz creator. Return ONLY a JSON list of 3 multiple-choice questions. "
            "Format: [{\"question\": \"...\", \"options\": {\"A\": \"...\", \"B\": \"...\"}, "
            "\"correct_answer\": \"A\", \"explanation\": \"...\"}]"
        )

        with Live(Spinner("dots", text=f"Generating questions for [cyan]{topic}[/]..."), refresh_per_second=10):
            data = self.client.generate_json(MODELS["generator"], topic, sys_prompt)

        if not data:
            self.console.print("[red]Error: Could not parse quiz data. Try again.[/red]")
            self.console.input("\nPress Enter...")
            return

        # Initialize Session
        questions = [Question(**q) for q in data]
        session = QuizSession(questions)

        # Quiz Loop
        while not session.is_complete():
            q = session.current_question
            self.show_header(f"Question {session.current_index + 1} of {len(questions)}")
            
            # Display Question
            q_text = f"**{q.question}**\n\n"
            for key, val in q.options.items():
                q_text += f"* **{key}**: {val}\n"
            
            self.console.print(Panel(Markdown(q_text), title=f"Score: {session.score}", border_style="cyan"))
            
            # Get User Input
            choice = self.console.input("\n[bold]Your Answer (A/B/C/D): [/bold]").upper()
            
            # Logic & Feedback
            correct = session.process_answer(choice)
            color = "green" if correct else "red"
            msg = "✅ [bold]Correct![/bold]" if correct else f"❌ [bold]Incorrect![/bold] The answer was {q.correct_answer}."
            
            self.console.print(Panel(f"{msg}\n\n[italic]{q.explanation}[/italic]", border_style=color))
            self.console.input("\n[dim]Press Enter for next question...[/dim]")

        # Final Result
        self.show_header("RESULTS")
        percent = (session.score / len(questions)) * 100
        self.console.print(f"\n[bold gold1]Quiz Finished![/bold gold1]")
        self.console.print(f"Final Score: [bold cyan]{session.score}/{len(questions)}[/bold cyan] ({percent}%)\n")
        self.console.input("[dim]Press Enter to return to menu...[/dim]")

    def run_tutor_mode(self):
        self.show_header("SOCRATIC TUTOR")
        sys_msg = "You are a Socratic tutor. Use questions to guide the student to the answer."
        while True:
            user_input = self.console.input("[bold green]You: [/bold green]")
            if user_input.lower() in ['exit', 'menu']: break
            
            with Live(Spinner("dots", text="Tutor is thinking...")):
                response = self.client.generate(MODELS["tutor"], user_input, sys_msg)
            
            self.console.print(Panel(Markdown(response), title="Tutor", border_style="blue"))

    def run_code_mode(self):
        self.show_header("CODE ANALYZER")
        self.console.print("[yellow]Paste code (Ctrl+D / Ctrl+Z + Enter to submit):[/yellow]")
        code = sys.stdin.read()
        if not code.strip(): return

        with Live(Spinner("dots", text="Analyzing code...")):
            sys_msg = "Explain bugs and concepts in this code for a beginner."
            result = self.client.generate(MODELS["coder"], code, sys_msg)
        
        self.console.print(Panel(Markdown(result), title="Analysis", border_style="magenta"))
        self.console.input("\nPress Enter...")

    def main_menu(self):
        while True:
            self.show_header("AI TUTOR v3.0")
            menu = Table(show_header=False, box=None)
            menu.add_row("[cyan]1.[/]", "Practice Quiz Mode")
            menu.add_row("[cyan]2.[/]", "Socratic Tutoring")
            menu.add_row("[cyan]3.[/]", "Code Analysis")
            menu.add_row("[red]4.[/]", "Exit")
            self.console.print(menu)

            choice = self.console.input("\n[bold]Select option: [/bold]")
            if choice == '1': self.run_quiz_mode()
            elif choice == '2': self.run_tutor_mode()
            elif choice == '3': self.run_code_mode()
            elif choice == '4': break

if __name__ == "__main__":
    app = AITutorApp()
    app.main_menu()