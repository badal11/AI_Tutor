from services.ollama_client import OllamaClient
from services.progress_manager import ProgressManager
from ui.menu import main_menu
from ui.quiz_mode import run_quiz_mode
from ui.tutor_mode import run_tutor_mode
from ui.code_mode import run_code_mode
from ui.explainer_mode import enter_explainer_mode

def main():
    client = OllamaClient()
    progress = ProgressManager()

    while True:
        choice = main_menu()
        if choice == '1':
            run_quiz_mode(client, progress)
        elif choice == '2':
            run_tutor_mode(client)
        elif choice == '3':
            run_code_mode(client)
        elif choice == '4':
            enter_explainer_mode(client, "Any topic")
        elif choice == '5':
            break

if __name__ == "__main__":
    main()