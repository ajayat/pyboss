import asyncio
import datetime
import json
import logging
import re

import discord
from discord.ext import commands
from discord.ext.commands import guild_only
from sqlalchemy import insert, select, update, delete

from pyboss import CONFIG, STATIC_DIR
from pyboss.models import CalendarModel, NotebookModel, ScheduleRefModel
from pyboss.utils import database
from pyboss.wrappers.member import MemberWrapper

from .utils.checkers import is_guild_owner, is_schedule_channel
from .utils.functions import send_embed

logger = logging.getLogger(__name__)

REGEX_HOUR = re.compile(
    r"^(?P<start>[0-1]?[0-9]|2[0-4])[hH]?[-àa; /:]*(?P<end>[0-1]?[0-9]|2[0-4])?[hH]?$"
)
REGEX_DATE = re.compile(r"^(?P<day>\d{1,2})[-\s/:]*(?P<month>\d{1,2})$")

# fmt: off
MONTHS = (
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
    "septembre", "octobre", "novembre", "décembre"
)
DAYS = ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche")
# fmt: on


class Schedule:

    with open(STATIC_DIR / "json/matters.json", encoding="utf-8") as wordlist:
        MATTERS = json.load(wordlist)

    def __init__(self, ctx, model):
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.author = ctx.author
        self.channel = ctx.channel
        self.model = model
        self.traced_msg = []
        self.subject = None
        self.response = None
        self.date = None
        self.description = None
        self.starthour, self.endhour = None, None

    async def send_question(self, question, check=None, timeout=60):
        msg_question = await self.channel.send(question)
        try:
            message = await self.bot.wait_for("message", timeout=timeout, check=check)
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError
        else:
            await message.delete()
        finally:
            await msg_question.delete()

    async def delete_traced_msg(self):
        for msg in self.traced_msg:
            try:
                await msg.delete()
            except discord.errors.NotFound:
                pass

    def get_data(self, model):
        return database.execute(
            select(model)
            .where(
                model.channel_id == self.channel.id,
                model.date >= datetime.datetime.now(),
            )
            .order_by(model.date)
        )

    @staticmethod
    async def update_message_ref(message: discord.Message):
        """
        Update id of agenda or planning message in database
        """
        ref_model = database.execute(
            select(ScheduleRefModel).where(
                ScheduleRefModel.channel_id == message.channel.id,
            )
        ).scalar_one_or_none()
        if ref_model:
            database.execute(
                update(ScheduleRefModel)
                .where(ScheduleRefModel.channel_id == message.channel.id)
                .values(message_id=message.id)
            )
            try:
                ex_message = await message.channel.fetch_message(ref_model.message_id)
            except (discord.NotFound, discord.HTTPException):
                return
            await ex_message.delete()
        else:
            database.execute(
                insert(ScheduleRefModel).values(
                    guild_id=message.guild.id,
                    channel_id=message.channel.id,
                    message_id=message.id,
                )
            )

    async def remove_procedure(self, update_fct=None):
        try:
            await self.send_question(
                "Quelle matière voulez-vous supprimer?",
                timeout=60,
                check=self.is_subject_valid,
            )
            await self.send_question(
                "De quel jour? (Ex: JJ/MM)", timeout=60, check=self.is_date_valid
            )
        except asyncio.TimeoutError:
            await self.channel.send(
                f"{self.author.mention} Vous avez mis trop de temps à répondre"
            )
            raise asyncio.TimeoutError
        else:
            database.execute(
                delete(self.model).where(
                    self.model.subject == self.subject, self.model.date == self.date
                )
            )
            if callable(update_fct):
                await update_fct()
        finally:
            await self.delete_traced_msg()

    def is_subject_valid(self, msg: discord.Message):
        """
        Check if the user write a correct subject and place him in blacklist if not.
        """
        if msg.channel != self.channel or msg.author.id != self.author.id:
            return False
        member = MemberWrapper(msg.author)

        if subject := self.MATTERS.get(msg.content.upper()):
            self.subject = subject
        elif not member.blacklist_date:
            member.place_in_blacklist()
            self.subject = msg.content.title()
        else:
            seconds = (member.blacklist_date - datetime.datetime.now()).total_seconds()
            hours, minutes = seconds // 3600, (seconds % 3600) // 60
            self.response = (
                f"Vous n'êtes pas autorisé à ajouter un évènement spécial "
                f"pendant encore {int(hours)}h {int(minutes)}min. "
            )
            return False
        return True

    def is_date_valid(self, msg: discord.Message):
        """
        Check with a regex the data as user input, can accept several formats
        """
        if msg.channel != self.channel or msg.author.id != self.author.id:
            return False

        match = REGEX_DATE.match(msg.content)
        if not match:
            self.response = "Votre format de date est invalide"
            logger.info(f"The user {msg.author.name} hasn't wrote correctly the date")
            return False

        day, month = map(int, match.groups())
        try:
            today = datetime.date.today()
            year = today.year if month >= today.month else today.year + 1
            date_user = datetime.date(year=year, month=month, day=day)
        except ValueError:
            self.response = "Vous avez mis des valeurs invalides"
            return False

        if date_user.weekday() < 5:
            if date_user >= datetime.date.today():
                self.date = str(date_user)
                return True
            self.response = f"{day}/{month} est antérieur à la date actuelle"
            return False
        self.response = "On ne travaille pas le week end!"
        return False

    def is_hours_valid(self, msg: discord.Message):
        if msg.channel != self.channel or msg.author.id != self.author.id:
            return False
        try:
            match = REGEX_HOUR.match(msg.content)
            starthour = int(match.group(1))
        except (KeyError, ValueError):
            self.response = "Votre format de plage horaire est invalide."
        else:
            if not (endhour := match.group(2)):
                endhour = str(starthour + 1)
            self.starthour, self.endhour = f"{starthour}h", f"{endhour}h"
            return True

    def is_description_valid(self, msg: discord.Message):
        if msg.channel != self.channel or msg.author.id != self.author.id:
            return False
        if msg.content.strip().upper() != "NON":
            self.description = msg.content
        return True


