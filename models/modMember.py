import json
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
        self.top_role = discord.utils.get(member.guild.roles, name=data["top_role"])
        self.sub_roles = set()
        if sub_roles := data["sub_roles"]:
            self.sub_roles = set(sub_roles.split(", "))

        self._XP = data["XP"]
        self._level = data["level"]
        # 0: not validated, 1: Validate message active, 2: validate
        self._validate_state = data["validate_state"]
        self._blacklist = data["blacklist"]
        self._dm_choice_msg_id = data["choice_msg_id"]

    def __getattr__(self, name):
        return getattr(self.member, name)

    async def update_top_role(self, new_role_name):
        """
        async function
        """
        new_role = discord.utils.get(self.member.guild.roles, name=new_role_name)
        sql = "UPDATE members SET main_role=%s WHERE member_id=%s"
        db.execute(sql, (new_role_name, self.member.id))

        await self.member.remove_roles(self.top_role, reason="Changing the main role")
        self.top_role = new_role
        await self.member.add_roles(self.top_role, reason="Update the main role")
        return self.top_role

    async def add_sub_roles(self):
        for name in self.sub_roles:
            role = discord.utils.get(self.member.guild.roles, name=name)
            await self.member.add_roles(
                role, reason="The member has choice this matter"
            )

    @property
    def XP(self):
        return self._XP

    @XP.setter
    def XP(self, value):
        if value < 0:
            value = 0
        sql = f"UPDATE members SET XP={value} WHERE member_id={self.member.id}"
        db.execute(sql)
        self._XP = value

        level = int(value ** (1 / 2) / 50) + 1
        if self._level != level:
            self.level = level

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        sql = f"UPDATE members SET level={value} WHERE member_id={self.member.id}"
        db.execute(sql)
        self._level = value

    @property
    def sub_roles(self):
        return self._sub_roles

    @sub_roles.setter
    def sub_roles(self, roles):
        """ Property to update a role when set """
        self._sub_roles = set(roles)
        sub_roles = ", ".join(self._sub_roles)
        sql = "UPDATE members SET sub_roles=%s WHERE member_id=%s"
        db.execute(sql, (sub_roles, self.member.id))

    @property
    def dm_choice_msg_id(self):
        return self._dm_choice_msg_id

    @dm_choice_msg_id.setter
    def dm_choice_msg_id(self, id):
        sql = (
            f"UPDATE members SET choice_msg_id={id} "
            f"WHERE member_id={self.member.id}"
        )
        self._dm_choice_msg_id = db.execute(sql, fetchone=True)

    @property
    def validate_state(self):
        with open("statics/json/validate_states.json", "r", encoding="utf-8") as f:
            state = json.load(f).get(str(self.member.id), 0)
        return int(state)

    @validate_state.setter
    def validate_state(self, state):
        with open("statics/json/validate_states.json", "r", encoding="utf-8") as f:
            states = json.load(f)
        states[str(self.member.id)] = state
        with open("statics/json/validate_states.json", "w", encoding="utf-8") as f2:
            json.dump(states, f2)

    def get_blacklist_date(self):
        end_date = self._blacklist
        if end_date:
            if end_date <= datetime.now():
                self._remove_from_blacklist()
            return end_date

    def place_in_blacklist(self, *, days=1, minutes=0):
        end_date = datetime.now() + timedelta(days=days, minutes=minutes)
        sql = "UPDATE members SET blacklist=%s WHERE member_id=%s"
        db.execute(sql, (end_date, self.member.id))
        Timer((end_date - datetime.now()).seconds, self._remove_from_blacklist).start()

    def _remove_from_blacklist(self):
        sql = f"UPDATE members SET blacklist=Null WHERE member_id={self.member.id}"
        db.execute(sql)


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
