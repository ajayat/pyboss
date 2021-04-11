from datetime import datetime, timedelta
from threading import Timer
from typing import Union

import discord

from utils import database as db

GUILD_NAME = "Terminales G"


class _MemberModel:
    def __init__(self, member: discord.Member, **data):
        """
        Representing a member with additional attributes
        """
        self.member = member
        self.class_group = data["class_group"]
        self.top_role = self.get_role_by_name(data["top_role"])
        sub_roles_name = data["sub_roles"].split(", ")
        self.sub_roles = set(map(self.get_role_by_name, sub_roles_name))
        self._level = data["level"]
        self._XP = data["XP"]
        self._validate_state = data["validate_state"]
        self._blacklist = data["blacklist"]
        self.dm_choice_msg_id = data["choice_msg_id"]

    def __getattr__(self, name):
        return getattr(self.member, name)

    def get_role_by_name(self, name: str) -> discord.Role:
        return discord.utils.get(self.member.guild.roles, name=name)

    def _update_db(self, **kwargs):
        """ Accept keyword arguments only matching with a column in members table """
        sql = (
            f"UPDATE members "
            f"SET {'=%s, '.join(kwargs.keys())}=%s "
            f"WHERE member_id={self.member.id}"
        )
        db.execute(sql, tuple(kwargs.values()))

    @property
    def validate_state(self):
        return self._validate_state

    @validate_state.setter
    def validate_state(self, value):
        self._validate_state = value
        self._update_db(validate_state=value)

    @property
    def level(self):
        return self._level

    @property
    def XP(self):
        return self._XP

    @XP.setter
    def XP(self, value):
        value = max(value, 0)
        self._update_db(XP=value)
        level = int(value ** (1 / 2) / 50) + 1
        if self._level != level:
            self._update_db(level=level)
            self._level = level

    @property
    def blacklist_date(self):
        if self._blacklist < datetime.now():
            self._remove_from_blacklist()
        return self._blacklist

    def place_in_blacklist(self, *, days=1, minutes=0):
        self._blacklist = datetime.now() + timedelta(days=days, minutes=minutes)
        self.update_db(blacklist=self._blacklist)
        Timer(
            (self._blacklist - datetime.now()).seconds, self._remove_from_blacklist
        ).start()

    def _remove_from_blacklist(self):
        self._blacklist = None
        self.update_db(blacklist="Null")


def get_member_model(bot, member: Union[int, discord.Member, discord.User]):
    """
    Get MemberModel type from a user, member or id and load its data
    """
    guild = discord.utils.get(bot.guilds, name=GUILD_NAME)
    if isinstance(member, int):
        member = discord.utils.get(guild.members, id=member)
    if isinstance(member, discord.User):
        member = discord.utils.get(guild.members, id=member.id)

    sql = f"SELECT * FROM members WHERE member_id={member.id}"
    mod_member = db.execute(sql, dictionary=True, fetchone=True)
    if mod_member:
        return _MemberModel(member, **mod_member)
    return None
