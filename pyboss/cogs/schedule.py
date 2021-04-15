import asyncio
import datetime
import json

import discord
from discord.ext import commands

from pyboss.utils import database as db

from .utils.checkers import is_guild_owner, is_schedule_channel
from .utils.schedule import check_date, check_description, check_hours, check_matter

# fmt: off
MONTHS = (
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
    "septembre", "octobre", "novembre", "décembre"
)  # fmt: on
DAYS = ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi")


async def update_message_ref(fieldname, message: discord.Message):
    """
    Update id of agenda or planning message in messages_id.json file
    """
    sql = f"SELECT message_id FROM specials WHERE name='{fieldname}'"
    (ex_message_id,) = db.execute(sql, fetchone=True)
    sql = "UPDATE specials SET message_id=? WHERE name=?"
    db.execute(sql, (message.id, fieldname))
    try:
        ex_message = await message.channel.fetch_message(ex_message_id)
    except (discord.NotFound, discord.HTTPException):
        return
    await ex_message.delete()


class Schedule:

    with open("pyboss/static/json/channels_tables.json") as f:
        CHANNELS_TABLES = json.load(f)

    def __init__(self, ctx):
        self.bot = ctx.bot
        self.author = ctx.author
        self.channel = ctx.channel
        self.custom_response = ""
        self.table = self.CHANNELS_TABLES[str(ctx.channel.id)]["table"]
        self.table_class = self.CHANNELS_TABLES[str(ctx.channel.id)]["class"]
        self.answers = {"class": self.table_class}
        self.traces = []

    async def new_procedure(self, ctx):
        await ctx.message.delete()
        try:
            if self.table == "planning":
                await self.gen_question(
                    "Quelle matière voulez-vous ajouter ?", check_matter
                )
                await self.gen_question(
                    "A quelle date le cours aura lieu ? (Ex : JJ/MM)", check_date
                )
                await self.gen_question(
                    "A quelle heure ? (Ex: 10h; 10h/12h…)", check_hours
                )
                await self.gen_question(
                    'Voulez-vous ajouter des infos supplémentaires? ("votre contenu" ou "non")',
                    check_description,
                    timeout=120,
                )
            else:
                await self.gen_question(
                    "Quelle matière voulez-vous ajouter ?", check_matter
                )
                await self.gen_question(
                    "Quelle est la date limite du devoir ? (Ex : JJ/MM)",
                    check_date,
                )
                await self.gen_question(
                    "Indiquez quels sont les devoirs à faire (obligatoire):",
                    check_description,
                    timeout=120,
                )
        except asyncio.TimeoutError:
            await ctx.author.send(
                f"{ctx.author.mention} Vous avez mis trop de temps à répondre"
                f" ou vos réponses n'étaient pas correct. {self.custom_response}"
            )
        else:
            columns = ",".join(self.answers.keys())
            values = ",".join(map(repr, self.answers.values()))
            sql = f"INSERT INTO {self.table} ({columns}) VALUES ({values})"
            db.execute(sql)
            await self.update_data()
        finally:
            for msg in self.traces:
                try:
                    await msg.delete()
                except discord.errors.NotFound:
                    pass

    async def remove_procedure(self, ctx):
        await ctx.message.delete()

        try:
            msg1 = await ctx.channel.send("Quelle matière voulez-vous supprimer?")
            self.traces.append(msg1)
            resp1 = await self.bot.wait_for("message", timeout=60, check=check_matter)
            await msg1.delete()
            await resp1.delete()

            msg2 = await ctx.channel.send("De quel jour? (Ex: JJ/MM)")
            self.traces.append(msg2)
            resp2 = await self.bot.wait_for("message", timeout=120, check=check_date)
            await msg2.delete()
            await resp2.delete()

        except asyncio.TimeoutError:
            await self.author.send(
                f"{self.author.mention} Vous avez mis trop de temps à répondre "
                f"ou vos réponses n'étaient pas correct. {self.custom_response}"
            )
        else:
            sql = f"DELETE FROM {self.table} WHERE matter=%s AND date=%s"
            db.execute(sql, (self.answers["matter"], self.answers["date"]))
            await self.update_data()
        finally:
            for msg in self.traces:
                try:
                    await msg.delete()
                except discord.errors.NotFound:
                    pass

    async def gen_question(self, question, check=None, timeout=60):
        msg_question = await self.channel.send(question)
        self.traces.append(msg_question)
        message = await self.bot.wait_for("message", timeout=timeout, check=check)
        self.traces.append(message)
        await message.delete()
        await msg_question.delete()

    async def update_data(self):
        # fetch the database to get the list of rows ordered by date
        sql = (
            f"SELECT * FROM {self.table} "
            f"WHERE class='{self.table_class}' AND date>=NOW() ORDER BY date"
        )
        result = db.execute(sql, dictionary=True, fetchall=True)

        next_date, message = None, ""
        for row in result:
            date = row["date"]

            if date != next_date:
                next_date = date
                day = DAYS[date.weekday()]
                month = MONTHS[int(f"{date:%m}") - 1]
                message += f"\n__Pour le **{day}** {date:%d} {month}:__\n"

            description = (
                f"*({row['description']})*" if bool(row["description"]) else ""
            )
            if self.table == "planning":
                message += f"- \t {row['matter']}: "
                message += (
                    f"**{row['starthour']}**-**{row['endhour']}** {description}\n"
                )
            else:
                message += f"\n**{row['matter']}**: {row['description']}\n"

        title = "Cours à venir:" if self.table == "planning" else "Devoirs à faire:"
        embed = discord.Embed(color=0x22CCFF, title=title, description=message)
        embed.set_thumbnail(url="static/img/book.jpg")
        new_msg = await self.channel.send(embed=embed)

        await update_message_ref(f"{self.table}_{self.table_class}", new_msg)


class PlanningAndAgenda(commands.Cog):
    """
    A controller class to listen commands related to the agenda or planning
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rules", hidden=True)
    @is_schedule_channel()
    @is_guild_owner()
    async def send_planning_rules(self, ctx):
        """
        Send the rules for planning or agenda channel
        """
        await ctx.message.delete()
        if "agenda" in ctx.channel.name:
            with open("../static/text/agenda_rules.md", encoding="utf-8") as agenda:
                content = agenda.read()
                title = "Fonctionnement de l'agenda"
        else:
            with open("../static/text/planning_rules.md", encoding="utf-8") as planning:
                content = planning.read()
                title = "Fonctionnement du planning"

        embed = discord.Embed(
            title=title,
            description=content,
            colour=0xFFA325,
            timestamp=datetime.datetime.now(),
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_footer(text=f"Generated by {self.bot.user.name}")

        await ctx.send(embed=embed)

    @commands.command(name="new")
    @is_schedule_channel()
    async def new_item(self, ctx):
        """
        Ajoute un cours ou un devoir (procedure)
        """
        model = Schedule(ctx)
        await model.new_procedure(ctx)

    @commands.command(name="del")
    @is_schedule_channel()
    async def remove_item(self, ctx):
        """
        Supprimer un devoir ou un cours (procedure)
        """
        model = Schedule(ctx)
        await model.remove_procedure(ctx)

    @commands.command(name="update")
    @is_schedule_channel()
    async def update(self, ctx):
        """
        Actualise et affiche l'agenda ou le planning
        """
        await Schedule(ctx).update_data()
        await ctx.message.delete()


class Notebook(Schedule):  # TODO
    pass


class Calendar(Schedule):  # TODO
    pass


def setup(bot):
    bot.add_cog(PlanningAndAgenda(bot))
