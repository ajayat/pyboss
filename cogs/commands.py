import discord
from discord.ext import commands

from models.modMember import get_mod_member


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    @commands.command(aliases=["mi"])
    @commands.guild_only()
    async def member_info(self, ctx, mention=None):
        """
        Consulter les infos d'un membre
        """
        member = ctx.guild.get_member(int(mention[3:-1])) if mention else ctx.author
        mod_member = get_mod_member(self.bot, member)
        embed = discord.Embed(title="User profile", colour=0xFFA325)
        embed.set_author(name=member.name)
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="Name", value=member.mention, inline=True)
        embed.add_field(name="Level", value=mod_member.level, inline=True)
        embed.add_field(name="XP", value=mod_member.XP, inline=True)
        embed.add_field(
            name="Membre depuis...",
            value=f"{mod_member.joined_at:%d/%m/%Y}",
            inline=True,
        )
        await ctx.send(embed=embed)

    # TODO: add embed_send command


def setup(bot):
    bot.add_cog(Commands(bot))
