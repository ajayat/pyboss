from sqlalchemy import BigInteger, Column, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Member(Base):
    __tablename__ = "members"

    id: int = Column(BigInteger, primary_key=True)
    name: str = Column(String(50), unique=True)
    top_role: str = Column(String(50), nullable=True)
    sub_roles: str = Column(Text, nullable=True)
    level: int = Column(Integer, default=0)
    XP: int = Column(Integer, default=0)
    blacklist = Column(DateTime, nullable=True)
    choice_msg_id: int = Column(BigInteger, nullable=True)

    def __repr__(self):
        return f"Member(id={self.id}, name={self.name}, role={self.top_role})"


class Agenda(Base):
    __tablename__ = "agenda"

    id: int = Column(BigInteger, primary_key=True)
    class_name: str = Column(String(30))
    subject: str = Column(String(50))
    date = Column(Date)
    description: str = Column(Text, nullable=True)

    def __repr__(self):
        return "Agenda(class={} subject={}, date={:%d/%m}".format(
            self.class_name, self.subject, self.date
        )


class Planning(Base):
    __tablename__ = "planning"

    id: int = Column(BigInteger, primary_key=True)
    class_name: str = Column(String(30))
    subject: str = Column(String(50))
    date = Column(Date)
    starthour: int = Column(Integer)
    endhour: int = Column(Integer)
    description: str = Column(Text, nullable=True)

    def __repr__(self):
        return "Planning(class={} subject={}, date={:%d/%m}".format(
            self.class_name, self.subject, self.date
        )


class Message(Base):
    __tablename__ = "messages"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)
    author_id: int = Column(BigInteger)  # foreign_key=Member.id
    channel: str = Column(String(50))
    date = Column(DateTime)
    content: str = Column(Text, nullable=True)

    def __repr__(self):
        return "Message(author_id={}, channel={}, date={}, content={:30.30}".format(
            self.author_id, self.channel, self.date, self.content
        )


class Question(Base):
    __tablename__ = "quiz"

    id: int = Column(BigInteger, primary_key=True)
    author: str = Column(String(50), default="Anonyme")
    theme: str = Column(String(80), nullable=True)
    question: str = Column(Text, unique=True)
    propositions: str = Column(Text)
    answer: str = Column(String(1))

    def __repr__(self):
        return "Question(author={}, theme={}, question={:50.50}".format(
            self.author, self.theme, self.question
        )


class Special(Base):
    __tablename__ = "specials"

    message_id: int = Column(BigInteger, primary_key=True)
    name: str = Column(String(50), unique=True)
    date = Column(DateTime, nullable=True)

    def __repr__(self):
        return "Special(message_id={}, name={}, date={:%d/%m}".format(
            self.message_id, self.name, self.date
        )


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)
    author: str = Column(String(50))
    date = Column(DateTime, nullable=True)
    description: str = Column(Text)

    def __repr__(self):
        return f"Special(author={self.author}, description={self.description:30.30}"
