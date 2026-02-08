import json
import os
import sys
from dataclasses import dataclass
from typing import List, Dict

# Google Gemini & UI
import google.generativeai as genai
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown

# --- Configuration ---
GOOGLE_API_KEY = ""
genai.configure(api_key=GOOGLE_API_KEY)

# Using Gemini 2.5 Flash for the best speed/free-tier balance
MODEL_NAME = 'gemini-2.5-flash'

# --- 1. Data Structure ---
@dataclass
class Question:
    question: str
    options: Dict[str, str]
    correct_answer: str
    explanation: str

# --- 2. Adaptive Progress Manager ---
class ProgressManager:
    def __init__(self, filename="user_progress.json"):
        self.filename = filename
        self.data = self._load_data()

    def _load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except: pass
        return {"topics": {}}

    def get_level(self, topic: str) -> int:
        return self.data["topics"].get(topic.lower(), {}).get("level", 1)

    def update(self, topic: str, is_correct: bool):
        topic = topic.lower()
        if topic not in self.data["topics"]:
            self.data["topics"][topic] = {"level": 1, "history": []}
        
        stats = self.data["topics"][topic]
        stats["history"].append(is_correct)
        
        # Level up on 3 correct, Level down on 2 wrong
        if stats["history"][-3:] == [True, True, True]:
            stats["level"] = min(stats["level"] + 1, 10)
            stats["history"] = []
        elif stats["history"][-2:] == [False, False]:
            stats["level"] = max(stats["level"] - 1, 10)
            stats["history"] = []
        
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

# --- 3. Gemini Tutor App ---
class GeminiTutor:
    def __init__(self):
        self.model = genai.GenerativeModel(MODEL_NAME)
        self.console = Console()
        self.progress = ProgressManager()
        self.chat = self.model.start_chat(history=[])

    def show_header(self, text: str, style="bold blue"):
        self.console.clear()
        self.console.print(Panel(text, style=style, expand=False))

    def run_quiz(self):
        self.show_header("GEMINI FLASH QUIZ")
        topic = self.console.input("[bold yellow]What topic are we mastering today? [/]")
        level = self.progress.get_level(topic)
        
        prompt = f"""
        Generate a 3-question quiz on {topic} for a Level {level}/10 student.
        Return ONLY a JSON object with this exact structure:
        {{
            "questions": [
                {{
                    "question": "string",
                    "options": {{"A": "str", "B": "str", "C": "str", "D": "str"}},
                    "correct_answer": "A, B, C, or D",
                    "explanation": "string"
                }}
            ]
        }}
        """

        with Live(Spinner("bouncingBar", text=f"Gemini is crafting Level {level} questions...")):
            # response_mime_type ensures valid JSON every time
            response = self.model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            quiz_data = json.loads(response.text)

        for i, q_raw in enumerate(quiz_data['questions']):
            q = Question(**q_raw)
            self.show_header(f"Question {i+1} (Level {level})", style="cyan")
            
            # Display Question
            q_text = f"### {q.question}\n\n" + "\n".join([f"* **{k}**: {v}" for k, v in q.options.items()])
            self.console.print(Markdown(q_text))
            
            user_ans = self.console.input("\n[bold]Your choice (A/B/C/D): [/]").upper()
            is_correct = user_ans == q.correct_answer
            self.progress.update(topic, is_correct)

            # Feedback
            res_style = "green" if is_correct else "red"
            msg = "🌟 Correct!" if is_correct else f"❌ Not quite. The answer was {q.correct_answer}."
            self.console.print(Panel(f"{msg}\n\n{q.explanation}", border_style=res_style))
            self.console.input("[dim]Press Enter to continue...[/]")

    def run_tutor(self):
        self.show_header("SOCRATIC TUTOR (FREE TIER)", style="green")
        self.console.print("[dim]I'll help you find answers yourself. Type 'quit' to exit.[/]\n")
        
        # Set the persona
        chat = self.model.start_chat(history=[
            {"role": "user", "parts": "You are a Socratic Tutor. Never give direct answers. Ask guiding questions."}
        ])

        while True:
            user_input = self.console.input("[bold green]You > [/]")
            if user_input.lower() in ['quit', 'exit']: break
            
            with Live(Spinner("dots", text="Gemini is thinking...")):
                response = chat.send_message(user_input)
            
            self.console.print(Panel(Markdown(response.text), title="Tutor", border_style="blue"))

    def menu(self):
        while True:
            self.show_header("AI TUTOR v6.0 (GEMINI FLASH)")
            self.console.print("1. [bold cyan]Adaptive Quiz[/]\n2. [bold green]Socratic Chat[/]\n3. [bold red]Exit[/]")
            choice = self.console.input("\n[bold]Select: [/]")
            if choice == '1': self.run_quiz()
            elif choice == '2': self.run_tutor()
            elif choice == '3': break

if __name__ == "__main__":
    # Ensure you set your API key
    if GOOGLE_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("Please insert your Gemini API Key from https://aistudio.google.com/")
    else:
        app = GeminiTutor()
        app.menu()