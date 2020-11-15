import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from database import test_connection

load_dotenv()
test_connection()

TOKEN = os.getenv("DISCORD_TOKEN")
APP_NAME = os.getenv("APP_NAME")
OWNER_ID = int(os.getenv("OWNER_ID"))

logging.basicConfig(
    filename="logs/PyBoss.log",
    format="%(levelname)s: %(asctime)s -> %(message)s",
    level=logging.INFO,
)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, owner_id=OWNER_ID)


if __name__ == "__main__":
    # you can deactivate a specific cog
    bot.load_extension("cogs.events")
    bot.load_extension("cogs.commands")
    bot.load_extension("cogs.roles")
    bot.load_extension("cogs.suggestions")
    bot.load_extension("cogs.planningAndAgenda")
    bot.load_extension("cogs.quiz")
    bot.load_extension("cogs.music")

    bot.run(TOKEN)
