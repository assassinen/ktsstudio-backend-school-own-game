from uuid import UUID

from sqlalchemy import Column, Integer, BIGINT, DateTime, String, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.store.database.sqlalchemy_base import db
from app.game.statuses import GameStatus


def generate_uuid():
    return str(UUID.uuid4())


class Game(db):
    __tablename__ = 'game'

    uuid = Column(String, name="uuid", primary_key=True, default=generate_uuid)
    chat_id = Column(BIGINT, nullable=False)
    status = Column(Enum(GameStatus), nullable=False)
    create_date = Column(DateTime, nullable=False)
    update_date = Column(DateTime, nullable=False)
