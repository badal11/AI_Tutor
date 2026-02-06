import json
import requests
from typing import List, Dict
from config import OLLAMA_CHAT_URL, OLLAMA_GEN_URL

class OllamaClient:
    def chat(self, model: str, messages: List[Dict[str, str]]) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7}
        }
        response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")

    def generate_json(self, model: str, topic: str, system_prompt: str):
        payload = {
            "model": model,
            "prompt": f"System: {system_prompt}\n\nUser: {topic}",
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2}
        }
        response = requests.post(OLLAMA_GEN_URL, json=payload, timeout=60)
        response.raise_for_status()
        raw_output = response.json().get("response", "")
        data = json.loads(raw_output)
        return [data] if isinstance(data, dict) else data