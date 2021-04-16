from itertools import cycle

import discord
from discord.ext import commands, tasks

from bot.controllers.guild import GuildController

from .utils import youtube
from .utils.checkers import is_guild_owner


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status = cycle((discord.Game(name=f"{bot.command_prefix}help"),))

    @commands.command(aliases=["status"])
    @commands.guild_only()
    @is_guild_owner()
    async def change_status(self, _, *params):
        """
        Change le status du bot par des vidéos correspondantes à la recherche
        """
        query = " ".join(params)
        videos = []
        for video in youtube.search(query, n=50):
            videos.append(discord.Streaming(**video))

        self.status = cycle(videos)

    @tasks.loop(seconds=30)
    async def loop_status(self):
        await self.bot.change_presence(activity=next(self.status))

    @commands.Cog.listener("on_ready")
    async def before_loop_status(self):
        self.loop_status.start()

    @commands.command()
    @commands.guild_only()
    async def clear(self, ctx, n=1):
        """
        Supprime les n message du salon
        """
        await ctx.channel.purge(limit=int(n) + 1)

    @commands.command()
    @commands.guild_only()
    async def send(self, ctx, *params):
        """
        Envoie un message dans le salon actuel
        """
        await ctx.send(" ".join(params))
        await ctx.message.delete()

    @commands.command()
    @commands.guild_only()
    async def profile(self, ctx, mention=None):
        """
        Consulter les infos d'un membre
        """
        id = mention.strip("<>!?@&") if mention else ctx.author.id
        if not id.isdigit():
            await ctx.send(f"{mention} est incorrect")

        elif member := GuildController(ctx.guild).get_member(int(id)):
            embed = discord.Embed(title="Profil", colour=0xFFA325)
            embed.set_author(name=member.name)
            embed.set_thumbnail(url=member.avatar_url)
            embed.add_field(name="Name", value=member.mention, inline=True)
            embed.add_field(name="Level", value=member.level, inline=True)
            embed.add_field(name="XP", value=member.XP, inline=True)
            embed.add_field(
                name="Membre depuis...",
                value=f"{member.joined_at:%d/%m/%Y}",
                inline=True,
            )
            await ctx.send(embed=embed)

    # TODO: add embed_send command and LaTeX command like Texit bot


def setup(bot):
    bot.add_cog(Commands(bot))
