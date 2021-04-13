import logging
from datetime import datetime

import discord
from discord.ext import commands

from ..controllers.member import MemberController
from ..utils import database as db


class Events(commands.Cog):
    WELCOME_CHANNEL = "📢annonces"

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """
        When client is connected
        """
        print(f"\n{' READY ':>^80}\n")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        When a member join a guild, insert it in database or restore all its data
        """
        if mod_member := MemberController(member):
            await member.add_roles(
                mod_member.sub_roles | {mod_member.top_role},  # union
                reason="The user was already register, re-attribute the main role",
            )
        else:
            sql = "INSERT INTO members (member_id, name) VALUES (%s, %s)"
            db.execute(sql, (member.id, member.name))
            mod_member = MemberController(member)
            default_role = mod_member.get_role_by_name("Non Vérifié")
            await member.add_roles(default_role, reason="User was not verified")

        text = f"{member.mention} a rejoint le serveur {member.guild.name}!"
        embed = discord.Embed(
            title="Arrivée d'un membre!",
            colour=0xFF22FF,
            description=text,
            timestamp=datetime.now(),
        )
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_author(name=member.name, url=member.avatar_url)
        embed.set_footer(text=f"{self.bot.user.name}")

        publish_channel = discord.utils.get(
            member.guild.channels, name=self.WELCOME_CHANNEL
        )
        await publish_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, ctx):
        """
        Log message in database for users
        """
        channel = (
            "DMChannel"
            if isinstance(ctx.channel, discord.DMChannel)
            else ctx.channel.name
        )
        if ctx.author.id != self.bot.user.id:
            sql = (
                "INSERT INTO messages (member_id, channel, content)"
                "VALUES (%s, %s, %s)"
            )
            db.execute(sql, (ctx.author.id, channel, ctx.content))

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """
        Check if a member has updated roles and modifies them in the database
        """
        if before.roles == after.roles:
            return

        if mod_member := MemberController(after):
            mod_member.sub_roles.clear()
            for role in after.roles:
                if role.name in ("Prof", "Non Vérifié", "Élève G1", "Élève G2"):
                    mod_member.update_db(top_role=role.name)
                elif role.name.startswith("Groupe"):
                    mod_member.update_db(class_group=int(role.name[-1]))
                elif role.name != "@everyone":
                    mod_member.sub_roles.add(role)

            sub_roles_name = map(lambda r: r.name, mod_member.sub_roles)
            mod_member.update_db(sub_roles=", ".join(sub_roles_name))
        else:
            logging.error(f"The user {after.name} was not found in members table")


def setup(bot):
    bot.add_cog(Events(bot))
