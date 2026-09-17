
import os
import json
import logging
import requests

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL = "openrouter/free"

logging.basicConfig(level=logging.INFO)


def call_openrouter(
    messages,
    temperature=0.85,
    max_tokens=100
):

    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY missing"
        )

    headers = {
        "Authorization": (
            f"Bearer {OPENROUTER_API_KEY}"
        ),
        "Content-Type": "application/json",
        "HTTP-Referer": (
            "https://sunsine-bot.onrender.com"
        ),
        "X-Title": "Sunshine Discord Bot"
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    response = requests.post(
        URL,
        headers=headers,
        json=payload,
        timeout=45
    )

    if response.status_code != 200:

        logging.error(
            "OpenRouter error %s: %s",
            response.status_code,
            response.text[:1000]
        )

    response.raise_for_status()

    data = response.json()

    choices = data.get("choices")

    if not choices:
        raise RuntimeError(
            f"No choices in response: {data}"
        )

    message = choices[0].get("message") or {}

    content = message.get("content")

    if not isinstance(content, str):
        raise RuntimeError(
            f"AI returned no text: {data}"
        )

    content = content.strip()

    if not content:
        raise RuntimeError(
            "AI returned empty content"
        )

    return content


def get_smart_reply(prompt: str) -> str:

    messages = [

        {
            "role": "system",
            "content": (
                "You are Sunshine, a sweet, "
                "playful Discord friend. "
                "Be natural, affectionate, "
                "and occasionally flirty. "
                "Use cute words when appropriate. "
                "You may use light romantic teasing "
                "but never graphic sexual content. "
                "Keep replies concise. "
                "Use emojis sometimes. "
                "Do not sound robotic."
            )
        },

        {
            "role": "user",
            "content": prompt
        }

    ]

    return call_openrouter(
        messages,
        temperature=0.85,
        max_tokens=100
    )


def should_reply(
    conversation: str
) -> bool:

    messages = [

        {
            "role": "system",
            "content": (
                "You are Sunshine's conversation "
                "decision engine. "
                "Decide whether Sunshine should "
                "reply to a Discord group message. "
                "Reply YES when the conversation "
                "invites participation, asks a "
                "question, includes a joke, or "
                "would benefit from a natural "
                "playful response. "
                "Reply NO when the message is "
                "routine, already answered, "
                "spam, or does not need Sunshine. "
                "Return ONLY YES or NO."
            )
        },

        {
            "role": "user",
            "content": conversation
        }

    ]

    result = call_openrouter(
        messages,
        temperature=0.2,
        max_tokens=5
    )

    result = result.upper().strip()

    return result.startswith("YES")
