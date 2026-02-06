from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner

from config import MODELS
from ui.common import console, show_header
from ui.explainer_mode import enter_explainer_mode


def run_tutor_mode(client):
    show_header("SOCRATIC TUTOR")
    console.print("[dim]Type 'explain' to switch to direct explanations or 'menu' to quit.[/dim]\n")

    history = [{"role": "system", "content": "Socratic tutor. Ask questions, don't give answers."}]

    while True:
        user_input = console.input("[bold green]You: [/bold green]")
        if user_input.lower() == "menu":
            break

        if user_input.lower() == "explain":
            last_msg = history[-1]["content"] if len(history) > 1 else "the current topic"
            enter_explainer_mode(client, last_msg)
            continue

        history.append({"role": "user", "content": user_input})

        with Live(Spinner("dots", text="Tutor is thinking...")):
            response = client.chat(MODELS["tutor"], history)

        history.append({"role": "assistant", "content": response})
        console.print(Panel(Markdown(response), title="Tutor", border_style="blue"))