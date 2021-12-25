from __future__ import annotations

from datetime import datetime, timedelta
from threading import Timer
from typing import Iterable, NoReturn, Optional, Union

import discord
import sqlalchemy.exc
from cached_property import cached_property
from sqlalchemy import insert, select, update

from pyboss.models import MemberModel
from pyboss.utils import database
from pyboss.wrappers.guild import GuildWrapper


class MemberWrapper:
    """
    A class that wraps a Discord member and offers an interface
    for the database for attributes like XP, level, roles and blacklist date
    """

    def __init__(self, member: discord.Member):
        """
        Represente a member with additional attributes
        """
        self.member = member
        self.guild = GuildWrapper(member.guild)
        self.__model = self._fetch()

    def __getattr__(self, name: str):
        return getattr(self.member, name)

    def _fetch(self) -> Optional[MemberModel]:
        """
        Fetch from the database and returns the member if exists
        """
        try:
            return database.execute(
                select(MemberModel).where(MemberModel.id == self.member.id)
            ).scalar_one()
        except sqlalchemy.exc.NoResultFound:
            return None

    def update(self, **kwargs):
        """
        Accept keyword arguments only matching with a column in members table
        """
        database.execute(
            update(MemberModel).where(MemberModel.id == self.member.id).values(**kwargs)
        )

    def register(self) -> NoReturn:
        """
        Insert the member in table, with optionals attributes
        """
        database.execute(
            insert(MemberModel).values(id=self.member.id, name=self.member.name)
        )
        self.__model = self._fetch()  # Update the model

    def exists(self) -> bool:
        return self.__model is not None

    def place_in_blacklist(self, *, days=1, minutes=0):
        blacklist = datetime.now() + timedelta(days=days, minutes=minutes)
        self.update(blacklist=blacklist)
        Timer(
            (self._blacklist - datetime.now()).seconds, self._remove_from_blacklist
        ).start()

    def _remove_from_blacklist(self):
        self.update(blacklist="Null")

    @property
    def blacklist_date(self) -> Optional[datetime]:
        if self.__model.blacklist < datetime.now():
            self._remove_from_blacklist()
            return None
        return self.__model.blacklist

    @property
    def top_role(self) -> discord.Role:
        return self.guild.get_role_by_name(self._top_role_name)

    @top_role.setter
    def top_role(self, role: Union[discord.Role, str]):
        top_role_name = role if isinstance(role, str) else role.name
        self.update(top_role=top_role_name)

    @property
    def sub_roles(self) -> set[discord.Role]:
        sub_roles_names = self.__models.sub_roles.split(", ")
        return set(map(self.guild.get_role_by_name, sub_roles_names))

    @sub_roles.setter
    def sub_roles(self, roles: Iterable[discord.Role]):
        sub_roles_names = database.array_to_string(roles, "name")
        self.update(sub_roles=sub_roles_names)

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
        self.update(XP=value, level=level)

    @property
    def dm_choice_msg_id(self) -> int:
        return self.__model.dm_choice_msg_id

    @dm_choice_msg_id.setter
    def dm_choice_msg_id(self, message_id: int):
        self.update(choice_msg_id=message_id)

    @cached_property
    async def dm_choice_msg(self) -> discord.Message:
        return await self.fetch_message(self.dm_choice_msg_id)
