# ui/cli.py
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.live import Live

from services.ollama_client import OllamaClient
from services.progress_manager import ProgressManager
from domain.quiz_session import QuizSession
from core.prompts import quiz_prompt
from config import MODELS
from domain.models import Question

class AITutorCLI:
    def __init__(self):
        self.console = Console()
        self.client = OllamaClient()
        self.progress = ProgressManager()

    def header(self, title: str):
        self.console.clear()
        self.console.print(Panel(title, style="bold cyan"))

    def explain_mode(self, context: str):
        history = [{"role": "system", "content": f"Explain deeply: {context}"}]
        while True:
            q = self.console.input("Explain > ")
            if q.lower() in ("exit", "back"):
                break
            history.append({"role": "user", "content": q})
            with Live(Spinner("dots", text="Thinking...")):
                answer = self.client.chat(MODELS["explainer"], history)
            self.console.print(Panel(Markdown(answer)))