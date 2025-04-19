from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.game.statuses import GameStatus
from app.store.database.sqlalchemy_base import db


class Game(db):
    __tablename__ = "game"

    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(sa.BigInteger)
    status: Mapped[GameStatus]
    create_date: Mapped[datetime]
    update_date: Mapped[datetime]
