import json
import requests
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown

console = Console()

class AITutor:
    def __init__(self):
        self.url = "http://localhost:11434/api/generate"
        self.models = {
            "tutor": "llama3.2:3b",
            "generator": "gemma2:2b",
            "coder": "qwen2.5:3b"
        }

    def _call_ollama(self, model, prompt, system_prompt=""):
        """Internal helper to handle requests with a loading spinner."""
        payload = {
            "model": model,
            "prompt": f"{system_prompt}\n\nUser: {prompt}",
            "stream": False
        }
        
        try:
            with Live(Spinner("dots", text=f"Thinking ([bold cyan]{model}[/])..."), refresh_per_second=10):
                response = requests.post(self.url, json=payload, timeout=30)
                response.raise_for_status()
            return response.json().get("response", "Error: No response content.")
        except requests.exceptions.ConnectionError:
            return "[bold red]Error:[/bold red] Could not connect to Ollama. Is it running?"
        except Exception as e:
            return f"[bold red]Error:[/bold red] {str(e)}"

    def show_header(self, title):
        console.clear()
        console.print(Panel(f"[bold blue]{title}[/bold blue]", expand=False))

    def question_generator(self):
        self.show_header("QUESTION GENERATOR")
        topic = console.input("[bold yellow]Enter a topic to practice:[/bold yellow] ")
        if not topic.strip(): return

        sys_msg = "You are an educational assistant. Generate 5 multiple-choice questions for beginners. Format with Markdown."
        result = self._call_ollama(self.models["generator"], topic, sys_msg)
        console.print(Markdown(result))
        console.input("\n[dim]Press Enter to return to menu...[/dim]")

    def conversational_tutor(self):
        self.show_header("SOCRATIC TUTOR MODE")
        console.print("[dim]Type 'exit' or 'menu' to return home.[/dim]\n")
        sys_msg = "You are a friendly Socratic tutor. Guide the student with questions; don't just give answers."
        
        while True:
            user_input = console.input("[bold green]You:[/bold green] ")
            if user_input.lower() in ['exit', 'quit', 'menu']: break
            
            response = self._call_ollama(self.models["tutor"], user_input, sys_msg)
            console.print(Panel(Markdown(response), title="Tutor", title_align="left", border_style="blue"))

    def code_analyzer(self):
        self.show_header("CODE ANALYZER")
        console.print("[yellow]Paste your code (Press Ctrl+D/Ctrl+Z + Enter when finished):[/yellow]\n")
        
        try:
            code_lines = sys.stdin.read()
            if not code_lines.strip(): return
        except EOFError:
            return

        sys_msg = "Analyze this code for bugs and explain concepts simply for a beginner. Use Markdown."
        result = self._call_ollama(self.models["coder"], code_lines, sys_msg)
        console.print(Panel(Markdown(result), title="Analysis", border_style="magenta"))
        console.input("\n[dim]Press Enter to return to menu...[/dim]")

    def main_menu(self):
        while True:
            self.show_header("AI TUTOR SYSTEM v2.0")
            
            table = Table(show_header=False, box=None)
            table.add_row("[bold cyan]1.[/bold cyan]", "Generate Practice Questions")
            table.add_row("[bold cyan]2.[/bold cyan]", "Interactive Socratic Tutoring")
            table.add_row("[bold cyan]3.[/bold cyan]", "Analyze Code Snippets")
            table.add_row("[bold red]4.[/bold red]", "Exit")
            
            console.print(table)
            choice = console.input("\n[bold]Select an option:[/bold] ")

            if choice == '1': self.question_generator()
            elif choice == '2': self.conversational_tutor()
            elif choice == '3': self.code_analyzer()
            elif choice == '4': 
                console.print("[italic]Goodbye![/italic]")
                break
            else:
                console.print("[red]Invalid selection, try again.[/red]")

if __name__ == "__main__":
    tutor = AITutor()
    tutor.main_menu()