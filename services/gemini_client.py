import os
import json
import google.generativeai as genai
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    def __init__(self):
        # Setup the API
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        
        genai.configure(api_key=api_key)
        self.model_name = "gemini-2.5-flash"

    def chat(self, model_name: str, messages: List[Dict[str, str]]) -> str:
        history = []
        for msg in messages[:-1]:
            role = "model" if msg["role"] == "assistant" else "user"
            history.append({"role": role, "parts": [msg["content"]]})
        
        # Use the model_name passed in the argument
        model = genai.GenerativeModel(model_name)
        chat_session = model.start_chat(history=history)
        
        last_message = messages[-1]["content"]
        response = chat_session.send_message(
            last_message, 
            generation_config={"temperature": 0.7}
        )
        return response.text

    def generate_json(self, model_name: str, topic: str, system_prompt: str):
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt
        )
        
        # Gemini throws an error if the user prompt (topic) is empty.
        # We provide a default instruction if topic is empty.
        prompt_content = topic if topic.strip() else "Please generate the requested JSON data based on your instructions."
        
        response = model.generate_content(
            prompt_content,
            generation_config={
                "temperature": 0.2,
                "response_mime_type": "application/json"
            }
        )
        
        data = json.loads(response.text)
        return [data] if isinstance(data, dict) else data