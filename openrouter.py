import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3-8b-instruct"  # stable + cheap

def get_smart_reply(prompt, style="sweet", mood="flirty"):
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
                    f"You are {style}, {mood}, playful, and very short. "
                    "Keep replies under 10 words. "
                    "Use emojis. "
                    "Never flirt with minors. "
                    "Keep content PG-13."
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

    if "choices" not in result:
        raise RuntimeError(f"Invalid OpenRouter response: {result}")

    return result["choices"][0]["message"]["content"].strip()