class Calendar(Schedule):
    def __init__(self, ctx):
        super().__init__(ctx, CalendarModel)

    async def rules(self):
        """
        Send the rules for planning or agenda channel
        """
        with open(STATIC_DIR / "text/calendar_rules.md") as calendar:
            content = calendar.read()
            title = "Fonctionnement du planning"
        await send_embed(self.bot, self.channel, title, content)

    async def new(self):
        try:
            await self.send_question(
                "Quelle matière voulez-vous ajouter ?", self.is_subject_valid
            )
            await self.send_question(
                "A quelle date le cours aura lieu ? (Ex : JJ/MM)",
                self.is_date_valid,
            )
            await self.send_question(
                "A quelle heure ? (Ex: 10h; 10h/12h…)", self.is_hours_valid
            )
            await self.send_question(
                "Voulez-vous ajouter des infos supplémentaires? "
                "('votre contenu' ou 'non')",
                self.is_description_valid,
                timeout=120,
            )
        except asyncio.TimeoutError:
            await self.channel.send(
                f"{self.author.mention} Vous avez mis trop de temps à répondre"
            )
            if self.response:
                await self.channel.send(f"Détails: \n{self.response}")
        else:
            database.execute(
                insert(CalendarModel).values(
                    guild_id=self.guild.id,
                    channel_id=self.channel.id,
                    subject=self.subject,
                    description=self.description,
                    date=self.date,
                    starthour=self.starthour,
                    endhour=self.endhour,
                )
            )
            await self.update()
        finally:
            await self.delete_traced_msg()

    async def update(self):
        """
        Fetch the database to get the list of rows ordered by date
        """
        next_date, message = None, ""
        for row in self.get_data(CalendarModel):
            date = row[0].date
            if date != next_date:
                next_date = date
                day = DAYS[date.weekday()]
                month = MONTHS[int(f"{date:%m}") - 1]
                message += f"\n__Pour le **{day}** {date:%d} {month}:__\n"

            description = f"*({row[0].description})*" if row[0].description else ""
            message += (
                f"- \t {row[0].subject}: "
                f"**{row[0].starthour}**-**{row[0].endhour}** {description}\n"
            )

        embed = discord.Embed(
            colour=0x22CCFF, title="Cours à venir:", description=message
        )
        embed.set_thumbnail(url=CONFIG["images"]["calendar"]["url"])
        new_msg = await self.channel.send(embed=embed)
        await self.update_message_ref(new_msg)


