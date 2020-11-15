from itertools import cycle

import discord
from discord.ext import commands, tasks

import database


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status = cycle(
            [
                discord.Streaming(
                    name="MOOC Python3",
                    url="https://www.youtube.com/watch?v=-HF7yRthTsg&feature=youtu.be",
                ),
                discord.Game(name=f"{bot.command_prefix}help"),
            ]
        )

    @tasks.loop(seconds=5)
    async def change_status(self):
        """
        Change status every 5 seconds
        """
        await self.bot.change_presence(activity=next(self.status))

    @commands.Cog.listener()
    async def on_ready(self):
        """
        When client is connected
        """
        self.change_status.start()
        print(f"\n{' READY ':>^80}\n")

    @commands.Cog.listener()
    async def on_message(self, ctx):
        """
        Log message in db for users
        """
        channel = (
            "DMChannel"
            if isinstance(ctx.channel, discord.DMChannel)
            else ctx.channel.name
        )
        if ctx.author.id != self.bot.user.id:
            sql = f"INSERT INTO messages (member_id, channel, content) \
                    VALUES ({ctx.author.id}, {repr(channel)}, {repr(ctx.content)})"
            database.execute(sql)


def setup(bot):
    bot.add_cog(Commands(bot))
