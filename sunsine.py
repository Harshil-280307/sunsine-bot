
import os
import time
import random
import asyncio
import logging
import threading
from collections import deque

from dotenv import load_dotenv
import discord
from discord.ext import commands

from openrouter import get_smart_reply
from web import run_web

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN missing")

# ---------- LOGGING ----------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s"
)

# ---------- DISCORD ----------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ---------- STATE ----------
bot_enabled_channels = set()
cooldowns = {}

COOLDOWN_SECONDS = 8
CHANNEL_CONTEXT_LIMIT = 8

channel_context = {}

# ---------- FALLBACK ----------
try:
    with open(
        "fallback_sweet_replies.txt",
        encoding="utf-8"
    ) as f:
        FALLBACK = [
            line.strip()
            for line in f
            if line.strip()
        ]

except Exception:
    FALLBACK = [
        "Hey sunshine ☀️",
        "I'm hereee ✨",
        "What's happening? 🌞",
        "Hehe, tell me more 💛"
    ]

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    logging.info(
        f"🌞 Sunsine online as {bot.user}"
    )

# ---------- COMMAND ----------
@bot.command()
async def sunshine(ctx, mode: str = None):

    if mode is None:
        await ctx.send(
            "Use `!sunshine on` or `!sunshine off`"
        )
        return

    mode = mode.lower()

    if mode == "on":

        bot_enabled_channels.add(ctx.channel.id)

        await ctx.send(
            "Sunsine is glowing 🌞✨"
        )

        logging.info(
            f"Enabled channel: {ctx.channel.id}"
        )

    elif mode == "off":

        bot_enabled_channels.discard(
            ctx.channel.id
        )

        await ctx.send(
            "Sunsine is going quiet 🌙💤"
        )

    else:

        await ctx.send(
            "Use `!sunshine on` or `!sunshine off`"
        )

# ---------- MESSAGE LISTENER ----------
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    # Always process commands
    await bot.process_commands(message)

    cid = message.channel.id

    if cid not in bot_enabled_channels:
        return

    # Initialize memory
    if cid not in channel_context:
        channel_context[cid] = deque(
            maxlen=CHANNEL_CONTEXT_LIMIT
        )

    channel_context[cid].append(
        f"{message.author.display_name}: "
        f"{message.content}"
    )

    logging.info(
        f"Message received in enabled channel: {cid}"
    )

    await maybe_reply(message, cid)

# ---------- DECISION ----------
async def maybe_reply(message, cid):

    now = time.time()

    # Cooldown
    if now - cooldowns.get(cid, 0) < COOLDOWN_SECONDS:
        logging.info("Cooldown active")
        return

    text = message.content.lower()

    # Ignore commands
    if text.startswith("!"):
        return

    # TEMPORARY: Do not ignore short messages
    # We want to test replies first.

    # Reply chance
    if bot.user and bot.user.mentioned_in(message):
        chance = 1.0

    elif "sunshine" in text or "sunsine" in text:
        chance = 1.0

    else:
        chance = 0.9

    if random.random() > chance:
        logging.info("Random chance skipped reply")
        return

    cooldowns[cid] = now

    await reply_with_context(message, cid)

# ---------- AI REPLY ----------
async def reply_with_context(message, cid):

    history = "\n".join(
        channel_context[cid]
    )

    prompt = (
        "You are chatting in a Discord group.\n"
        "Reply naturally as part of the conversation.\n"
        "Do not repeat others.\n\n"
        f"Conversation:\n{history}\n\n"
        "Your reply:"
    )

    reply = None

    try:

        logging.info("Calling OpenRouter...")

        loop = asyncio.get_running_loop()

        reply = await loop.run_in_executor(
            None,
            get_smart_reply,
            prompt
        )

        if not reply:
            raise RuntimeError(
                "OpenRouter returned an empty reply"
            )

        logging.info(
            f"AI reply received: {reply}"
        )

    except Exception as e:

        logging.exception(
            f"AI error: {e}"
        )

        reply = random.choice(FALLBACK)

        logging.info(
            f"Using fallback: {reply}"
        )

    try:

        await message.channel.send(reply)

        logging.info("Reply sent successfully")

    except Exception as e:

        logging.exception(
            f"Discord send error: {e}"
        )

# ---------- START WEB + BOT ----------
threading.Thread(
    target=run_web,
    daemon=True
).start()

bot.run(TOKEN)
