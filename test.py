import json
import os
from datetime import datetime

# We use a simple library like 'requests' to talk to Ollama's local API
import requests

class AITutor:
    def __init__(self):
        self.url = "http://localhost:11434/api/generate"
        self.history = []
        self.models = {
            "tutor": "llama3.2:3b",
            "generator": "gemma2:2b",
            "coder": "qwen2.5:3b"
        }

    def query_local_llm(self, model, prompt, system_prompt=""):
        payload = {
            "model": model,
            "prompt": f"{system_prompt}\n\nUser: {prompt}",
            "stream": False,
            "context": self.history if model == self.models["tutor"] else []
        }
        try:
            response = requests.post(self.url, json=payload)
            return response.json().get("response", "Error: No response from model.")
        except Exception as e:
            return f"Connection Error: Ensure Ollama is running. {str(e)}"

    def question_generator(self):
        topic = input("\n[Gen] Enter topic for questions: ")
        sys_msg = "You are an educational assistant. Generate 5 multiple-choice questions for beginners."
        print("\n--- Generating Questions ---")
        result = self.query_local_llm(self.models["generator"], topic, sys_msg)
        print(result)

    def conversational_tutor(self):
        print("\n--- Tutor Mode (Type 'exit' to stop) ---")
        sys_msg = "You are a friendly Socratic tutor. Don't give answers immediately; guide the student."
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']: break
            response = self.query_local_llm(self.models["tutor"], user_input, sys_msg)
            print(f"\nTutor: {response}")

    def code_analyzer(self):
        print("\n--- Code Feedback Mode ---")
        print("Paste your code below (Press Ctrl+D or Ctrl+Z on Windows then Enter when done):")
        code = []
        while True:
            try: line = input(); code.append(line)
            except EOFError: break
        
        full_code = "\n".join(code)
        sys_msg = "Analyze this code for bugs and explain concepts simply for a beginner."
        result = self.query_local_llm(self.models["coder"], full_code, sys_msg)
        print("\n--- Feedback ---\n", result)

    def main_menu(self):
        while True:
            print("\n" + "="*20)
            print(" AI TUTOR CLI (OFFLINE)")
            print("="*20)
            print("1. Generate Questions (Gemma)")
            print("2. Start Tutoring Session (Llama)")
            print("3. Analyze Code (Qwen)")
            print("4. Exit")
            choice = input("\nSelect an option: ")

            if choice == '1': self.question_generator()
            elif choice == '2': self.conversational_tutor()
            elif choice == '3': self.code_analyzer()
            elif choice == '4': break
            else: print("Invalid choice.")

if __name__ == "__main__":
    tutor = AITutor()
    tutor.main_menu()