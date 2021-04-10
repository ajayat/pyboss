import asyncio
import datetime
import json
import logging
import re

import discord
from discord.ext import commands

import database as db
from models.modMember import get_mod_member

with open("static/json/channels_tables.json") as f:
    CHANNELS_TABLES = json.load(f)


def check_source(func):
    def evaluate(self, msg):
        if msg.channel == self.channel and msg.author.id == self.author.id:
            return func(self, msg)

    return evaluate


def authorized_channels(ctx):
    if not isinstance(ctx, discord.DMChannel):
        return str(ctx.channel.id) in PlanningAndAgendaModel.CHANNELS_TABLES


async def update_message_ref(fieldname, message: discord.Message):
    """
    update id of agenda or planning message in messages_id.json file
    """
    sql = f"SELECT message_id FROM specials WHERE name='{fieldname}'"
    (ex_message_id,) = db.execute(sql, fetchone=True)
    sql = "UPDATE specials SET message_id=%s WHERE name=%s"
    db.execute(sql, (message.id, fieldname))
    try:
        ex_message = await message.channel.fetch_message(ex_message_id)
    except (discord.NotFound, discord.HTTPException):
        return
    await ex_message.delete()


class PlanningAndAgendaModel:
    MONTHS = (
        "janvier",
        "février",
        "mars",
        "avril",
        "mai",
        "juin",
        "juillet",
        "août",
        "septembre",
        "octobre",
        "novembre",
        "décembre",
    )
    DAYS = ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi")

    with open("static/json/channels_tables.json") as f:
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
                    "Quelle matière voulez-vous ajouter ?", self._check_matter
                )
                await self.gen_question(
                    "A quelle date le cours aura lieu ? (Ex : JJ/MM)", self._check_date
                )
                await self.gen_question(
                    "A quelle heure ? (Ex: 10h; 10h/12h…)", self._check_hours
                )
                await self.gen_question(
                    'Voulez-vous ajouter des infos supplémentaires? ("votre contenu" ou "non")',
                    self._check_description,
                    timeout=120,
                )
            else:
                await self.gen_question(
                    "Quelle matière voulez-vous ajouter ?", self._check_matter
                )
                await self.gen_question(
                    "Quelle est la date limite du devoir ? (Ex : JJ/MM)",
                    self._check_date,
                )
                await self.gen_question(
                    "Indiquez quels sont les devoirs à faire (obligatoire):",
                    self._check_description,
                    timeout=120,
                )
        except asyncio.TimeoutError:
            await ctx.author.send(
                f"{ctx.author.mention} Vous avez mis trop de temps à répondre ou vos réponses "
                f"n'étaient pas correct. {self.custom_response}"
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
            resp1 = await self.bot.wait_for(
                "message", timeout=60, check=self._check_matter
            )
            await msg1.delete()
            await resp1.delete()

            msg2 = await ctx.channel.send("De quel jour? (Ex: JJ/MM)")
            self.traces.append(msg2)
            resp2 = await self.bot.wait_for(
                "message", timeout=120, check=self._check_date
            )
            await msg2.delete()
            await resp2.delete()

        except asyncio.TimeoutError:
            await self.author.send(
                f"{self.author.mention} Vous avez mis trop de temps à répondre ou vos réponses"
                f"n'étaient pas correct. {self.custom_response}"
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

    async def gen_question(self, question, check, timeout=60):
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
                day = self.DAYS[date.weekday()]
                month = self.MONTHS[int(f"{date:%m}") - 1]
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
        embed.set_thumbnail(
            url="https://cruxnow.com/wp-content/uploads/2019/09/book-1853677_1280-1024x682.jpg"
        )
        new_msg = await self.channel.send(embed=embed)

        await update_message_ref(f"{self.table}_{self.table_class}", new_msg)

    # ------------------------------ CHECKS -----------------------------

    @check_source
    def _check_matter(self, msg):
        """
        Callback to check if the user write a correct matter and place in blacklist if not
        """
        content = msg.content.upper()
        mod_member = get_mod_member(self.bot, msg.author)
        end_date = mod_member.get_blacklist_date()

        with open("static/json/matters_wordlist.json", encoding="utf-8") as wordlist:
            matters_wordlist = json.load(wordlist)
        if matters_wordlist.get(content):
            self.answers["matter"] = matters_wordlist[content]

        elif not end_date:
            mod_member.place_in_blacklist()
            self.answers["matter"] = content.title()
        else:
            timedelta = end_date - datetime.datetime.now()
            hours, minutes = (
                timedelta.total_seconds() // 3600,
                (timedelta.total_seconds() % 3600) // 60,
            )
            self.custom_response = (
                f"Vous n'êtes pas autorisé à ajouter un évènement spécial "
                f"pendant encore {int(hours)}h {int(minutes)}min. "
            )
            return False
        return True

    @check_source
    def _check_date(self, msg):
        """
        Check with a regex the data as user input, can accept several formats
        """
        regex = re.match(r"^(\d{1,2})[-\s/:]*(\d{1,2})$", msg.content)
        if regex:
            day, month = map(int, (regex.group(1), regex.group(2)))
            try:
                today = datetime.date.today()
                year = today.year if today.month > month else today.year + 1
                date_user = datetime.date(year=year, month=month, day=day)
            except ValueError:
                self.custom_response = "Vous avez mis des valeurs invalides"
                return

            if date_user.weekday() < 5:
                if date_user >= datetime.date.today():
                    self.answers["date"] = str(date_user)
                    return True
                else:
                    self.custom_response = (
                        f"Vous ne pouvez pas ajouter ou supprimer des cours car "
                        f"{day}/{month} est antérieur à la date d'aujourd'hui"
                    )
            else:
                self.custom_response = "On ne travaille pas le week end! \
                                        Votre jour doit faire parti de la semaine."
        else:
            self.custom_response = "Votre format de date est invalide."
            logging.info(f"The user {msg.author.name} hasn't wrote correctly the date")

    @check_source
    def _check_hours(self, msg):
        try:
            regex = re.match(
                r"^(?P<start>\d{1,3})[hH]?[-àa; /:]*(?P<end>\d{1,2})?[hH]?$",
                msg.content,
            )
            starthour, endhour = map(int, (regex.group("start"), regex.group("end")))
        except KeyError:
            self.custom_response = "Votre format de plage horaire est invalide."
        else:
            if starthour < 24 and (not endhour or endhour < 24):
                # verifying if endhour exists or calculate it
                if not endhour:
                    endhour = str(starthour + 1)
                self.answers["starthour"] = starthour + "h"
                self.answers["endhour"] = endhour + "h"
                return True
            self.custom_response = (
                "Veuillez saisir une heure valide comprise entre 0 et 24h"
            )

    @check_source
    def _check_description(self, msg):
        if msg.content.strip().upper() != "NON":
            self.answers["description"] = msg.content
        return True


class PlanningAndAgenda(commands.Cog):
    """
    A controller class to listen commands
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rules", hidden=True)
    @commands.is_owner()
    @commands.check(authorized_channels)
    async def send_planning_rules(self, ctx):
        """
        send the rules for planning or agenda channel
        """
        await ctx.message.delete()
        if "agenda" in ctx.channel.name:
            with open("static/txt/agenda_rules.txt", encoding="utf-8") as agenda:
                content = agenda.read()
                title = "Fonctionnement de l'agenda"
        else:
            with open("static/txt/planning_rules.txt", encoding="utf-8") as planning:
                content = planning.read()
                title = "Fonctionnement du planning"

        embed = discord.Embed(title=title, description=content, colour=0xFFA325)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_footer(
            text=f"Generated by {self.bot.user.name} | {datetime.datetime.now():%D - %H:%M}"
        )
        await ctx.send(embed=embed)

    @commands.command(name="new")
    @commands.check(authorized_channels)
    async def new_item(self, ctx):
        """
        Ajoute un cours ou un devoir (procedure)
        """
        model = PlanningAndAgendaModel(ctx)
        await model.new_procedure(ctx)

    @commands.command(name="del")
    @commands.check(authorized_channels)
    async def remove_item(self, ctx):
        """
        Supprimer un devoir ou un cours (procedure)
        """
        model = PlanningAndAgendaModel(ctx)
        await model.remove_procedure(ctx)

    @commands.command(name="update")
    @commands.check(authorized_channels)
    async def update(self, ctx):
        """
        Actualise et affiche l'agenda ou le planning
        """
        await PlanningAndAgendaModel(ctx).update_data()
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(PlanningAndAgenda(bot))
