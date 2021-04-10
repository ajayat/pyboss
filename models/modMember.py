from datetime import datetime, timedelta
from threading import Timer

import discord

import database as db


class _ModMember:
    def __init__(self, member: discord.Member, **data):
        """
        Representing a member with additional attributes
        """
        self.member = member
        self.class_group = data["class_group"]
        self.top_role = data["top_role"]
        self.sub_roles = set()
        if sub_roles := data["sub_roles"]:
            self.sub_roles = set(sub_roles.split(", "))

        self._XP = data["XP"]
        self.level = data["level"]
        self._blacklist = data["blacklist"]
        self.dm_choice_msg_id = data["choice_msg_id"]

    def __getattr__(self, name):
        return getattr(self.member, name)

    def update_db(self, **kwargs):
        """ Accept keyword arguments only matching with a column in members table """
        sql = (
            f"UPDATE members "
            f"SET {'=%s, '.join(kwargs.keys())}=%s "
            f"WHERE member_id={self.member.id}"
        )
        db.execute(sql, tuple(kwargs.values()))

    async def update_top_role(self, new_role_name):
        new_role = discord.utils.get(self.member.guild.roles, name=new_role_name)
        top_role = discord.utils.get(self.member.guild.roles, name=self.top_role)
        self.update_db(top_role=new_role_name)

        await self.member.remove_roles(top_role, reason="Changing the class")
        await self.member.add_roles(new_role, reason="Update the class")

    @property
    def XP(self):
        return self._XP

    @XP.setter
    def XP(self, value):
        if value < 0:
            value = 0
        self.update_db(XP=value)

        level = int(value ** (1 / 2) / 50) + 1
        if self.level != level:
            self.update_db(level=level)

    def get_blacklist_date(self):
        end_date = self._blacklist
        if end_date:
            if end_date <= datetime.now():
                self._remove_from_blacklist()
            return end_date

    def place_in_blacklist(self, *, days=1, minutes=0):
        end_date = datetime.now() + timedelta(days=days, minutes=minutes)
        self.update_db(blacklist=end_date)
        Timer((end_date - datetime.now()).seconds, self._remove_from_blacklist).start()

    def _remove_from_blacklist(self):
        self.update_db(blacklist="Null")


def get_mod_member(bot, member, guild_name="Terminales G"):
    """
    Get ModMember type with a associate discord member id
    """
    member_id = member.id if isinstance(member, discord.Member) else member
    guild = discord.utils.get(bot.guilds, name=guild_name)
    member = discord.utils.get(guild.members, id=member_id)

    sql = f"SELECT * FROM members WHERE member_id={member_id}"
    mod_member = db.execute(sql, dictionary=True, fetchone=True)
    if mod_member:
        return _ModMember(member, **mod_member)
