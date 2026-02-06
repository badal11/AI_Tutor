import json
import sys
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
    "coder": "qwen2.5:3b"
}
# Note: Using /api/chat for history-based modes
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_GEN_URL = "http://localhost:11434/api/generate"

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
    
    def chat(self, model: str, messages: List[Dict[str, str]]) -> str:
        """Handles multi-turn conversations using the Chat API."""
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
        """Helper for structured JSON data (used for Quiz generation)."""
        payload = {
            "model": model,
            "prompt": f"System: {system_prompt}\n\nUser: {topic}",
            "stream": False,
            "format": "json",  # Forces Ollama to output valid JSON
            "options": {"temperature": 0.2}
        }
        try:
            response = requests.post(OLLAMA_GEN_URL, json=payload, timeout=60)
            response.raise_for_status()
            raw_output = response.json().get("response", "")

            # Some models return JSON as string; normalize here
            data = json.loads(raw_output)

            # Normalize single object to list
            if isinstance(data, dict):
                data = [data]

            return data
        except Exception as e:
            print("JSON generation error:", e)
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
        self.client = OllamaClient()
        self.console = Console()

    def show_header(self, title: str):
        self.console.clear()
        self.console.print(Panel(f"[bold blue]{title}[/bold blue]", expand=False))

    def run_quiz_mode(self):
        self.show_header("PRACTICE QUIZ GENERATOR")
        topic = self.console.input("[bold yellow]What topic do you want to practice? [/bold yellow]")
        
        sys_prompt = (
            "You are a quiz creator. Return ONLY valid JSON. "
            "Return a JSON ARRAY (list) of exactly 3 multiple-choice questions. "
            "Each item must follow this format:\n"
            "{\n"
            "  \"question\": \"...\",\n"
            "  \"options\": {\"A\": \"...\", \"B\": \"...\", \"C\": \"...\", \"D\": \"...\"},\n"
            "  \"correct_answer\": \"A\",\n"
            "  \"explanation\": \"...\"\n"
            "}\n"
            "Do NOT return a single object. Do NOT add any extra text."
        )

        all_questions = []
        previous_questions = set()  # Track question texts to avoid duplicates

        with Live(Spinner("dots", text=f"Generating questions for [cyan]{topic}[/]..."), refresh_per_second=10):
            while len(all_questions) < 3:
                if not previous_questions:
                    # First call, just use the topic
                    prompt_variation = topic
                else:
                    # Ask for a different question than the ones before
                    prompt_variation = f"{topic}. Ask a different question than before: avoid questions {list(previous_questions)}"
                
                data = self.client.generate_json(MODELS["generator"], prompt_variation, sys_prompt)
                if not data:
                    break

                for q in data:
                    # Only add if question text is new
                    if q["question"] not in previous_questions:
                        all_questions.append(q)
                        previous_questions.add(q["question"])
                    if len(all_questions) >= 3:
                        break

        # Trim to exactly 3 questions
        all_questions = all_questions[:3]

        try:
            questions = [Question(**q) for q in all_questions]
        except TypeError as e:
            self.console.print("[red]Error: Invalid question format from model[/red]")
            self.console.print(str(e))
            self.console.print(all_questions)
            self.console.input("\nPress Enter...")
            return

        session = QuizSession(questions)

        while not session.is_complete():
            q = session.current_question
            self.show_header(f"Question {session.current_index + 1} of {len(questions)}")
            
            q_text = f"**{q.question}**\n\n"
            for key, val in q.options.items():
                q_text += f"* **{key}**: {val}\n"
            
            self.console.print(Panel(Markdown(q_text), title=f"Score: {session.score}", border_style="cyan"))
            choice = self.console.input("\n[bold]Your Answer (A/B/C/D): [/bold]").upper()
            
            correct = session.process_answer(choice)
            color = "green" if correct else "red"
            msg = "✅ [bold]Correct![/bold]" if correct else f"❌ [bold]Incorrect![/bold] The answer was {q.correct_answer}."
            
            self.console.print(Panel(f"{msg}\n\n[italic]{q.explanation}[/italic]", border_style=color))
            self.console.input("\n[dim]Press Enter for next question...[/dim]")

    def run_tutor_mode(self):
        self.show_header("SOCRATIC TUTOR")
        self.console.print("[dim]The tutor will guide you. Type 'menu' to quit.[/dim]\n")
        
        # This list maintains the memory of the conversation
        history = [
            {"role": "system", "content": "You are a Socratic tutor. Never give answers directly. "
                                          "Instead, ask short, helpful questions to guide the student."}
        ]

        while True:
            user_input = self.console.input("[bold green]You: [/bold green]")
            if user_input.lower() in ['exit', 'menu']: break
            
            # 1. Add User input to history
            history.append({"role": "user", "content": user_input})
            
            with Live(Spinner("dots", text="Tutor is thinking...")):
                # 2. Send the FULL history to the AI
                response = self.client.chat(MODELS["tutor"], history)
            
            # 3. Add AI response to history
            history.append({"role": "assistant", "content": response})
            
            self.console.print(Panel(Markdown(response), title="Tutor", border_style="blue"))

    def run_code_mode(self):
        self.show_header("CODE ANALYZER")
        self.console.print("[yellow]Paste code (Ctrl+D / Ctrl+Z + Enter to submit):[/yellow]")
        code = sys.stdin.read()
        if not code.strip(): return

        history = [
            {"role": "system", "content": "Explain bugs and concepts in this code for a beginner."},
            {"role": "user", "content": code}
        ]

        with Live(Spinner("dots", text="Analyzing code...")):
            result = self.client.chat(MODELS["coder"], history)
        
        self.console.print(Panel(Markdown(result), title="Analysis", border_style="magenta"))
        self.console.input("\nPress Enter...")

    def main_menu(self):
        while True:
            self.show_header("AI TUTOR v4.0")
            menu = Table(show_header=False, box=None)
            menu.add_row("[cyan]1.[/]", "Practice Quiz Mode")
            menu.add_row("[cyan]2.[/]", "Socratic Tutoring (With Memory)")
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