import json

import discord
from discord.ext import commands

from pyboss import STATIC_DIR

with open(STATIC_DIR / "json/channels_tables.json") as f:
    CHANNELS_TABLES = json.load(f)


def is_guild_owner():
    def predicate(ctx: commands.Context) -> bool:
        return ctx.guild and ctx.guild.owner_id == ctx.author.id

    return commands.check(predicate)


def is_schedule_channel():
    def predicate(ctx: commands.Context) -> bool:
        if not isinstance(ctx, discord.DMChannel):
            return str(ctx.channel.id) in CHANNELS_TABLES
        return False

    return commands.check(predicate)
