import logging

import discord
from discord.ext import commands

from pyboss import CONFIG

logger = logging.getLogger(__name__)


def is_guild_owner():
    def predicate(ctx: commands.Context) -> bool:
        return ctx.guild and ctx.guild.owner_id == ctx.author.id

    return commands.check(predicate)


def is_schedule_channel(schedule: str):
    def predicate(ctx: commands.Context) -> bool:
        return ctx.channel.id in CONFIG["guild"]["channels"][schedule]

    return commands.check(predicate)


def is_quiz_channel():
    def predicate(ctx: commands.Context) -> bool:
        if not isinstance(ctx.channel, discord.DMChannel):
            return "quiz" in ctx.channel.name or "test" in ctx.channel.name
        return False

    return commands.check(predicate)


def is_suggestion_channel():
    def predicate(ctx: commands.Context) -> bool:
        if not isinstance(ctx.channel, discord.DMChannel):
            return "suggestion" in ctx.channel.name
        return False

    return commands.check(predicate)
