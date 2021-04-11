import asyncio
import itertools
import json
import logging
import math
import random
import string

import discord
from discord.ext import commands

from models.member import get_member_model
from utils import database as db


def quiz_channel(ctx):
    if not isinstance(ctx, discord.DMChannel):
        return "quiz" in ctx.channel.name or "test" in ctx.channel.name
    return False


class Question:

    COLOURS = [0xFFFF00, 0x0000FF, 0xFF0000, 0xFF75FF, 0x00FF00, 0x757575, 0x75FF75]
    TIMEOUT_MESSAGES = [
        "Le temps est écoulé!",
        "ding ding it's finish",
        "Il est l'heure !",
        "Allez hop on rembale !",
        "Coulé est le temps",
        "Le dernier grain de sable est tombé dans le sablier",
        "Avez vous vu l'heure !? Temps terminé !",
    ]

    def __init__(self, bot, channel: discord.TextChannel, question: dict):
        self.bot = bot
        self.channel = channel
        self.question_dict = question
        self.player_wins = set()
        self.player_loses = set()
        self.message = None

    async def send_question(self, timeout=30.0):
        """
        send a question
        question is a dict selected from the database
        """

        embed = discord.Embed(
            title=self.question_dict["question"],
            colour=random.choice(self.COLOURS),
            description=self.question_dict["propositions"],
        )
        embed.set_author(name=self.question_dict["theme"])
        embed.set_footer(text=f"Auteur: {self.question_dict['author']}")
        self.message = await self.channel.send(embed=embed)

        for p in self.question_dict["propositions"].split("\n"):
            if p:
                with open("static/json/letters_emojis.json", encoding="utf-8") as f:
                    emoji = json.load(f)[p[0]]
                await self.message.add_reaction(emoji)

        await asyncio.sleep(timeout)

    async def send_rank(self):
        """
        check reactions, send a rank info and ajust XP of the members
        """

        def win_score(n, coef, level):
            return math.ceil(((200 + level) * math.sqrt(n)) / (math.sqrt(coef) * level))

        def lose_score(level):
            return math.ceil(20 * math.sqrt(level))

        description = "**Gagnants**: \n" if self.player_wins else ""
        nb_players = len(self.player_wins) + len(self.player_loses)

        for id, i in zip(self.player_wins, itertools.count(1)):
            mod_member = get_member_model(self.bot, id)
            score = win_score(nb_players, i, mod_member.level)
            description += f"{i}. {mod_member.name}: +{score}XP \n"
            mod_member.XP += score

        description += "\n**Perdants**: \n" if self.player_loses else ""
        for id in self.player_loses:
            mod_member = get_member_model(self.bot, id)
            score = lose_score(nb_players)
            description += f":small_red_triangle_down: {mod_member.name}: -{score}XP \n"
            mod_member.XP -= score

        embed = discord.Embed(
            title=":hourglass: Résultats de la question:",
            colour=random.choice(self.COLOURS),
            description=description,
        )
        embed.set_footer(text=random.choice(self.TIMEOUT_MESSAGES))
        await self.channel.send(embed=embed)

        return self.player_wins, self.player_loses


