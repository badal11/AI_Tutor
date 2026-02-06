from rich.console import Console
from rich.panel import Panel

console = Console()

def show_header(title: str):
    console.clear()
    console.print(Panel(f"[bold blue]{title}[/bold blue]", expand=False))