class Notebook(Schedule):
    def __init__(self, ctx):
        super().__init__(ctx, NotebookModel)

    async def rules(self):
        """
        Send the rules for planning or agenda channel
        """
        with open(STATIC_DIR / "text/notebook_rules.md") as notebook:
            content = notebook.read()
            title = "Fonctionnement de l'agenda"
        await send_embed(self.bot, self.channel, title, content)

    async def new(self):
        try:
            await self.send_question(
                "Quelle matière voulez-vous ajouter ?", self.is_subject_valid
            )
            await self.send_question(
                "Quelle est la date limite du devoir ? (Ex : JJ/MM)",
                self.is_date_valid,
            )
            await self.send_question(
                "Indiquez quels sont les devoirs à faire (obligatoire):",
                self.is_description_valid,
                timeout=120,
            )
        except asyncio.TimeoutError:
            await self.channel.send(
                f"{self.author.mention} Vous avez mis trop de temps à répondre"
            )
            if self.response:
                await self.channel.send(f"Détails: \n{self.response}")
        else:
            database.execute(
                insert(NotebookModel).values(
                    guild_id=self.guild.id,
                    channel_id=self.channel.id,
                    subject=self.subject,
                    description=self.description,
                    date=self.date,
                )
            )
            await self.update()
        finally:
            await self.delete_traced_msg()

    async def update(self):
        """
        Fetch the database to get the list of rows ordered by date
        """
        next_date, message = None, ""
        for row in self.get_data(NotebookModel):
            date = row[0].date
            if date != next_date:
                next_date = date
                day = DAYS[date.weekday()]
                month = MONTHS[int(f"{date:%m}") - 1]
                message += f"\n__Pour le **{day}** {date:%d} {month}:__\n"
            message += f"\n**{row[0].subject}**: {row[0].description}\n"

        embed = discord.Embed(
            colour=0x22CCFF, title="Devoirs à faire:", description=message
        )
        embed.set_thumbnail(url=CONFIG["images"]["notebook"]["url"])
        new_msg = await self.channel.send(embed=embed)
        await self.update_message_ref(new_msg)


class ScheduleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_schedule(ctx):
        if is_schedule_channel(ctx, "notebook"):
            return Notebook(ctx)
        if is_schedule_channel(ctx, "calendar"):
            return Calendar(ctx)

    @commands.command(name="new")
    @guild_only()
    async def new(self, ctx):
        if schedule := self.get_schedule(ctx):
            await ctx.message.delete()
            await schedule.new()

    @commands.command(name="del")
    @guild_only()
    async def remove(self, ctx):
        if schedule := self.get_schedule(ctx):
            await ctx.message.delete()
            await schedule.remove_procedure(update_fct=schedule.update)

    @commands.command(name="update")
    @guild_only()
    async def update(self, ctx):
        if schedule := self.get_schedule(ctx):
            await ctx.message.delete()
            await schedule.update()

    @commands.command(name="rules", hidden=True)
    @is_guild_owner()
    async def rules(self, ctx):
        if schedule := self.get_schedule(ctx):
            await ctx.message.delete()
            await schedule.rules()


def setup(bot):
    bot.add_cog(ScheduleCog(bot))
