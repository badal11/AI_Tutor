from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from config import MODELS
from ui.common import console
from services.ollama_client import OllamaClient

def enter_explainer_mode(client: OllamaClient, context: str):
    console.print(Panel("[bold magenta]EXPLORER MODE ACTIVATED[/]\n[dim]Type 'back' to return.[/]", border_style="magenta"))

    history = [{"role": "system", "content": f"You are a helpful assistant. Explain: {context}"}]

    while True:
        user_input = console.input("[bold magenta]Explain Mode > [/bold magenta]")
        if user_input.lower() in ['back', 'exit', 'quit']:
            break

        history.append({"role": "user", "content": user_input})
        with Live(Spinner("dots", text="Exploring...")):
            response = client.chat(MODELS["explainer"], history)

        history.append({"role": "assistant", "content": response})
        console.print(Panel(Markdown(response), border_style="magenta"))