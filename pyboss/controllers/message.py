import datetime
from typing import NoReturn

import discord
from sqlalchemy import insert

from pyboss.models import Message
from pyboss.utils import database


class MessageController:
    def __init__(self, message: discord.Message):
        self.member = message

    def __getattr__(self, name: str):
        return getattr(self.message, name)

    def insert(self) -> NoReturn:
        """
        Inserts a message row in messages table
        """
        channel = (
            "DMChannel"
            if isinstance(self.message.channel, discord.DMChannel)
            else self.message.channel.name
        )
        database.execute(
            insert(Message).values(
                author_id=self.message.author.id,
                channel=channel,
                date=datetime.datetime.now(),
                content=self.message.content,
            )
        )
