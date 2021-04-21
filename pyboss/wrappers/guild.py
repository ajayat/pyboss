from functools import cache
from typing import Optional

import discord


class GuildWrapper:
    def __init__(self, guild: discord.Guild):
        self.guild = guild

    def __getattr__(self, name: str):
        return getattr(self.guild, name)

    @cache
    def get_member_by_name(self, member: str) -> Optional[discord.Member]:
        try:
            return discord.utils.get(self.members, name=member)
        except AttributeError:
            return None

    @cache
    def get_member_by_id(self, member: int) -> Optional[discord.Member]:
        try:
            return discord.utils.get(self.members, id=member)
        except AttributeError:
            return None

    @cache
    def get_role_by_name(self, name: str) -> Optional[discord.Role]:
        for role in self.member.guild.roles:
            if role.name == name:
                return role
        return None

    # TODO: add methods publish_channel() etc...
