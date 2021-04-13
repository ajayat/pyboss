from functools import cache

import discord
from controllers.member import MemberController


class GuildController:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.members = tuple(map(MemberController, guild.members))

    def __getattr__(self, name: str):
        return getattr(self.guild, name)

    @cache
    def get_member_by_name(self, member: str) -> MemberController | None:
        try:
            return discord.utils.get(self.members, name=member)
        except AttributeError:
            return None

    @cache
    def get_member_by_id(self, member: int) -> MemberController | None:
        try:
            return discord.utils.get(self.members, id=member)
        except AttributeError:
            return None
