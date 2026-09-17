
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


# =====================================================
# CONFIG
# =====================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_BOT_TOKEN missing"
    )


# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s"
)


# =====================================================
# DISCORD
# =====================================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =====================================================
# STATE
# =====================================================

enabled_channels = set()

channel_context = {}

cooldowns = {}

channel_settings = {}

DEFAULT_REPLY_CHANCE = 30
DEFAULT_COOLDOWN = 8

CONTEXT_LIMIT = 12


def get_settings(cid):

    if cid not in channel_settings:
        channel_settings[cid] = {
            "chance": DEFAULT_REPLY_CHANCE,
            "cooldown": DEFAULT_COOLDOWN
        }

    return channel_settings[cid]


# =====================================================
# FALLBACK
# =====================================================

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
        "Heyyy sunshine 🌞",
        "I'm listening, cutie ✨",
        "Ooo tell me more 😏",
        "Hehe, you're funny 💛",
        "What are you up to, sweetheart? ☀️"
    ]


# =====================================================
# READY
# =====================================================

@bot.event
async def on_ready():

    logging.info(
        f"🌞 Sunshine online as {bot.user}"
    )


# =====================================================
# SUNSHINE COMMAND
# =====================================================

@bot.command()
async def sunshine(ctx, mode: str = None):

    if mode is None:

        await ctx.send(
            "Use `!sunshine on`, `!sunshine off`, "
            "or `!sunshine status`"
        )

        return

    mode = mode.lower()

    if mode == "on":

        enabled_channels.add(ctx.channel.id)

        await ctx.send(
            "Sunshine is glowing 🌞✨"
        )

    elif mode == "off":

        enabled_channels.discard(
            ctx.channel.id
        )

        await ctx.send(
            "Going quiet... but I'll be here 🌙"
        )

    elif mode == "status":

        settings = get_settings(
            ctx.channel.id
        )

        await ctx.send(
            f"🌞 **Sunshine status**\n"
            f"Enabled: "
            f"{ctx.channel.id in enabled_channels}\n"
            f"Reply chance: "
            f"{settings['chance']}%\n"
            f"Cooldown: "
            f"{settings['cooldown']} seconds"
        )

    else:

        await ctx.send(
            "Use `!sunshine on`, `!sunshine off`, "
            "or `!sunshine status`"
        )


# =====================================================
# CHANCE COMMAND
# =====================================================

@bot.command()
async def chance(ctx, value: int = None):

    settings = get_settings(
        ctx.channel.id
    )

    if value is None:

        await ctx.send(
            f"🌞 Current reply chance: "
            f"{settings['chance']}%"
        )

        return

    if not 0 <= value <= 100:

        await ctx.send(
            "Choose a chance between 0 and 100."
        )

        return

    settings["chance"] = value

    await ctx.send(
        f"Reply chance set to **{value}%** 🌞"
    )


# =====================================================
# COOLDOWN COMMAND
# =====================================================

@bot.command()
async def cooldown(ctx, value: int = None):

    settings = get_settings(
        ctx.channel.id
    )

    if value is None:

        await ctx.send(
            f"🌞 Current cooldown: "
            f"{settings['cooldown']} seconds"
        )

        return

    if not 0 <= value <= 300:

        await ctx.send(
            "Cooldown must be between 0 and 300 seconds."
        )

        return

    settings["cooldown"] = value

    await ctx.send(
        f"Cooldown set to **{value} seconds** 🌞"
    )


# =====================================================
# MESSAGE LISTENER
# =====================================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    # Always process commands
    await bot.process_commands(message)

    cid = message.channel.id

    if cid not in enabled_channels:
        return

    # Initialize memory
    if cid not in channel_context:

        channel_context[cid] = deque(
            maxlen=CONTEXT_LIMIT
        )

    channel_context[cid].append(
        f"{message.author.display_name}: "
        f"{message.content}"
    )

    logging.info(
        f"Message received in channel {cid}"
    )

    await maybe_reply(message, cid)


# =====================================================
# DECISION ENGINE
# =====================================================

async def maybe_reply(message, cid):

    settings = get_settings(cid)

    now = time.time()

    # Cooldown
    if (
        now - cooldowns.get(cid, 0)
        < settings["cooldown"]
    ):

        logging.info("Cooldown active")

        return

    text = message.content.lower()

    # Ignore commands
    if text.startswith("!"):
        return

    # Always reply when mentioned
    mentioned = (
        bot.user is not None
        and bot.user.mentioned_in(message)
    )

    # Always reply when called by name
    called = (
        "sunshine" in text
        or "sunsine" in text
    )

    if mentioned or called:

        should_reply = True

    else:

        should_reply = (
            random.random()
            < settings["chance"] / 100
        )

    if not should_reply:

        logging.info(
            "Sunshine decided not to reply"
        )

        return

    cooldowns[cid] = now

    await reply_with_context(
        message,
        cid
    )


# =====================================================
# AI REPLY
# =====================================================

async def reply_with_context(message, cid):

    history = "\n".join(
        channel_context[cid]
    )

    prompt = f"""
You are Sunshine, a sweet and playful Discord
friend in a group chat.

PERSONALITY:
- Warm, cute, playful and natural.
- Occasionally flirty in a light, non-explicit way.
- You can use words like cutie, sweetheart,
  darling, pretty, handsome, or baby naturally.
- Use emojis sometimes, not every message.
- Tease gently when the situation fits.
- Never be creepy, overly sexual, or explicit.
- Never pretend to be human.
- Never repeat the entire conversation.
- Reply in under 20 words unless more detail
  is genuinely needed.

CONVERSATION:
{history}

TASK:
Read the conversation and write one natural reply.
Only write the reply. Do not explain your reasoning.
"""

    reply = None

    try:

        logging.info(
            "Sunshine is thinking..."
        )

        # Show typing while waiting for AI
        async with message.channel.typing():

            loop = asyncio.get_running_loop()

            reply = await loop.run_in_executor(
                None,
                get_smart_reply,
                prompt
            )

        if not reply:

            raise RuntimeError(
                "Empty AI response"
            )

        logging.info(
            f"AI reply: {reply}"
        )

    except Exception as e:

        logging.exception(
            f"AI error: {e}"
        )

        reply = random.choice(
            FALLBACK
        )

    # Send reply
    try:

        await message.channel.send(
            reply
        )

        logging.info(
            "Sunshine reply sent"
        )

    except Exception as e:

        logging.exception(
            f"Discord send error: {e}"
        )


# =====================================================
# START WEB + BOT
# =====================================================

threading.Thread(
    target=run_web,
    daemon=True
).start()

bot.run(TOKEN)
