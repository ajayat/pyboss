import os
from datetime import datetime

import discord
from discord.ext import commands

import database

OWNER_ID = int(os.getenv("OWNER_ID"))


def suggestion_channel(ctx):
    if not isinstance(ctx.channel, discord.DMChannel):
        return "suggestion" in ctx.channel.name


class Suggestion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="suggestions_rules", hidden=True)
    @commands.is_owner()
    @commands.check(suggestion_channel)
    async def send_suggestions_rules(self, ctx):
        """
        send the rules for suggestion channel
        """
        await ctx.message.delete()
        with open("static/txt/suggestions_rules.txt", encoding="utf-8") as f:
            content = f.read()
        embed = discord.Embed(
            title="Fonctionnement des suggestions", description=content, colour=0xff66ff
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_footer(
            text=f"Generated by {self.bot.user.name} | {datetime.now():%D - %H:%M}"
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener("on_message")
    async def make_suggestion(self, message):
        if suggestion_channel(message):
            await message.add_reaction("✅")
            await message.add_reaction("❌")

    @commands.Cog.listener("on_raw_reaction_add")
    async def decisive_reaction(self, payload):
        """
        Calling when the owner add a reaction
        """
        channel = self.bot.get_channel(payload.channel_id)
        if payload.user_id != OWNER_ID or "suggestion" not in channel.name:
            return

        message = await channel.fetch_message(payload.message_id)
        if str(payload.emoji) == "✅":
            sql = (
                f"""INSERT INTO suggestions (author, description) """
                f"""VALUES ("{message.author.name}", "{message.content}")"""
            )
            database.execute(sql)

        for reaction in message.reactions:
            if str(reaction.emoji) == "✅":
                async for user in reaction.users():
                    await self.send_dm_suggestion_state(
                        user, str(payload.emoji), message
                    )
        await self.send_dm_suggestion_state(message.author, str(payload.emoji), message)

        await message.delete()

    async def send_dm_suggestion_state(self, user, decisive_emoji, suggestion):
        """
        Send a message to a member who has voted to inform of the state of the reaction
        """
        if user.id != self.bot.user.id and decisive_emoji in ("✅", "❌"):
            citation = "\n> ".join(suggestion.content.split("\n"))

            if decisive_emoji == "✅":
                embed = discord.Embed(
                    colour=0xff22bb,
                    title="Suggestion acceptée!",
                    description=f"**Félicitations!** La suggestion de **{suggestion.author.name}** "
                    f"pour laquelle vous avez voté a été acceptée:\n\n > {citation} \n\n"
                    "__Note__: \
                    Il faut parfois attendre plusieurs jours avant qu'elle soit effective",
                )
            else:
                embed = discord.Embed(
                    colour=0xff22bb,
                    title="Suggestion refusée!",
                    description=f"**Mauvaise nouvelle...** "
                    f"la suggestion de **{suggestion.author.name}** pour laquelle vous avez voté "
                    f"a été malheureusement refusée:\n\n {citation} \n",
                )

            embed.set_thumbnail(
                url="https://kognos.pro/wp-content/uploads/2019/08/icon-2382008_960_720.png"
            )
            embed.set_footer(
                text=f"{self.bot.user.name} | This message was sent automatically"
            )

            await user.send(embed=embed)


def setup(bot):
    bot.add_cog(Suggestion(bot))