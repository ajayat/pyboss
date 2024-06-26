from datetime import datetime

import discord
from discord.ext.commands import Cog, check, command, is_owner
from sqlalchemy import insert

from pyboss import STATIC_DIR
from pyboss.models import SuggestionModel
from pyboss.utils import database

from .utils.checkers import is_suggestion_channel


class Suggestion(Cog):
    """Offers commands to allow members to propose suggestions and interact with them"""

    def __init__(self, bot):
        self.bot = bot

    @command(name="suggestions_rules", hidden=True)
    @is_owner()
    @check(is_suggestion_channel)
    async def send_suggestions_rules(self, ctx):
        """Send the rules for suggestion channel"""
        await ctx.message.delete()
        with open(STATIC_DIR / "text/suggestions_rules.md", encoding="utf-8") as f:
            content = f.read()
        embed = discord.Embed(
            title="Fonctionnement des suggestions", description=content, colour=0xFF66FF
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_footer(
            text=f"Generated by {self.bot.user.name} | {datetime.now():%D - %H:%M}"
        )
        await ctx.send(embed=embed)

    @Cog.listener("on_message")
    async def make_suggestion(self, message):
        if is_suggestion_channel(message):
            try:
                await message.add_reaction("✅")
                await message.add_reaction("❌")
            except discord.errors.NotFound:
                pass

    @Cog.listener("on_raw_reaction_add")
    async def decisive_reaction(self, payload):
        """Send result to all users when the owner add a reaction"""
        channel = self.bot.get_channel(payload.channel_id)
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.errors.NotFound:
            return
        if (
            str(payload.emoji) not in ("✅", "❌")
            or not is_suggestion_channel(message)
            or not await self.bot.is_owner(payload.member)
        ):
            return

        if accepted := str(payload.emoji) == "✅":
            stmt = insert(SuggestionModel).values(
                author=message.author.name, description=message.content
            )
            database.execute(stmt)
        for reaction in message.reactions:
            if str(reaction.emoji) not in ("✅", "❌"):
                continue
            async for user in reaction.users():
                if user.id != self.bot.user.id:
                    await self.send_dm_suggestion_state(user, accepted, message)
        await message.delete()

    async def send_dm_suggestion_state(self, user, accepted: bool, suggestion):
        """
        Send a message to a member who has voted to inform of the state of the reaction
        """
        citation = "\n> ".join(suggestion.content.split("\n"))

        if accepted:
            embed = discord.Embed(
                colour=0xFF22BB,
                title="Suggestion acceptée!",
                description=f"**Félicitations!** La suggestion de **{suggestion.author.name}** "
                f"pour laquelle vous avez voté a été acceptée:\n> {citation} \n\n"
                "__Note__: \n Il faut parfois attendre plusieurs jours "
                "avant qu'elle soit effective",
            )
        else:
            embed = discord.Embed(
                colour=0xFF22BB,
                title="Suggestion refusée!",
                description=f"**Mauvaise nouvelle...** la suggestion de "
                f"**{suggestion.author.name}** pour laquelle vous avez voté "
                f"a été malheureusement refusée:\n> {citation}\n\n",
            )
        file = discord.File(STATIC_DIR / "img/alert.png")
        embed.set_thumbnail(url="attachment://alert.png")
        embed.set_footer(
            text=f"{self.bot.user.name} | Ce message a été envoyé automatiquement"
        )
        await user.send(file=file, embed=embed)


def setup(bot):
    bot.add_cog(Suggestion(bot))
