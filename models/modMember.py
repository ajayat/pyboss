import json
from datetime import datetime, timedelta
from threading import Timer

import discord

import database


class _ModMember:
    def __init__(self, member: discord.Member, **data):
        """
        Representing a member with additional attributes
        """
        self.member = member
        self.main_role = discord.utils.get(member.guild.roles, name=data["main_role"])
        self._XP = data["XP"]
        self._level = data["level"]
        self._validate_state = data[
            "validate_state"
        ]  # 0: not validated, 1: Validate message active, 2: validate
        self._blacklist = data["blacklist"]
        if self._blacklist:
            t = self._blacklist - datetime.now()
            Timer(t.seconds, self._remove_from_blacklist).start()

        with open("static/json/members_sub_roles.json", encoding="utf-8") as f:
            self._sub_roles = json.load(f).get(member.id, [])

        with open("static/json/messages_id.json", encoding="utf-8") as f:
            messages_id = json.load(f)
            self._dm_choice_msg_id = messages_id["dm_choice"].get(str(member.id))

    def __getattr__(self, name):
        return getattr(self.member, name)

    async def update_main_role(self, new_role_name):
        """
        async function
        """
        new_role = discord.utils.get(self.member.guild.roles, name=new_role_name)
        sql = f"UPDATE members SET main_role='{new_role_name}' WHERE member_id={self.member.id}"
        database.execute(sql)

        await self.member.remove_roles(self.main_role, reason="Changing the main role")
        self.main_role = new_role
        await self.member.add_roles(self.main_role, reason="Update the main role")
        return self.main_role

    async def add_sub_roles(self):

        with open("static/json/members_sub_roles.json", "r+") as f:
            member_sub_roles = json.load(f).get(str(self.member.id), [])
            for id in member_sub_roles:
                if self.main_role.name == "Prof":
                    categorie = discord.utils.get(self.member.guild.categories, id=id)
                    await categorie.set_permissions(self.member, read_messages=True)
                else:
                    role = discord.utils.get(self.member.guild.roles, name=id)
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
        database.execute(sql)
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
        database.execute(sql)
        self._level = value

    @property
    def sub_roles(self):
        return self._sub_roles

    @sub_roles.setter
    def sub_roles(self, *roles):
        for role in roles:
            self._sub_roles.append(role)

        with open("static/json/members_sub_roles.json") as f:
            sub_roles = json.load(f)
            sub_roles[self.member.id] = self._sub_roles
        with open("static/json/members_sub_roles.json", "w") as f:
            json.dump(sub_roles, f)

    @property
    def dm_choice_msg_id(self):
        return self._dm_choice_msg_id

    @dm_choice_msg_id.setter
    def dm_choice_msg_id(self, id):
        """
        Update message_id in json file and update variable's value
        """
        with open("static/json/messages_id.json") as f:
            messages_id = json.load(f)
            messages_id["dm_choice"][self.member.id] = id
        with open("static/json/messages_id.json", "w") as f:
            json.dump(messages_id, f)

        self._dm_choice_msg_id = id

    @property
    def validate_state(self):
        return self._validate_state

    @validate_state.setter
    def validate_state(self, state):
        sql = f"UPDATE members SET validate_state={state} WHERE member_id={self.member.id}"
        database.execute(sql)
        self._validate_state = state

    def get_blacklist_date(self):
        sql = f"SELECT blacklist FROM members WHERE member_id={self.member.id}"
        end_date = database.execute(sql, fetchone=True)[0]
        if end_date and end_date > datetime.now():
            return end_date

    def place_in_blacklist(self, *, days=1, minutes=0):
        end_date = datetime.now() + timedelta(days=days, minutes=minutes)
        sql = f"UPDATE members SET blacklist='{end_date}' WHERE member_id={self.member.id}"
        database.execute(sql)
        Timer((end_date - datetime.now()).seconds, self._remove_from_blacklist).start()

    def _remove_from_blacklist(self):
        sql = f"UPDATE members SET blacklist=Null WHERE member_id={self.member.id}"
        database.execute(sql)


def get_mod_member(bot, member, guild_name="Terminales G"):
    """
    Get ModMember type with a associate discord member id
    """
    member_id = member.id if isinstance(member, discord.Member) else member
    guild = discord.utils.get(bot.guilds, name=guild_name)
    member = discord.utils.get(guild.members, id=member_id)

    sql = f"SELECT * FROM members WHERE member_id={member_id}"
    mod_member = database.execute(sql, dictionary=True, fetchone=True)
    if mod_member:
        return _ModMember(member, **mod_member)
