import logging
import os

import discord
from discord.ext import commands

from bot.utils import database, resolver

# Create a logger for this file, __name__ will take the package name if this file
# will does not run as a script
logger = logging.getLogger(__name__)
TOKEN = os.getenv("DISCORD_TOKEN")


def main() -> None:
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix="!", intents=intents)

    database.test_connection()
    # loads all available cogs
    for cog in resolver.COGS:
        bot.load_extension(cog.__name__)

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
