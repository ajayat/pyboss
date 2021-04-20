from functools import cache
from typing import Union

import discord

from .member import MemberController


class GuildController:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.members = tuple(map(MemberController, guild.members))

    def __getattr__(self, name: str):
        return getattr(self.guild, name)

    @cache
    def get_member_by_name(self, member: str) -> Union[MemberController, None]:
        try:
            return discord.utils.get(self.members, name=member)
        except AttributeError:
            return None

    @cache
    def get_member_by_id(self, member: int) -> Union[MemberController, None]:
        try:
            return discord.utils.get(self.members, id=member)
        except AttributeError:
            return None

    # TODO: add methods publish_channel() etc...
