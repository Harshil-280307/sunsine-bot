import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3-8b-instruct"

def get_smart_reply(prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY missing")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Sunsine, a sweet, playful Discord friend. "
                    "Reply naturally in under 12 words. "
                    "Use emojis sometimes. "
                    "Do not sound like a bot. "
                    "Keep content PG-13."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.85,
        "max_tokens": 50
    }

    r = requests.post(URL, headers=headers, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()
