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
    "coder": "qwen2.5:3b",
    "explainer": "llama3.2:3b"  # Explainer usually benefits from a general instructor model
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

# --- 2. API Client ---
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

# --- 3. Session Management ---
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

# --- 4. CLI Interface & Main App ---
class AITutorApp:
    def __init__(self):
        self.client = OllamaClient()
        self.console = Console()

    def show_header(self, title: str):
        self.console.clear()
        self.console.print(Panel(f"[bold blue]{title}[/bold blue]", expand=False))

    def enter_explainer_mode(self, context: str):
        """Reusable sub-mode to deep-dive into specific concepts."""
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
        """Standalone Explainer Feature."""
        self.show_header("CONCEPT EXPLAINER")
        topic = self.console.input("[bold magenta]What concept or topic should I explain? [/bold magenta]")
        if topic.strip():
            self.enter_explainer_mode(topic)

    def run_quiz_mode(self):
        self.show_header("PRACTICE QUIZ GENERATOR")
        topic = self.console.input("[bold yellow]What topic do you want to practice? [/bold yellow]")

        while True:
            try:
                num_questions = int(self.console.input("[bold yellow]How many questions? [/bold yellow]"))
                if num_questions > 0: break
            except ValueError:
                self.console.print("[red]Invalid input.[/red]")

        sys_prompt = (
            "Return ONLY a JSON ARRAY of MCQs. Format: "
            "{\"question\": \"...\", \"options\": {\"A\": \"...\"}, \"correct_answer\": \"A\", \"explanation\": \"...\"}"
        )

        all_questions = []
        with Live(Spinner("dots", text=f"Generating questions for [cyan]{topic}[/]...")):
            data = self.client.generate_json(MODELS["generator"], topic, sys_prompt)
            if data:
                all_questions = [Question(**q) for q in data[:num_questions]]

        if not all_questions:
            self.console.print("[red]Failed to generate questions.[/red]")
            return

        session = QuizSession(all_questions)

        while not session.is_complete():
            q = session.current_question
            self.show_header(f"Question {session.current_index + 1} of {len(all_questions)}")
            
            q_text = f"**{q.question}**\n\n"
            for key, val in q.options.items():
                q_text += f"* **{key}**: {val}\n"
            
            self.console.print(Panel(Markdown(q_text), title=f"Score: {session.score}", border_style="cyan"))
            
            # --- Explainer integration before answering ---
            choice = self.console.input("\n[bold]Answer (A/B/C/D) or type 'explain': [/bold]").upper()
            
            if choice == 'EXPLAIN':
                self.enter_explainer_mode(f"Topic: {topic}. Question: {q.question}")
                continue # Re-show question after explanation

            correct = session.process_answer(choice)
            color = "green" if correct else "red"
            msg = "✅ Correct!" if correct else f"❌ Incorrect! The answer was {q.correct_answer}."
            
            self.console.print(Panel(f"{msg}\n\n[italic]{q.explanation}[/italic]", border_style=color))
            
            # --- Explainer integration after answering ---
            post_action = self.console.input("\n[dim][Enter] Next | [E]xplain further: [/dim]").lower()
            if post_action == 'e':
                self.enter_explainer_mode(f"Context: {q.question}. Correct Answer: {q.correct_answer}. Explanation: {q.explanation}")
            
            session.next_question()

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
        self.console.print("[yellow]Paste the code and press Enter. Then, press Ctrl+D (on Linux/macOS) or Ctrl+Z (on Windows) to submit:[/yellow]")
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
            self.show_header("AI TUTOR v5.0")
            menu = Table(show_header=False, box=None)
            menu.add_row("[cyan]1.[/]", "Practice Quiz Mode")
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