class Quiz(commands.Cog):
    """
    Quiz can permit to obtain XP and level up...
    """

    def __init__(self, bot):
        self.bot = bot
        self.party_active = False
        self.active_questions = []
        self.scores = {}

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, msg):
        """Obtain a few XP per message"""
        if msg.author.id != self.bot.user.id and not msg.content.startswith("!"):
            try:
                mod_member = get_member_model(self.bot, msg.author.id)
                mod_member.XP += 25
            except AttributeError:
                pass

    @commands.command(name="question", aliases=["q"])
    @commands.guild_only()
    @commands.check(quiz_channel)
    async def question(self, ctx):
        """
        Générer une question de quiz aléatoire
        """
        sql = "SELECT * FROM quiz ORDER BY RAND () LIMIT 1"
        question_dict = db.execute(sql, fetchone=True, dictionary=True)
        question = Question(self.bot, ctx.channel, question_dict)
        self.active_questions.append(question)
        await question.send_question(timeout=30.0)
        self.active_questions.remove(question)
        await question.send_rank()

    @commands.Cog.listener("on_reaction_add")
    @commands.guild_only()
    async def _reaction_on_question(self, reaction, player):
        """
        remove ex reactions of the user in a quiz question
        """

        def get_question_if_active(question):
            for q in self.active_questions:
                if question.id == q.message.id:
                    return q
            return None

        msg = reaction.message
        question_class = get_question_if_active(msg)
        if player == self.bot.user or not question_class or reaction.count <= 1:
            return

        with open("static/json/letters_emojis.json", encoding="utf-8") as f:
            correct_reaction = json.load(f)[question_class.question_dict["response"]]

        for react in msg.reactions:
            async for user in react.users():
                if user == player and react is reaction:
                    wins, loses = (
                        question_class.player_wins,
                        question_class.player_loses,
                    )
                    if str(react.emoji) == correct_reaction:
                        wins.add(user.id)
                        loses.remove(user.id)
                    else:
                        loses.add(user.id)
                        wins.remove(user.id)
                elif user.id != self.bot.user.id:
                    await react.remove(user)

    @commands.command(name="quiz")
    @commands.guild_only()
    @commands.check(quiz_channel)
    async def many_questions(self, ctx, nb_questions=10):
        """
        Lancer une partie de n question
        """
        if self.party_active:
            return
        self.party_active, self.scores = True, {}
        sql = f"SELECT * FROM quiz ORDER BY RAND() LIMIT {nb_questions}"
        questions_dict = db.execute(sql, fetchall=True, dictionary=True)

        for question_dict in questions_dict:
            question = Question(self.bot, ctx.channel, question_dict)
            await question.send_question(timeout=30.0)
            self.active_questions.append(question)
            await asyncio.sleep(30.0)
            self.active_questions.remove(question)
            wins, _ = await question.send_rank()

            for id in wins:
                mod_member = get_member_model(self.bot, id)
                self.scores[mod_member.name] = self.scores.get(mod_member.name, 0) + 1
            await asyncio.sleep(30.0)

        await self.get_rank(ctx)
        self.party_active = False

    @commands.command(name="rank")
    @commands.guild_only()
    @commands.check(quiz_channel)
    async def get_rank(self, ctx):
        """
        Affiche le classement de la partie en cours
        """
        if not self.party_active:
            return
        titre, description = "Classements du Quiz:", ""
        association = sorted(self.scores.items(), key=lambda c: c[1], reverse=True)
        medals = [":first_place:", ":second_place:", ":third_place:"]

        for rang, (player, score) in enumerate(association):
            rang = medals[rang] if rang < 3 else rang + 1
            description += f"{rang}  {player} : {score} points \n"

        await ctx.send(
            embed=discord.Embed(title=titre, colour=0x00FF00, description=description)
        )

    @commands.command(name="question_add", aliases=["q_add"])
    @commands.check(quiz_channel)
    async def question_add_procedure(self, ctx):
        """
        Ajouter une question dans la base de donnée (procedure)
        """
        await ctx.message.delete()

        async def send_question(q, timeout=60.0):
            msg = await ctx.send(q)
            msg_response = await self.bot.wait_for(
                "message", check=lambda m: m.author == ctx.author, timeout=timeout
            )
            content = msg_response.content
            await msg.delete()
            await msg_response.delete()
            return content

        try:
            theme = await send_question(
                "Quel est le thème de votre question ? (Ex: Informatique)", timeout=30.0
            )
            question = await send_question("Quelle est votre question ?", timeout=60.0)
            propositions = await send_question(
                "Quelles sont les propositions (séparées par des /, minimum 3) ? \n"
                "Mettez un * à la fin de la bonne proposition (Ex: P1* / P2 / P3)",
                timeout=180.0,
            )
        except asyncio.TimeoutError:
            await ctx.author.send(
                "Vous avez mis trop de temps à ajouter la question, veuillez réesayer"
            )
        else:
            propositions = propositions.split("/")
            response = None
            for (i, p), letter in zip(enumerate(propositions), string.ascii_uppercase):
                if p.strip().endswith("*"):
                    response = letter
                    p = p.rstrip("* ")
                propositions[i] = f"{letter}) {p}"

            if not response:
                logging.error(
                    f"The question {question} hasn't response or propositions"
                )
            propositions = "\n".join(propositions)
            sql = (
                "INSERT INTO quiz (author, theme, question, propositions, response) "
                "VALUES (%s, %s, %s, %s, %s)"
            )
            db.execute(sql, (ctx.author.name, theme, question, propositions, response))

            mod_member = get_member_model(self.bot, ctx.author)
            mod_member.XP += 500
            embed = discord.Embed(
                title="Merci!",
                colour=0x5A546C,
                description=f"{ctx.author.mention} a ajouté une nouvelle question!",
            )
            embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.set_author(name=ctx.author.name)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Quiz(bot))
