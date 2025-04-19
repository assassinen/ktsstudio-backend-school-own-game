import sqlalchemy as sa
from uuid import UUID
from datetime import datetime

from app.game.statuses import GameStatus
from app.store.database.sqlalchemy_base import db
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


# class Game(db):
#     __tablename__ = "game"
#
#     uuid = Column(String, primary_key=True)
#     chat_id = Column(BIGINT, nullable=False)
#     status = Column(Enum(GameStatus), nullable=False)
#     create_date = Column(DateTime, nullable=False)
#     update_date = Column(DateTime, nullable=False)
#

class Game(db):
    __tablename__ = "game"

    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(sa.BigInteger)
    status: Mapped[GameStatus]
    create_date: Mapped[datetime]
    update_date: Mapped[datetime]
