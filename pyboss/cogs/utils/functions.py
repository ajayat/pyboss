import datetime
import logging

import discord

logger = logging.getLogger(__name__)


async def send_embed(bot, channel, title, content):
    embed = discord.Embed(
        title=title,
        description=content,
        colour=0xFFA325,
        timestamp=datetime.datetime.now(),
    )
    embed.set_thumbnail(url=channel.guild.icon_url)
    embed.set_footer(text=f"Generated by {bot.user.name}")

    await channel.send(embed=embed)
