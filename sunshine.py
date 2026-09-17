import os
import asyncio
import random
import logging
from threading import Thread
from collections import defaultdict, deque

import discord
from flask import Flask
from dotenv import load_dotenv

from openrouter import get_smart_reply


# ==================================================
# Environment
# ==================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_BOT_TOKEN is missing. Add it in Render Environment."
    )


# ==================================================
# Logging
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)

logger = logging.getLogger("sunshine-bot")


# ==================================================
# Flask Keep-Alive Server
# ==================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "Sunshine Bot is running! 🌞", 200


@app.route("/health")
def health():
    return {
        "status": "online",
        "bot": "Sunshine",
    }, 200


def run_flask():
    port = int(os.getenv("PORT", "8080"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


flask_thread = Thread(
    target=run_flask,
    daemon=True,
)

flask_thread.start()


# ==================================================
# Discord Setup
# ==================================================

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)


# ==================================================
# Sunshine Variables
# ==================================================

sunshine_mode = True

# 0.30 means 30% chance of replying
reply_chance = 0.30

# Prevent too many replies in a short time
reply_cooldown = 8

last_reply_time = defaultdict(float)

# Prevent multiple replies in the same channel
active_channels = set()

# Keep recent conversation for each channel
conversation_memory = defaultdict(
    lambda: deque(maxlen=12)
)


# ==================================================
# Sunshine Personality Helpers
# ==================================================

def style_reply(reply):
    """
    Cleans and styles the AI reply.
    """

    if not reply:
        return "My brain just took a tiny vacation 🌞"

    reply = str(reply).strip()

    if not reply:
        return "Wait, my brain is buffering 😭"

    # Keep Discord replies short
    if len(reply) > 1800:
        reply = reply[:1797].rstrip() + "..."

    return reply


def clean_bot_mentions(content):
    """
    Removes Sunshine mentions from the message.
    """

    if not client.user:
        return content

    content = content.replace(
        f"<@{client.user.id}>",
        "",
    )

    content = content.replace(
        f"<@!{client.user.id}>",
        "",
    )

    return content.strip()


def is_directly_mentioned(message):
    if not client.user:
        return False

    return client.user in message.mentions


def format_message(message):
    """
    Converts a Discord message into readable conversation text.
    """

    author = message.author.display_name
    content = message.content.strip()

    if not content:
        return ""

    return f"{author}: {content}"


def build_conversation(channel_id):
    """
    Builds recent conversation context for the AI.
    """

    history = conversation_memory[channel_id]

    if not history:
        return ""

    return "\n".join(history)


def should_ignore_message(content):
    """
    Avoids replying to empty or useless messages.
    """

    if not content:
        return True

    if len(content.strip()) < 2:
        return True

    return False


# ==================================================
# Sunshine Commands
# ==================================================

async def handle_command(message, content_lower):
    global sunshine_mode
    global reply_chance
    global reply_cooldown

    if content_lower == "!sunshine off":
        sunshine_mode = False

        await message.channel.send(
            "Okayyy, I’ll be quiet now 😌"
        )

        return True

    if content_lower == "!sunshine on":
        sunshine_mode = True

        await message.channel.send(
            "Sunshine is awake again 🌞✨"
        )

        return True

    if content_lower == "!sunshine status":
        await message.channel.send(
            f"🌞 Sunshine status\n"
            f"Mode: `{sunshine_mode}`\n"
            f"Reply chance: `{reply_chance * 100:.0f}%`\n"
            f"Cooldown: `{reply_cooldown} seconds`"
        )

        return True

    if content_lower.startswith("!sunshine chance"):
        try:
            parts = content_lower.split()

            if len(parts) < 3:
                raise ValueError

            new_chance = float(parts[2])

            if not 0 <= new_chance <= 1:
                raise ValueError

            reply_chance = new_chance

            await message.channel.send(
                f"✨ Reply chance set to "
                f"`{reply_chance * 100:.0f}%`"
            )

        except ValueError:
            await message.channel.send(
                "Use it like `!sunshine chance 0.3`"
            )

        return True

    if content_lower.startswith("!sunshine cooldown"):
        try:
            parts = content_lower.split()

            if len(parts) < 3:
                raise ValueError

            new_cooldown = int(parts[2])

            if not 0 <= new_cooldown <= 300:
                raise ValueError

            reply_cooldown = new_cooldown

            await message.channel.send(
                f"⏱️ Cooldown set to `{reply_cooldown} seconds`"
            )

        except ValueError:
            await message.channel.send(
                "Use it like `!sunshine cooldown 8`"
            )

        return True

    return False


# ==================================================
# Sunshine AI Reply
# ==================================================

async def reply_to_message(message, ai_content, conversation):
    channel_id = message.channel.id

    if channel_id in active_channels:
        return

    active_channels.add(channel_id)

    try:
        # The prompt includes both history and latest message
        full_prompt = f"""
RECENT DISCORD CONVERSATION:
{conversation}

LATEST MESSAGE:
{ai_content}

Reply naturally to the latest message while remembering the conversation.
"""

        logger.info(
            "Sunshine is thinking about: %s",
            ai_content[:200],
        )

        async with message.channel.typing():
            raw_reply = await get_smart_reply(full_prompt)

        final_reply = style_reply(raw_reply)

        if not final_reply:
            return

        await message.channel.send(
            final_reply,
            reference=message,
            mention_author=False,
        )

        logger.info(
            "Sunshine replied: %s",
            final_reply[:200],
        )

    except discord.Forbidden:
        logger.error(
            "Sunshine does not have permission to send messages."
        )

    except discord.HTTPException as error:
        logger.error(
            "Discord HTTP error: %s",
            error,
        )

    except Exception:
        logger.exception(
            "Sunshine AI reply failed"
        )

    finally:
        active_channels.discard(channel_id)


# ==================================================
# Discord Events
# ==================================================

@client.event
async def on_ready():
    logger.info(
        "🌞 Sunshine is online as %s",
        client.user,
    )


@client.event
async def on_message(message):
    global sunshine_mode

    try:
        # Ignore every bot, including Sunshine itself
        if message.author.bot:
            return

        content = message.content.strip()

        if not content:
            return

        content_lower = content.lower()

        # Handle commands first
        if content_lower.startswith("!sunshine"):
            await handle_command(
                message,
                content_lower,
            )
            return

        if not sunshine_mode:
            return

        # Remove Sunshine mention
        ai_content = clean_bot_mentions(content)

        if should_ignore_message(ai_content):
            return

        channel_id = message.channel.id

        # Save the user's message before generating a reply
        formatted_user_message = format_message(message)

        if formatted_user_message:
            conversation_memory[channel_id].append(
                formatted_user_message
            )

        mentioned = is_directly_mentioned(message)

        # Direct mention always gets a chance to reply
        if not mentioned:
            random_chance = random.random() < reply_chance

            if not random_chance:
                logger.info(
                    "Skipped message due to reply chance: %s",
                    ai_content[:100],
                )
                return

        # Cooldown check
        current_time = asyncio.get_running_loop().time()
        previous_reply = last_reply_time[channel_id]

        if current_time - previous_reply < reply_cooldown:
            return

        # Reserve the channel before calling AI
        last_reply_time[channel_id] = current_time

        conversation = build_conversation(channel_id)

        await reply_to_message(
            message,
            ai_content,
            conversation,
        )

        # Save Sunshine's reply into memory
        # This happens after the reply function completes.
        # The actual AI response is not returned here, so the next
        # user message still has the latest user context.

    except Exception:
        logger.exception(
            "Error inside Sunshine on_message"
        )


# ==================================================
# Start Bot
# ==================================================

try:
    client.run(TOKEN)

except Exception:
    logger.exception(
        "Error running Sunshine"
    )
