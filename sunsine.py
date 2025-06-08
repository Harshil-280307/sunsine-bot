import discord
import asyncio
from flask import Flask
from threading import Thread
from openrouter import get_smart_reply
import logging
import os
from dotenv import load_dotenv
import random

load_dotenv()

# Flask app to keep bot alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Sunsine Bot is shining ☀️💛"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# Logging setup
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

# Discord setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = discord.Client(intents=intents)
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Per-channel ON/OFF toggle
bot_enabled = {}

@bot.event
async def on_ready():
    logging.info(f"🌞 Sunsine is online as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.strip().lower()
    channel_id = str(message.channel.id)

    # ON/OFF Commands
    if content == "!sunsine on":
        bot_enabled[channel_id] = True
        await message.channel.send("Sunsine is glowing 🌞✨")

    elif content == "!sunsine off":
        bot_enabled[channel_id] = False
        await message.channel.send("Going quiet 🌙💤")

    elif bot_enabled.get(channel_id, False):
        if bot.user.mention in message.content or "sunsine" in message.content.lower():
            await send_sweet_reply(message, content)
        elif random.random() < 0.05:  # Random 5% chance to auto-reply
            await send_sweet_reply(message, content, auto=True)

async def send_sweet_reply(message, content, auto=False):
    try:
        prompt = f"Reply very short, sweet, flirty, and include emoji: {content}"
        reply = get_smart_reply(prompt, style="cute", mood="flirty")

        # If OpenRouter gives empty or broken reply, use fallback
        if not reply or not isinstance(reply, str):
            reply = "Awww you're adorable 💖"

        reply = reply.strip()

        # Optional: Limit overly long AI replies
        if len(reply.split()) > 12:
            reply = "You're just too sweet 🥺💘"

        await message.channel.send(reply)

    except Exception as e:
        logging.error(f"AI Error: {e}")
        await message.channel.send("Oops... got shy! 😳")

# --- Start Flask and Bot ---
keep_alive()
bot.run(TOKEN)
