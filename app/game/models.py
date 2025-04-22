from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.game.statuses import GameStatus
from app.store.database.sqlalchemy_base import db


class Game(db):
    __tablename__ = "game"

    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(sa.BigInteger)
    status: Mapped[GameStatus]
    created_by: Mapped[int] = mapped_column(sa.BigInteger, nullable=True)
    create_date: Mapped[datetime]
    update_date: Mapped[datetime]
    active_user: Mapped[UUID] = mapped_column(ForeignKey("user.uuid"), nullable=True)
    round: Mapped[int] = mapped_column(nullable=True)


class User(db):
    __tablename__ = "user"

    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(sa.BigInteger)
    username: Mapped[str]
    score: Mapped[int]


class UserToGame(db):
    __tablename__ = "user_to_game"

    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    game_uuid: Mapped[Game] = mapped_column(ForeignKey("game.uuid"))
    user_uuid: Mapped[User] = mapped_column(ForeignKey("user.uuid"))
    score: Mapped[int] = mapped_column(nullable=True)


class Theme(db):
    __tablename__ = "theme"

    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str]


class ThemeToGame(db):
    __tablename__ = "theme_to_game"

    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    game_uuid: Mapped[Game] = mapped_column(ForeignKey("game.uuid"))
    theme_uuid: Mapped[User] = mapped_column(ForeignKey("theme.uuid"))
    create_date: Mapped[datetime]
    update_date: Mapped[datetime]
    is_selected: Mapped[bool]
    round: Mapped[int]
    iteration: Mapped[int]



class Question(db):
    __tablename__ = "question"

    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    theme_uuid: Mapped[Theme] = mapped_column(ForeignKey("theme.uuid"))


class Answer(db):
    __tablename__ = "answer"

    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    is_correct: Mapped[bool]
    question_uuid: Mapped[Theme] = mapped_column(ForeignKey("theme.uuid"))
