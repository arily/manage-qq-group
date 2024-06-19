from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    scoped_session,
    sessionmaker,
)

engine = create_engine("sqlite:///db.sqlite3", echo=True)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


class OpType(Enum):
    AddToWhiteList = "whitelist"
    Kick = "kick"


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(index=True)
    qq_id: Mapped[int] = mapped_column(index=True)
    sb_id: Mapped[Optional[int]] = mapped_column(index=True)
    comment: Mapped[str] = mapped_column(default="")
    whitelisted: Mapped[bool] = mapped_column(default=False)


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    qq_id: Mapped[int] = mapped_column(index=True)


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    time: Mapped[datetime]
    account_id: Mapped[Account] = relationship(Account.id)
    admin_id: Mapped[Account] = relationship(Account.id)
    op: Mapped[OpType]


Base.metadata.create_all(bind=engine)
