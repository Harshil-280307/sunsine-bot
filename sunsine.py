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
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- STATE ----------
bot_enabled_channels = set()
cooldowns = {}
COOLDOWN_SECONDS = 8

CHANNEL_CONTEXT_LIMIT = 8
channel_context = {}

# ---------- FALLBACK ----------
try:
    with open("fallback_sweet_replies.txt", encoding="utf-8") as f:
        FALLBACK = [l.strip() for l in f if l.strip()]
except:
    FALLBACK = ["Hey ☀️"]

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    logging.info(f"🌞 Sunsine online as {bot.user}")

# ---------- COMMAND ----------
@bot.command()
async def sunsine(ctx, mode: str):
    mode = mode.lower()
    if mode == "on":
        bot_enabled_channels.add(ctx.channel.id)
        await ctx.send("Sunsine is glowing 🌞✨")
    elif mode == "off":
        bot_enabled_channels.discard(ctx.channel.id)
        await ctx.send("Going quiet 🌙💤")
    else:
        await ctx.send("Use `!sunsine on` or `!sunsine off`")

# ---------- MESSAGE LISTENER ----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    cid = message.channel.id
    if cid not in bot_enabled_channels:
        return

    # init memory
    if cid not in channel_context:
        channel_context[cid] = deque(maxlen=CHANNEL_CONTEXT_LIMIT)

    channel_context[cid].append(
        f"{message.author.display_name}: {message.content}"
    )

    await maybe_reply(message, cid)

# ---------- DECISION ----------
async def maybe_reply(message, cid):
    now = time.time()
    if now - cooldowns.get(cid, 0) < COOLDOWN_SECONDS:
        return

    text = message.content.lower()

    # ignore short junk
    if len(text.split()) < 3:
        return

    # chance logic
    if bot.user.mentioned_in(message) or "sunsine" in text:
        chance = 1.0
    else:
        chance = 0.2  # natural participation

    if random.random() > chance:
        return

    cooldowns[cid] = now
    await reply_with_context(message, cid)

# ---------- AI REPLY ----------
async def reply_with_context(message, cid):
    history = "\n".join(channel_context[cid])

    prompt = (
        "You are chatting in a Discord group.\n"
        "Reply naturally as part of the conversation.\n"
        "Do not repeat others.\n\n"
        f"Conversation:\n{history}\n\n"
        "Your reply:"
    )

    try:
        loop = asyncio.get_running_loop()
        reply = await loop.run_in_executor(None, get_smart_reply, prompt)
        if not reply:
            reply = random.choice(FALLBACK)
    except Exception as e:
        logging.error(f"AI error: {e}")
        reply = random.choice(FALLBACK)

    await message.channel.send(reply)

# ---------- START WEB + BOT ----------
threading.Thread(target=run_web, daemon=True).start()
bot.run(TOKEN)
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
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- STATE ----------
bot_enabled_channels = set()
cooldowns = {}
COOLDOWN_SECONDS = 8

CHANNEL_CONTEXT_LIMIT = 8
channel_context = {}

# ---------- FALLBACK ----------
try:
    with open("fallback_sweet_replies.txt", encoding="utf-8") as f:
        FALLBACK = [l.strip() for l in f if l.strip()]
except:
    FALLBACK = ["Hey ☀️"]

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    logging.info(f"🌞 Sunsine online as {bot.user}")

# ---------- COMMAND ----------
@bot.command()
async def sunsine(ctx, mode: str):
    mode = mode.lower()
    if mode == "on":
        bot_enabled_channels.add(ctx.channel.id)
        await ctx.send("Sunsine is glowing 🌞✨")
    elif mode == "off":
        bot_enabled_channels.discard(ctx.channel.id)
        await ctx.send("Going quiet 🌙💤")
    else:
        await ctx.send("Use `!sunsine on` or `!sunsine off`")

# ---------- MESSAGE LISTENER ----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    cid = message.channel.id
    if cid not in bot_enabled_channels:
        return

    # init memory
    if cid not in channel_context:
        channel_context[cid] = deque(maxlen=CHANNEL_CONTEXT_LIMIT)

    channel_context[cid].append(
        f"{message.author.display_name}: {message.content}"
    )

    await maybe_reply(message, cid)

# ---------- DECISION ----------
async def maybe_reply(message, cid):
    now = time.time()
    if now - cooldowns.get(cid, 0) < COOLDOWN_SECONDS:
        return

    text = message.content.lower()

    # ignore short junk
    if len(text.split()) < 3:
        return

    # chance logic
    if bot.user.mentioned_in(message) or "sunsine" in text:
        chance = 1.0
    else:
        chance = 0.5  # natural participation

    if random.random() > chance:
        return

    cooldowns[cid] = now
    await reply_with_context(message, cid)

# ---------- AI REPLY ----------
async def reply_with_context(message, cid):
    history = "\n".join(channel_context[cid])

    prompt = (
        "You are chatting in a Discord group.\n"
        "Reply naturally as part of the conversation.\n"
        "Do not repeat others.\n\n"
        f"Conversation:\n{history}\n\n"
        "Your reply:"
    )

    try:
        loop = asyncio.get_running_loop()
        reply = await loop.run_in_executor(None, get_smart_reply, prompt)
        if not reply:
            reply = random.choice(FALLBACK)
    except Exception as e:
        logging.error(f"AI error: {e}")
        reply = random.choice(FALLBACK)

    await message.channel.send(reply)

# ---------- START WEB + BOT ----------
threading.Thread(target=run_web, daemon=True).start()
bot.run(TOKEN)
