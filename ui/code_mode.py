import sys
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner

from config import MODELS
from ui.common import console, show_header
from ui.explainer_mode import enter_explainer_mode
from core.prompts import CODE_ANALYZER_PROMPT


def run_code_mode(client):
    show_header("CODE ANALYZER")
    console.print("[yellow]Paste code (Ctrl+D/Ctrl+Z to submit):[/yellow]")

    code = sys.stdin.read()
    if not code.strip():
        return

    history = [
        {"role": "system", "content": CODE_ANALYZER_PROMPT},
        {"role": "user", "content": code}
    ]

    with Live(Spinner("dots", text="Analyzing code...")):
        result = client.chat(MODELS["coder"], history)

    console.print(Panel(Markdown(result), title="Analysis", border_style="magenta"))

    while True:
        action = console.input("\n[dim][Enter] Menu | [E]xplain Code deeply: [/dim]").lower()
        if action == "e":
            enter_explainer_mode(client, f"Code Snippet:\n{code}\n\nAnalysis Provided:\n{result}")
        else:
            break