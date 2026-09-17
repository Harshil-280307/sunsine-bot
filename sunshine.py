
import os
import time
import random
import asyncio
import logging
import sqlite3
import threading

from collections import deque
from contextlib import closing

from dotenv import load_dotenv

import discord
from discord.ext import commands

from openrouter import (
    get_smart_reply,
    should_reply
)

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
    format=(
        "[%(asctime)s] "
        "[%(levelname)s] "
        "%(message)s"
    )
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
# DATABASE
# =====================================================

DB_PATH = "sunshine.db"


def db():

    return sqlite3.connect(
        DB_PATH,
        timeout=10
    )


def init_db():

    with closing(db()) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS
            channel_settings (
                channel_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                chance INTEGER DEFAULT 30,
                cooldown INTEGER DEFAULT 8
            )
        """)

        conn.commit()


def get_settings(channel_id):

    with closing(db()) as conn:

        row = conn.execute(
            """
            SELECT enabled, chance, cooldown
            FROM channel_settings
            WHERE channel_id = ?
            """,
            (channel_id,)
        ).fetchone()

        if row is None:

            conn.execute(
                """
                INSERT INTO channel_settings
                (channel_id, enabled, chance, cooldown)
                VALUES (?, 0, 30, 8)
                """,
                (channel_id,)
            )

            conn.commit()

            return {
                "enabled": False,
                "chance": 30,
                "cooldown": 8
            }

        return {
            "enabled": bool(row[0]),
            "chance": row[1],
            "cooldown": row[2]
        }


def update_settings(
    channel_id,
    enabled=None,
    chance=None,
    cooldown=None
):

    current = get_settings(channel_id)

    if enabled is not None:
        current["enabled"] = enabled

    if chance is not None:
        current["chance"] = chance

    if cooldown is not None:
        current["cooldown"] = cooldown

    with closing(db()) as conn:

        conn.execute(
            """
            UPDATE channel_settings
            SET enabled = ?,
                chance = ?,
                cooldown = ?
            WHERE channel_id = ?
            """,
            (
                int(current["enabled"]),
                current["chance"],
                current["cooldown"],
                channel_id
            )
        )

        conn.commit()


# =====================================================
# MEMORY
# =====================================================

CONTEXT_LIMIT = 12

channel_context = {}

cooldowns = {}

active_replies = set()


# =====================================================
# FALLBACK
# =====================================================

DEFAULT_FALLBACK = [

    "Heyyy sunshine 🌞",
    "I'm listening, cutie ✨",
    "Ooo tell me more 😏",
    "Hehe, you're funny 💛",
    "What's happening, sweetheart? ☀️",
    "Don't leave me hanging now 😌",
    "Aww, tell me more 💛",
    "You're making me smile 🌞"

]


def load_fallback():

    try:

        with open(
            "fallback_sweet_replies.txt",
            encoding="utf-8"
        ) as f:

            replies = [
                line.strip()
                for line in f
                if line.strip()
            ]

            if replies:
                return replies

    except Exception as e:

        logging.warning(
            f"Fallback file error: {e}"
        )

    return DEFAULT_FALLBACK.copy()


FALLBACK = load_fallback()


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

    cid = ctx.channel.id

    if mode is None:

        await ctx.send(
            "Use `!sunshine on`, "
            "`!sunshine off`, "
            "or `!sunshine status`"
        )

        return

    mode = mode.lower()

    settings = get_settings(cid)

    if mode == "on":

        update_settings(
            cid,
            enabled=True
        )

        await ctx.send(
            "Sunshine is glowing 🌞✨"
        )

    elif mode == "off":

        update_settings(
            cid,
            enabled=False
        )

        await ctx.send(
            "Going quiet... but I'll be here 🌙"
        )

    elif mode == "status":

        await ctx.send(
            f"🌞 **Sunshine status**\n"
            f"Enabled: {settings['enabled']}\n"
            f"Reply chance: {settings['chance']}%\n"
            f"Cooldown: {settings['cooldown']} seconds"
        )

    else:

        await ctx.send(
            "Use `!sunshine on`, "
            "`!sunshine off`, "
            "or `!sunshine status`"
        )


# =====================================================
# CHANCE COMMAND
# =====================================================

@bot.command()
async def chance(ctx, value: int = None):

    cid = ctx.channel.id

    settings = get_settings(cid)

    if value is None:

        await ctx.send(
            f"🌞 Current reply chance: "
            f"{settings['chance']}%"
        )

        return

    if not 0 <= value <= 100:

        await ctx.send(
            "Choose a number between 0 and 100."
        )

        return

    update_settings(
        cid,
        chance=value
    )

    await ctx.send(
        f"Reply chance set to **{value}%** 🌞"
    )


# =====================================================
# COOLDOWN COMMAND
# =====================================================

@bot.command()
async def cooldown(ctx, value: int = None):

    cid = ctx.channel.id

    settings = get_settings(cid)

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

    update_settings(
        cid,
        cooldown=value
    )

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

    await bot.process_commands(message)

    cid = message.channel.id

    settings = get_settings(cid)

    if not settings["enabled"]:
        return

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

    if (
        now - cooldowns.get(cid, 0)
        < settings["cooldown"]
    ):

        logging.info(
            "Cooldown active"
        )

        return

    text = message.content.lower()

    if text.startswith("!"):
        return

    if cid in active_replies:
        return

    mentioned = (
        bot.user is not None
        and bot.user.mentioned_in(message)
    )

    called = (
        "sunshine" in text
        or "sunsine" in text
    )

    # Direct calls always get a response attempt
    if mentioned or called:

        reply_allowed = True

    else:

        # Chance gate
        if random.random() > (
            settings["chance"] / 100
        ):

            logging.info(
                "Sunshine skipped by chance"
            )

            return

        # AI decides whether this is worth replying to
        history = "\n".join(
            channel_context[cid]
        )

        try:

            logging.info(
                "Sunshine is deciding..."
            )

            loop = asyncio.get_running_loop()

            reply_allowed = await loop.run_in_executor(
                None,
                should_reply,
                history
            )

        except Exception as e:

            logging.exception(
                f"Decision AI error: {e}"
            )

            # Safe fallback: skip instead of spamming
            reply_allowed = False

    if not reply_allowed:

        logging.info(
            "Sunshine decided not to reply"
        )

        return

    cooldowns[cid] = now

    active_replies.add(cid)

    try:

        await reply_with_context(
            message,
            cid
        )

    finally:

        active_replies.discard(cid)


# =====================================================
# AI REPLY
# =====================================================

async def reply_with_context(message, cid):

    history = "\n".join(
        channel_context[cid]
    )

    prompt = f"""
You are Sunshine, a sweet, playful Discord
friend in a group chat.

PERSONALITY:
- Warm, cute, playful and natural.
- Occasionally flirty in a light romantic way.
- Gentle teasing when it fits.
- Use words like cutie, sweetheart,
  darling or handsome naturally.
- Emojis sometimes.
- Never graphic or explicit.
- Do not be creepy or overly sexual.
- Do not sound like a bot.
- Reply in under 20 words unless needed.

CONVERSATION:
{history}

TASK:
Write one natural reply to the latest message.
Only write the reply.
Do not explain your reasoning.
"""

    reply = None

    try:

        logging.info(
            "Sunshine is thinking..."
        )

        async with message.channel.typing():

            loop = asyncio.get_running_loop()

            reply = await loop.run_in_executor(
                None,
                get_smart_reply,
                prompt
            )

        if not reply:

            raise RuntimeError(
                "AI returned empty reply"
            )

    except Exception as e:

        logging.exception(
            f"AI error: {e}"
        )

        reply = random.choice(
            FALLBACK
        )

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
# START
# =====================================================

init_db()

threading.Thread(
    target=run_web,
    daemon=True
).start()

bot.run(TOKEN)
