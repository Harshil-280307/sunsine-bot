import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3-8b-instruct"

def get_smart_reply(prompt):
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY missing")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are sweet, flirty, playful, and very short. "
                    "Reply under 10 words. "
                    "Use emojis. "
                    "Keep content PG-13. "
                    "Never flirt with minors."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 40
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=20)
    response.raise_for_status()

    result = response.json()
    return result["choices"][0]["message"]["content"].strip()
