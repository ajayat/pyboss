from __future__ import annotations

from datetime import datetime, timedelta
from functools import cache
from threading import Timer
from typing import Iterable, Optional, Union

import discord
from cached_property import cached_property
from sqlalchemy import select, update

from pyboss.models import Member
from pyboss.utils import database


class MemberController:
    """
    A class that represents a Discord member and offers an interface
    for the database for attributes like XP, level, roles and blacklist date
    """

    def __new__(cls, member: discord.Member, *args) -> Optional[MemberController]:
        """
        Create an instance of MemberController by fetching its data
        """
        stmt = select(Member).where(id=member.id)
        if model := database.execute(stmt).first():
            return super().__new__(cls, member, model)
        return None

    def __init__(self, member: discord.Member, model):
        """
        Represente a member with additional attributes
        """
        self.member = member
        self.__model = model

    def __getattr__(self, name: str):
        return getattr(self.member, name)

    def _update(self, **kwargs):
        """
        Accept keyword arguments only matching with a column in members table
        """
        database.execute(update(Member).where(id=self.member.id).values(**kwargs))

    @cache
    def get_role_by_name(self, name: str) -> Optional[discord.Role]:
        for role in self.member.guild.roles:
            if role.name == name:
                return role
        return None

    def place_in_blacklist(self, *, days=1, minutes=0):
        blacklist = datetime.now() + timedelta(days=days, minutes=minutes)
        self._update(blacklist=blacklist)
        Timer(
            (self._blacklist - datetime.now()).seconds, self._remove_from_blacklist
        ).start()

    def _remove_from_blacklist(self):
        self._update(blacklist="Null")

    @property
    def blacklist_date(self) -> Optional[datetime]:
        if self.__model.blacklist < datetime.now():
            self._remove_from_blacklist()
            return None
        return self.__model.blacklist

    @property
    def top_role(self) -> discord.Role:
        return self.get_role_by_name(self._top_role_name)

    @top_role.setter
    def top_role(self, role: Union[discord.Role, str]):
        top_role_name = role if isinstance(role, str) else role.name
        self._update(top_role=top_role_name)

    @property
    def group_role(self) -> discord.Role:
        return self.get_role_by_name(self._group_role_name)

    @group_role.setter
    def group_role(self, role: Union[discord.Role, str]):
        group_role_name = role if isinstance(role, str) else role.name
        self._update(group_role=group_role_name)

    @property
    def sub_roles(self) -> set[discord.Role]:
        sub_roles_names = self.__models.sub_roles.split(", ")
        return set(map(self.get_role_by_name, sub_roles_names))

    @sub_roles.setter
    def sub_roles(self, roles: Iterable[discord.Role]):
        sub_roles_names = database.array_to_string(roles, "name")
        self._update(sub_roles=sub_roles_names)

    @property
    def validate_state(self):
        return self.__model.validate_state

    @validate_state.setter
    def validate_state(self, value):
        self._update(validate_state=value)

    @property
    def level(self):
        return self.__model.level

    @property
    def XP(self):
        return self.__model.XP

    @XP.setter
    def XP(self, value):
        value = max(value, 0)
        level = int(value ** (1 / 2) / 50) + 1
        self._update(XP=value, level=level)

    @property
    def dm_choice_msg_id(self) -> int:
        return self.__model.dm_choice_msg_id

    @dm_choice_msg_id.setter
    def dm_choice_msg_id(self, message_id: int):
        self._update(choice_msg_id=message_id)

    @cached_property
    async def dm_choice_msg(self) -> discord.Message:
        return await self.fetch_message(self.dm_choice_msg_id)
