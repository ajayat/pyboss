from __future__ import annotations

from datetime import datetime, timedelta
from functools import cache
from threading import Timer
from typing import Iterable

import discord
from cached_property import cached_property

from pyboss.utils import database as db


class MemberController:
    """
    A class that represents a Discord member and offers an interface
    for the database for attributes like XP, level, roles and blacklist date
    """

    def __new__(cls, member: discord.Member) -> MemberController | None:
        """
        Create an instance of MemberController by fetching its data
        """
        sql = f"SELECT * FROM members WHERE member_id={member.id}"
        if data := db.execute(sql, dictionary=True, fetchone=True):
            return super().__new__(cls, member, **data)
        return None

    def __init__(self, member: discord.Member, **data):
        """
        Represente a member with additional attributes
        """
        self.member = member
        self._top_role_name: str = data["top_role"]
        self._group_role_name: str = data["group_role"]
        self._sub_roles_name: list = data["sub_roles"].split(", ")
        self.__level: int = data["level"]
        self.__XP: int = data["XP"]
        self.__validate_state: int = data["validate_state"]
        self.__blacklist: datetime = data["blacklist"]
        self.__dm_choice_msg_id: int = data["choice_msg_id"]

    def __getattr__(self, name: str):
        return getattr(self.member, name)

    def _update_db(self, **kwargs):
        """
        Accept keyword arguments only matching with a column in members table
        """
        sql = (
            f"UPDATE members "
            f"SET {'=%s, '.join(kwargs.keys())}=%s "
            f"WHERE member_id={self.member.id}"
        )
        db.execute(sql, tuple(kwargs.values()))

    @cache
    def get_role_by_name(self, name: str):
        for role in self.member.guild.roles:
            if role.name == name:
                return role
        return None

    def place_in_blacklist(self, *, days=1, minutes=0):
        self.__blacklist = datetime.now() + timedelta(days=days, minutes=minutes)
        self._update_db(blacklist=self._blacklist)
        Timer(
            (self._blacklist - datetime.now()).seconds, self._remove_from_blacklist
        ).start()

    def _remove_from_blacklist(self):
        self.__blacklist = None
        self._update_db(blacklist="Null")

    @property
    def blacklist_date(self) -> datetime:
        if self._blacklist < datetime.now():
            self._remove_from_blacklist()
        return self._blacklist

    @property
    def top_role(self) -> discord.Role:
        return self.get_role_by_name(self._top_role_name)

    @top_role.setter
    def top_role(self, role: discord.Role | str):
        self._top_role_name = role if isinstance(role, str) else role.name
        self._update_db(top_role=self._top_role_name)

    @property
    def group_role(self) -> discord.Role:
        return self.get_role_by_name(self._group_role_name)

    @group_role.setter
    def group_role(self, role: discord.Role | str):
        self._group_role_name = role if isinstance(role, str) else role.name
        self._update_db(group_role=self._group_role_name)

    @property
    def sub_roles(self) -> set[discord.Role]:
        return set(map(self.get_role_by_name, self._sub_roles_name))

    @sub_roles.setter
    def sub_roles(self, roles: Iterable[discord.Role, str]):
        self._sub_roles_name.clear()
        for role in roles:
            role_name = role if isinstance(roles, str) else role.name
            self._sub_roles_name.append(role_name)
        self._update_db(sub_roles=self._sub_roles_name)

    @property
    def validate_state(self):
        return self._validate_state

    @validate_state.setter
    def validate_state(self, value):
        self.__validate_state = value
        self._update_db(validate_state=value)

    @property
    def level(self):
        return self.__level

    @property
    def XP(self):
        return self.__XP

    @XP.setter
    def XP(self, value):
        value = max(value, 0)
        self._update_db(XP=value)
        level = int(value ** (1 / 2) / 50) + 1
        if self._level != level:
            self._update_db(level=level)
            self.__level = level

    @cached_property
    async def dm_choice_msg(self) -> discord.Message:
        return await self.fetch_message(self._dm_choice_msg_id)

    @property
    def dm_choice_msg_id(self) -> int:
        return self.__dm_choice_msg_id

    @dm_choice_msg_id.setter
    def dm_choice_msg_id(self, message_id: int):
        self.__dm_choice_msg_id = message_id
        self._update_db(choice_msg_id=message_id)
