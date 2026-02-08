# config.py
USE_LOCAL_MODELS = False  # set True for Ollama/local, False for Gemini

LOCAL_MODELS = {
    "tutor": "llama3.2:3b",
    "generator": "gemma2:2b",
    "coder": "qwen2.5:3b",
    "explainer": "llama3.2:3b"
}

CLOUD_MODELS = {
    "tutor": "gemini-2.5-flash",
    "generator": "gemini-2.5-flash",
    "coder": "gemini-2.5-flash",
    "explainer": "gemini-2.5-flash"
}


MODELS = LOCAL_MODELS if USE_LOCAL_MODELS else CLOUD_MODELS


OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_GEN_URL = "http://localhost:11434/api/generate"