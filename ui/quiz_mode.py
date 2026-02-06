from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner

from config import MODELS
from domain.models import Question
from domain.quiz_session import QuizSession
from ui.common import console, show_header
from ui.explainer_mode import enter_explainer_mode
from core.prompts import quiz_system_prompt, map_level_to_difficulty
from core.prompts import quiz_system_prompt, verification_prompt


def run_quiz_mode(client, progress):
    show_header("PRACTICE QUIZ GENERATOR")
    topic = console.input("[bold yellow]What topic do you want to practice? [/bold yellow]")

    stats = progress.get_topic_stats(topic)
    current_level = stats["level"]
    console.print(f"[dim]Current Proficiency Level for {topic}: {current_level}/10[/dim]")

    while True:
        try:
            num_questions = int(console.input("[bold yellow]How many questions do you want? [/bold yellow]"))
            if num_questions > 0:
                break
            console.print("[red]Please enter a positive number.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Enter a number.[/red]")

    all_questions = []
    previous_questions = set()

    with Live(Spinner("dots", text=f"Generating {num_questions} questions..."), refresh_per_second=10):
        while len(all_questions) < num_questions:
            # Prompt variation for diversity
            if not previous_questions:
                prompt_variation = topic
            else:
                prompt_variation = f"{topic}. Ask a different question than: {list(previous_questions)[-3:]}"

            # System prompt with descriptive difficulty
            sys_prompt = quiz_system_prompt(topic, current_level)

            # Generate question(s)
            data = client.generate_json(MODELS["generator"], prompt_variation, sys_prompt)
            if not data:
                break

            for q in data:
                if q["question"] in previous_questions:
                    continue

                verif_prompt = verification_prompt(q["question"], q["options"], q["correct_answer"])
                verification = client.generate_json(MODELS["explainer"], "", verif_prompt)
                if verification and isinstance(verification, list) and "correct_answer" in verification[0]:
                    q["correct_answer"] = verification[0]["correct_answer"]
                # Add to quiz
                all_questions.append(q)
                previous_questions.add(q["question"])

                if len(all_questions) >= num_questions:
                    break

    all_questions = all_questions[:num_questions]

    # Convert JSON to Question objects
    try:
        questions = [Question(**q) for q in all_questions]
    except TypeError:
        console.print("[red]Error: Invalid question format from model[/red]")
        return

    # --- Quiz session ---
    session = QuizSession(questions)

    while not session.is_complete():
        q = session.current_question
        show_header(f"Question {session.current_index + 1} of {len(questions)}")

        q_text = f"**{q.question}**\n\n"
        for key, val in q.options.items():
            q_text += f"* **{key}**: {val}\n"

        console.print(
            Panel(Markdown(q_text),
                  title=f"Score: {session.score} | Level: {current_level}",
                  border_style="cyan")
        )

        choice = console.input("\n[bold]Answer (A/B/C/D) or type 'explain': [/bold]").upper()

        if choice == "EXPLAIN":
            enter_explainer_mode(client, f"Topic: {topic}. Question: {q.question}")
            continue

        correct = session.process_answer(choice)
        progress.update_progress(topic, correct)

        color = "green" if correct else "red"
        msg = "✅ [bold]Correct![/bold]" if correct else f"❌ [bold]Incorrect![/bold] The answer was {q.correct_answer}."
        console.print(Panel(f"{msg}\n\n[italic]{q.explanation}[/italic]", border_style=color))

        post_action = console.input("\n[dim][Enter] Next | [E]xplain further: [/dim]").lower()
        if post_action == "e":
            enter_explainer_mode(
                client,
                f"Context: {q.question}. Correct Answer: {q.correct_answer}. Explanation: {q.explanation}"
            )

        session.next_question()

    console.print(f"\n[bold green]Quiz Complete! Final Score: {session.score}/{len(questions)}[/bold green]")
    console.input("[dim]Press Enter to return to main menu...[/dim]")