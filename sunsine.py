import discord
import asyncio
from flask import Flask
from threading import Thread
from openrouter import get_smart_reply
import logging
import os
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

# Flask server to keep bot alive
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

# Load fallback replies from file
fallback_replies = []
try:
    with open("fallback_sweet_replies.txt", "r", encoding="utf-8") as f:
        fallback_replies = [line.strip() for line in f.readlines() if line.strip()]
except Exception as e:
    logging.error(f"Failed to load fallback replies: {e}")
    fallback_replies = ["You're adorable 💖"]  # Fallback for fallback 😅

# Discord setup
intents = discord.Intents.default()
intents.message_content = True  # Needed for reading messages
bot = discord.Client(intents=intents)

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot_enabled = {}  # Channel-wise on/off toggle

@bot.event
async def on_ready():
    logging.info(f"🌞 Sunsine is online as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.strip().lower()
    channel_id = str(message.channel.id)

    # Toggle Commands
    if content == "!sunsine on":
        bot_enabled[channel_id] = True
        await message.channel.send("Sunsine is glowing 🌞✨")
        return

    elif content == "!sunsine off":
        bot_enabled[channel_id] = False
        await message.channel.send("Going quiet 🌙💤")
        return

    # Respond if bot is enabled in the channel
    if bot_enabled.get(channel_id, False):
        # If tagged or name mentioned
        if bot.user.mention in message.content or "sunsine" in content:
            await send_sweet_reply(message, content)
        # 5% chance to auto reply
        elif random.random() < 0.05:
            await send_sweet_reply(message, content, auto=True)

async def send_sweet_reply(message, content, auto=False):
    try:
        prompt = f"Reply very short, sweet, flirty, and include emoji: {content}"
        reply = get_smart_reply(prompt)

        logging.info(f"[Prompt] {prompt}")
        logging.info(f"[OpenRouter Reply] {reply}")

        # If OpenRouter fails or returns nothing
        if not reply or not isinstance(reply, str):
            reply = random.choice(fallback_replies)

        # Optional shortener
        if len(reply.split()) > 12:
            reply = "You're just too sweet 🥺💘"

        await message.channel.send(reply.strip())

    except Exception as e:
        logging.error(f"AI Error: {e}")
        await message.channel.send(random.choice(fallback_replies))

# --- Launch everything ---
keep_alive()
bot.run(TOKEN)
