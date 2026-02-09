import os
import json
import time
import google.generativeai as genai
from typing import List, Dict, Any, Union
from dotenv import load_dotenv
from services.logger import InteractionLogger

load_dotenv()

class GeminiClient:
    def __init__(self):
        # Setup the API
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        
        genai.configure(api_key=api_key)
        self.default_model_name = "gemini-2.5-flash"
        
        # Initialize the logger
        self.logger = InteractionLogger("evaluation/logs.jsonl")

    def chat(self, model_name: str, messages: List[Dict[str, str]]) -> str:
        start_time = time.time()
        
        history = []
        for msg in messages[:-1]:
            role = "model" if msg["role"] == "assistant" else "user"
            history.append({"role": role, "parts": [msg["content"]]})
        
        # Use the model_name passed in, or fallback to default if None/Empty
        target_model = model_name if model_name else self.default_model_name
        
        try:
            model = genai.GenerativeModel(target_model)
            chat_session = model.start_chat(history=history)
            
            last_message = messages[-1]["content"]
            response = chat_session.send_message(
                last_message, 
                generation_config={"temperature": 0.7}
            )
            
            content = response.text
            
            # LOGGING
            self.logger.log(
                model_name=target_model,
                interaction_type="chat",
                input_data=messages,
                output_data=content,
                start_time=start_time
            )
            
            return content
            
        except Exception as e:
            print(f"[Gemini Chat Error]: {e}")
            return "I encountered an error processing your request."

    def generate_json(self, model_name: str, topic: str, system_prompt: str) -> Union[List[Any], Dict[str, Any]]:
        start_time = time.time()
        
        target_model = model_name if model_name else self.default_model_name
        
        try:
            model = genai.GenerativeModel(
                model_name=target_model,
                system_instruction=system_prompt
            )
            
            # Gemini throws an error if the user prompt (topic) is empty.
            prompt_content = topic if topic.strip() else "Please generate the requested JSON data based on your instructions."
            
            response = model.generate_content(
                prompt_content,
                generation_config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json"
                }
            )
            
            # Parse response
            data = json.loads(response.text)
            
            # LOGGING
            self.logger.log(
                model_name=target_model,
                interaction_type="json_gen",
                input_data={
                    "topic": prompt_content,
                    "system_prompt": system_prompt
                },
                output_data=data,
                start_time=start_time
            )
            
            return [data] if isinstance(data, dict) else data
            
        except Exception as e:
            print(f"[Gemini JSON Error]: {e}")
            return []