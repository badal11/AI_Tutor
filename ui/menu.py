from rich.table import Table
from ui.common import console, show_header

def main_menu():
    show_header("AI TUTOR v5.0 (ADAPTIVE)")
    menu = Table(show_header=False, box=None)
    menu.add_row("[cyan]1.[/]", "Practice Quiz Mode (Level-Aware)")
    menu.add_row("[cyan]2.[/]", "Socratic Tutoring")
    menu.add_row("[cyan]3.[/]", "Code Analysis")
    menu.add_row("[cyan]4.[/]", "Concept Explainer")
    menu.add_row("[red]5.[/]", "Exit")
    console.print(menu)
    return console.input("\n[bold]Select option: [/bold]")