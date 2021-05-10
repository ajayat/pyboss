from sqlalchemy import BigInteger, Column, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class GuildModel(Base):
    __tablename__ = "guilds"

    id: int = Column(BigInteger, primary_key=True)
    name: str = Column(String(50), unique=True)

    def __repr__(self):
        return f"Guild(id={self.id}, name={self.name})"


class MemberModel(Base):
    __tablename__ = "members"

    id: int = Column(BigInteger, primary_key=True)
    guild_id: int = Column(BigInteger)
    name: str = Column(String(50), unique=True)
    top_role: str = Column(String(50), nullable=True)
    sub_roles: str = Column(Text, nullable=True)
    level: int = Column(Integer, default=1)
    XP: int = Column(Integer, default=0)
    blacklist = Column(DateTime, nullable=True)
    choice_msg_id: int = Column(BigInteger, nullable=True)

    def __repr__(self):
        return f"Member(id={self.id}, name={self.name}, role={self.top_role})"


class NotebookModel(Base):
    __tablename__ = "notebook"

    id: int = Column(BigInteger, primary_key=True)
    guild_id: int = Column(BigInteger)
    channel: str = Column(String(30))
    subject: str = Column(String(50))
    date = Column(Date)
    description: str = Column(Text, nullable=True)

    def __repr__(self):
        return "Agenda(class={} subject={}, date={:%d/%m}".format(
            self.class_name, self.subject, self.date
        )


class CalendarModel(Base):
    __tablename__ = "calendar"

    id: int = Column(BigInteger, primary_key=True)
    guild_id: int = Column(BigInteger)
    channel: str = Column(String(30))
    subject: str = Column(String(50))
    date = Column(Date)
    starthour: int = Column(Integer)
    endhour: int = Column(Integer)
    description: str = Column(Text, nullable=True)

    def __repr__(self):
        return "Planning(class={} subject={}, date={:%d/%m}".format(
            self.class_name, self.subject, self.date
        )


class MessageModel(Base):
    __tablename__ = "messages"

    id: int = Column(BigInteger, primary_key=True)
    guild_id: int = Column(BigInteger)
    author_id: int = Column(BigInteger)  # foreign_key=Member.id
    channel: str = Column(String(50))
    date = Column(DateTime)
    content: str = Column(Text, nullable=True)

    def __repr__(self):
        return "Message(author_id={}, channel={}, date={}, content={:30.30}".format(
            self.author_id, self.channel, self.date, self.content
        )


class QuestionModel(Base):
    __tablename__ = "questions"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)
    guild_id: int = Column(BigInteger)
    author: str = Column(String(50), default="Anonyme")
    theme: str = Column(String(80), nullable=True)
    title: str = Column(Text, unique=True)
    propositions: str = Column(Text)
    answer: str = Column(String(1))

    def __repr__(self):
        return "Question(author={}, theme={}, question={:50.50}".format(
            self.author, self.theme, self.question
        )


class ScheduleRefModel(Base):
    __tablename__ = "schedule_ref"

    message_id: int = Column(BigInteger, primary_key=True)
    guild_id: int = Column(BigInteger)
    channel_id: int = Column(BigInteger)

    def __repr__(self):
        return "ScheduleRefModel(message_id={}, guild_id={}, channel_id={}".format(
            self.message_id, self.guild_id, self.channel_id
        )


class SuggestionModel(Base):
    __tablename__ = "suggestions"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)
    author: str = Column(String(50))
    date = Column(DateTime, nullable=True)
    description: str = Column(Text)

    def __repr__(self):
        return f"Special(author={self.author}, description={self.description:30.30}"
