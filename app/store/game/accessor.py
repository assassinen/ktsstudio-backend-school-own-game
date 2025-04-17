from datetime import datetime
import typing
import uuid

from app.game.statuses import GameStatus
from sqlalchemy import desc, func, select, update
from sqlalchemy.dialects.postgresql import insert
from app.store.telegram_api.dataclasses import UpdateObject, UpdateMessage

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.game.models import Game
from app.store.telegram_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameAccessor(BaseAccessor):

    async def create_game(self, chat_id):
        # game_data = {
        #     "uuid": str(uuid.uuid4()),
        #     "chat_id": chat_id,
        #     "status": GameStatus.wait_game,
        #     "create_date": datetime.now(),
        #     "update_date": datetime.now(),
        # }
        #
        # stmt = insert(Game).values(game_data)
        #
        # async with self.app.database.session() as session:
        #     await session.execute(stmt)
        #     await session.commit()
        async with self.app.database.session() as session:
            game = Game(uuid=str(uuid.uuid4()),
                        chat_id=chat_id,
                        status=GameStatus.wait_game,
                        create_date=datetime.now(),
                        update_date=datetime.now()
                    )
            session.add(game)
            await session.commit()

    async def get_last_game_by_chat_id(self, update: UpdateObject) -> Game:
        async with self.app.database.session() as session:
            query = select(Game).filter(Game.chat_id == update.object.chat_id).order_by(Game.create_date)
            return await session.scalar(query)

    async def get_game_by_chat_id(self, chat_id: int) -> Game:
        async with self.app.database.session() as session:
            query = select(Game)
            # # result = await session.execute(query)
            # # print(result)
            # result = await session.execute(query)
            # question = result.scalar_one_or_none()
            # print(123, question.uuid, question.status, 321)

            return await session.scalar(query)