# services/logger.py
import json
import time
import os
from datetime import datetime
from typing import Any, Dict

class InteractionLogger:
    def __init__(self, log_file="evaluation_data.jsonl"):
        # Ensure the evaluation directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.log_file = log_file

    def log(self, 
            model_name: str, 
            interaction_type: str, 
            input_data: Any, 
            output_data: Any, 
            start_time: float):
        """
        Logs an interaction to a JSONL file.
        """
        duration = time.time() - start_time
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "type": interaction_type,  # e.g., 'chat', 'quiz_gen'
            "latency_seconds": round(duration, 4),
            "input": input_data,
            "output": output_data
        }

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")