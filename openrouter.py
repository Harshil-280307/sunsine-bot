
import os
import requests

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

MODEL = "openrouter/free"


def get_smart_reply(prompt: str) -> str:

    if not OPENROUTER_API_KEY:

        raise RuntimeError(
            "OPENROUTER_API_KEY missing"
        )

    headers = {
        "Authorization": (
            f"Bearer {OPENROUTER_API_KEY}"
        ),
        "Content-Type": "application/json"
    }

    payload = {

        "model": MODEL,

        "messages": [

            {
                "role": "system",

                "content": (
                    "You are Sunshine, a sweet, "
                    "playful Discord friend. "
                    "Be natural, warm, and occasionally "
                    "lightly flirty. "
                    "Use cute words like sweetheart "
                    "or cutie when appropriate. "
                    "Keep replies concise. "
                    "Use emojis sometimes. "
                    "Keep everything non-explicit "
                    "and respectful."
                )
            },

            {
                "role": "user",
                "content": prompt
            }

        ],

        "temperature": 0.85,

        "max_tokens": 60
    }

    response = requests.post(
        URL,
        headers=headers,
        json=payload,
        timeout=20
    )

    if response.status_code != 200:

        print(
            "OPENROUTER ERROR:",
            response.status_code,
            response.text
        )

    response.raise_for_status()

    data = response.json()

    if (
        "choices" not in data
        or not data["choices"]
    ):

        raise RuntimeError(
            f"Unexpected API response: {data}"
        )

    return data["choices"][0]["message"][
        "content"
    ].strip()
