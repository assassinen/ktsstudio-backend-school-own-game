import uuid
from datetime import datetime

from sqlalchemy import select

from app.base.base_accessor import BaseAccessor
from app.game.models import Game
from app.game.statuses import GameStatus


class GameAccessor(BaseAccessor):
    async def create_game(self, chat_id):
        async with self.app.database.session() as session:
            game = Game(
                uuid=str(uuid.uuid4()),
                chat_id=chat_id,
                status=GameStatus.wait_game,
                create_date=datetime.now(),
                update_date=datetime.now(),
            )
            session.add(game)
            await session.commit()

    async def get_last_game_by_chat_id(self, _update) -> Game:
        async with self.app.database.session() as session:
            query = select(Game).filter(Game.chat_id == _update.object.chat_id).order_by(Game.create_date)
            return await session.scalar(query)

    async def get_game_by_chat_id(self, chat_id: int) -> Game:
        async with self.app.database.session() as session:
            query = select(Game)
            return await session.scalar(query)
