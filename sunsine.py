import os
import time
import random
import asyncio
import logging
from dotenv import load_dotenv

import discord
from discord.ext import commands

from openrouter import get_smart_reply

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s"
)

# ---------- Discord Setup ----------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- State ----------
bot_enabled_channels = set()
cooldowns = {}  # channel_id -> last_time
COOLDOWN_SECONDS = 6

# ---------- Load fallback replies ----------
try:
    with open("fallback_sweet_replies.txt", "r", encoding="utf-8") as f:
        FALLBACK_REPLIES = [l.strip() for l in f if l.strip()]
except:
    FALLBACK_REPLIES = ["Hey cutie 💛"]

# ---------- Events ----------
@bot.event
async def on_ready():
    logging.info(f"🌞 Sunsine online as {bot.user}")

# ---------- Commands ----------
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

# ---------- Message Listener ----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if message.channel.id not in bot_enabled_channels:
        return

    content = message.content.lower()

    if bot.user.mentioned_in(message) or "sunsine" in content:
        await handle_ai_reply(message)

# ---------- AI Reply ----------
async def handle_ai_reply(message):
    now = time.time()
    last = cooldowns.get(message.channel.id, 0)

    if now - last < COOLDOWN_SECONDS:
        return

    cooldowns[message.channel.id] = now

    prompt = f"Reply sweetly to: {message.content}"

    try:
        loop = asyncio.get_running_loop()
        reply = await loop.run_in_executor(
            None, get_smart_reply, prompt
        )

        if not reply:
            reply = random.choice(FALLBACK_REPLIES)

    except Exception as e:
        logging.error(f"AI error: {e}")
        reply = random.choice(FALLBACK_REPLIES)

    await message.channel.send(reply)

# ---------- Run ----------
if not TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN missing")

bot.run(TOKEN)
