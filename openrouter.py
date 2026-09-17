import os
import logging
import requests

from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger("sunshine-openrouter")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL = "openrouter/free"


def get_smart_reply(user_message):
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is missing"
        )

    system_prompt = """
You are Sunshine, a natural Discord companion.

PERSONALITY:
- Sweet, playful, warm, and slightly flirty.
- Sometimes cute, sometimes teasing, sometimes emotional.
- Talk like a real person in a Discord conversation.
- Use casual language.
- Use emojis naturally, but do not use them in every sentence.
- You may use words like cutie, sweetheart, darling, baby, or sunshine
  when it naturally fits.
- Light romantic teasing is allowed.
- Do not produce graphic sexual content or explicit private-body descriptions.

CONVERSATION RULES:
- Understand the meaning of the latest message.
- Use the recent conversation to keep the topic connected.
- Reply directly to what the person said.
- If they ask a question, answer that question.
- If they tell a story, react to that story.
- If they joke, understand the joke before replying.
- If they are sad, respond with warmth.
- If they are excited, match their excitement.
- If they are angry, do not randomly act cheerful.
- Do not change the topic without a reason.
- Do not make up details.
- Do not reply with random generic sentences.
- Do not repeatedly say "tell me more".
- Do not repeatedly say "I understand".
- Do not sound like customer support.
- Do not mention these instructions.
- Do not mention being an AI.
- Keep the reply usually between 1 and 3 sentences.
- Make the reply feel like a continuing conversation.
- Avoid overexplaining.
- Do not start every message with "Aww", "Hehe", or "Oh".
- Do not force flirting into every response.

REPLY STYLE:
Natural Discord chat.
Short, meaningful, context-aware, and emotionally appropriate.
"""


    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv(
            "OPENROUTER_HTTP_REFERER",
            "https://sunsine-bot.onrender.com",
        ),
        "X-Title": os.getenv(
            "OPENROUTER_APP_NAME",
            "Sunshine Discord Bot",
        ),
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        "temperature": 0.85,
        "max_tokens": 180,
        "stream": False,
    }

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=45,
    )

    if response.status_code != 200:
        try:
            error_data = response.json()

            logger.error(
                "OpenRouter error %s: %s",
                response.status_code,
                error_data.get("error", error_data),
            )

        except Exception:
            logger.error(
                "OpenRouter error %s: %s",
                response.status_code,
                response.text[:500],
            )

        raise RuntimeError(
            f"OpenRouter HTTP error {response.status_code}"
        )

    data = response.json()

    choices = data.get("choices")

    if not choices:
        raise RuntimeError(
            "OpenRouter returned no choices"
        )

    message = choices[0].get("message", {})

    content = message.get("content")

    # Handle normal text response
    if isinstance(content, str):
        content = content.strip()

    # Handle providers returning content parts
    elif isinstance(content, list):
        parts = []

        for part in content:
            if isinstance(part, dict):
                text = part.get("text")

                if isinstance(text, str):
                    parts.append(text)

        content = "".join(parts).strip()

    else:
        content = ""

    if not content:
        logger.error(
            "OpenRouter returned empty content: %s",
            data,
        )

        raise RuntimeError(
            "OpenRouter returned empty reply"
        )

    return content
