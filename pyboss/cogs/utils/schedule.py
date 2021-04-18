import datetime
import json
import logging
import re

from pyboss import STATIC_DIR
from pyboss.controllers.member import MemberController

REGEX_HOUR = re.compile(
    r"^(?P<start>[0-1]?[0-9]|2[0-4])[hH]?[-àa; /:]*(?P<end>[0-1]?[0-9]|2[0-4])?[hH]?$"
)
REGEX_DATE = re.compile(r"^(?P<day>\d{1,2})[-\s/:]*(?P<month>\d{1,2})$")


def check_source(func):
    def evaluate(self, msg):
        if msg.channel == self.channel and msg.author.id == self.author.id:
            return func(self, msg)
        return None

    return evaluate


@check_source
def check_matter(schedule, msg):
    """
    Check if the user write a correct matter and place him in blacklist if not.
    """
    content = msg.content.upper()
    mod_member = MemberController(msg.author)

    with open(STATIC_DIR / "json/matters.json", encoding="utf-8") as wordlist:
        matters_wordlist = json.load(wordlist)
    if matters_wordlist.get(content):
        schedule.answers["matter"] = matters_wordlist[content]

    elif not mod_member.blacklist_date:
        mod_member.place_in_blacklist()
        schedule.answers["matter"] = content.title()
    else:
        timedelta = mod_member.blacklist_date - datetime.datetime.now()
        hours, minutes = (
            timedelta.total_seconds() // 3600,
            (timedelta.total_seconds() % 3600) // 60,
        )
        schedule.custom_response = (
            f"Vous n'êtes pas autorisé à ajouter un évènement spécial "
            f"pendant encore {int(hours)}h {int(minutes)}min. "
        )
        return False
    return True


@check_source
def check_date(schedule, msg):
    """
    Check with a regex the data as user input, can accept several formats
    """
    match = REGEX_DATE.match(msg.content)
    if not match:
        schedule.custom_response = "Votre format de date est invalide."
        logging.info(f"The user {msg.author.name} hasn't wrote correctly the date")
        return False

    day, month = map(int, match.groups())
    try:
        today = datetime.date.today()
        year = today.year if today.month > month else today.year + 1
        date_user = datetime.date(year=year, month=month, day=day)
    except ValueError:
        schedule.custom_response = "Vous avez mis des valeurs invalides"
        return False

    if date_user.weekday() < 5:
        if date_user >= datetime.date.today():
            schedule.answers["date"] = str(date_user)
            return True
        schedule.custom_response = (
            f"{day}/{month} est antérieur à la date d'aujourd'hui"
        )
        return False
    schedule.custom_response = "On ne travaille pas le week end! \
                            Votre jour doit faire parti de la semaine."
    return False


@check_source
def check_hours(schedule, msg):
    try:
        match = REGEX_HOUR.match(msg.content)
        starthour, endhour = map(int, match.groups())
    except (KeyError, ValueError):
        schedule.custom_response = "Votre format de plage horaire est invalide."
    else:
        # verifying if endhour exists or calculate it
        if not endhour:
            endhour = str(starthour + 1)
        schedule.answers["starthour"] = starthour + "h"
        schedule.answers["endhour"] = endhour + "h"
        return True


@check_source
def check_description(schedule, msg):
    if msg.content.strip().upper() != "NON":
        schedule.answers["description"] = msg.content
    return True
