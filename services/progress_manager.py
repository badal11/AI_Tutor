import json
import os

class ProgressManager:
    def __init__(self, filename="user_progress.json"):
        self.filename = filename
        self.data = self._load_data()

    def _load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"topics": {}}

    def get_topic_stats(self, topic: str):
        return self.data["topics"].get(topic.lower().strip(), {"level": 1, "history": []})

    def update_progress(self, topic: str, is_correct: bool):
        key = topic.lower().strip()
        self.data["topics"].setdefault(key, {"level": 1, "history": []})

        stats = self.data["topics"][key]
        stats["history"].append(is_correct)

        recent = stats["history"][-3:]
        if recent == [True, True, True]:
            stats["level"] += 1
            stats["history"] = []
        elif recent[-2:] == [False, False] and stats["level"] > 1:
            stats["level"] -= 1
            stats["history"] = []

        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=2)