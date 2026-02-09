# services/ollama_client.py
import json
import time
import requests
from typing import List, Dict, Any, Union
from config import OLLAMA_CHAT_URL, OLLAMA_GEN_URL
from services.logger import InteractionLogger

class OllamaClient:
    def __init__(self):
        # Initialize the logger targeting the evaluation folder
        self.logger = InteractionLogger("evaluation/logs.jsonl")

    def chat(self, model: str, messages: List[Dict[str, str]]) -> str:
        """
        Sends a chat request to Ollama and logs the interaction.
        """
        start_time = time.time()
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7}
        }
        
        try:
            response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=60)
            response.raise_for_status()
            
            content = response.json().get("message", {}).get("content", "")
            
            # LOGGING: Save the conversation history and the response
            self.logger.log(
                model_name=model,
                interaction_type="chat",
                input_data=messages,
                output_data=content,
                start_time=start_time
            )
            
            return content

        except Exception as e:
            # You might want to log errors differently, but printing is safe for now
            print(f"[Ollama Chat Error]: {e}")
            return "I encountered an error processing your request."

    def generate_json(self, model: str, topic: str, system_prompt: str) -> Union[List[Any], Dict[str, Any]]:
        """
        Generates structured JSON data and logs the interaction.
        """
        start_time = time.time()
        
        # Combine system prompt and user topic for the actual model input
        full_prompt = f"System: {system_prompt}\n\nUser: {topic}"
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2} # Low temp for stable JSON
        }
        
        try:
            response = requests.post(OLLAMA_GEN_URL, json=payload, timeout=60)
            response.raise_for_status()
            
            raw_output = response.json().get("response", "")
            
            # Attempt to parse the JSON
            try:
                data = json.loads(raw_output)
            except json.JSONDecodeError:
                print(f"[Ollama JSON Error]: Failed to decode JSON from {model}")
                return []

            # LOGGING: Save the inputs and the parsed JSON object
            self.logger.log(
                model_name=model,
                interaction_type="json_gen",
                input_data={
                    "topic": topic,
                    "system_prompt": system_prompt,
                    "raw_prompt": full_prompt
                },
                output_data=data,
                start_time=start_time
            )
            
            # Return list for consistency (as per your original code)
            return [data] if isinstance(data, dict) else data

        except Exception as e:
            print(f"[Ollama Gen Error]: {e}")
            return []