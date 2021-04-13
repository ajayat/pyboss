import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

if __package__:
    from pyboss.utils import database
else:
    from utils import database
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

logging.basicConfig(
    filename="logs/PyBoss.log",
    format="%(levelname)s: %(asctime)s -> %(message)s",
    level=logging.INFO,
)


def main():
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix="!", intents=intents)

    # loads cogs that need database
    if database.test_connection():
        for name in os.listdir("cogs"):
            bot.load_extension(f"cogs.{name}")

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
