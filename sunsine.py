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
app = Flask('')

@app.route('/')
def home():
    return "Sunsine Bot is shining ☀️💛"

def run():
    app.run(host='0.0.0.0', port=8080)

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

    # ON/OFF Commands using "! sunsine on" and "! sunsine off"
    if content == "! sunsine on":
        bot_enabled[channel_id] = True
        await message.channel.send("Sunsine is glowing 🌞✨")

    elif content == "! sunsine off":
        bot_enabled[channel_id] = False
        await message.channel.send("Going quiet 🌙💤")

    # Respond only if bot is ON
    elif bot_enabled.get(channel_id, False):
        if bot.user.mention in content or "sunsine" in content:
            await send_sweet_reply(message, content)
        elif random.random() < 0.05:
            await send_sweet_reply(message, content, auto=True)

async def send_sweet_reply(message, content, auto=False):
    try:
        prompt = f"Reply very short, sweet, flirty, and include emoji: {content}"
        reply = get_smart_reply(prompt, style="cute", mood="flirty")
        if reply:
            reply = reply.strip()
            if len(reply.split()) > 10:
                reply = "💖 You're so cute! 😘"
            await message.channel.send(reply)
    except Exception as e:
        logging.error(f"AI Error: {e}")
