"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# API keys - loaded from .env file
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

# Provider chains - STRICTLY using your list of models
PROVIDER_CHAINS = {
    "Team Elite": [
        "gemini/gemini-3-flash-preview",
        "openrouter/stepfun/step-3.5-flash:free",
        "cerebras/gpt-oss-120b",
        "google/gemini-2.5-flash"
    ],
    "Team Pro": [
        "google/gemini-2.5-flash-lite",
        "openrouter/nvidia/nemotron-nano-9b-v2:free",
        "cerebras/llama3.1-8b",
        "google/gemma-3-27b-it",
        "openrouter/google/gemma-3-27b-it:free"
    ],
    "Team Support": [
        "openrouter/arcee-ai/trinity-large-preview:free",
        "openrouter/liquid/lfm-2.5-1.2b-instruct:free",
        "google/gemma-3-4b",
        "openrouter/google/gemma-3-4b-it:free",
        "openrouter/openrouter/auto-router"
    ]
}

# Council members
COUNCIL_MODELS = [
    "Team Elite",
    "Team Pro",
    "Team Support"
]

# Chairman model - synthesizer
CHAIRMAN_MODEL = "Team Elite"



# Endpoints
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
CEREBRAS_API_URL = "https://api.cerebras.ai/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"

