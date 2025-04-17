from sqlalchemy import BIGINT, Column, DateTime, Enum, String

from app.game.statuses import GameStatus
from app.store.database.sqlalchemy_base import db


class Game(db):
    __tablename__ = "game"

    uuid = Column(String, primary_key=True)
    chat_id = Column(BIGINT, nullable=False)
    status = Column(Enum(GameStatus), nullable=False)
    create_date = Column(DateTime, nullable=False)
    update_date = Column(DateTime, nullable=False)
