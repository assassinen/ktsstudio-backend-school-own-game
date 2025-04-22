import uuid
from datetime import datetime

from sqlalchemy import select, update, desc

from app.base.base_accessor import BaseAccessor
from app.game.models import Game, UserToGame, User, Theme, ThemeToGame
from app.game.statuses import GameStatus


class GameAccessor(BaseAccessor):
    async def create_game(self, update):
        async with self.app.database.session() as session:
            game = Game(
                uuid=uuid.uuid4(),
                chat_id=update.object.chat_id,
                status=GameStatus.wait_player,
                created_by=update.object.from_id,
                create_date=datetime.now(),
                update_date=datetime.now(),
                round=0,
            )
            session.add(game)
            await session.commit()

    async def get_last_game_by_chat_id(self, chat_id) -> Game:
        async with self.app.database.session() as session:
            query = select(Game).filter(Game.chat_id == chat_id).order_by(desc(Game.create_date))
            return await session.scalar(query)

    async def get_active_games(self):
        async with self.app.database.session() as session:
            query = select(Game).filter(Game.status != GameStatus.end_game)
            return await session.scalars(query)

    async def update_game(self, game_uuid, kwargs):
        kwargs.update(update_date=datetime.now())
        async with self.app.database.session() as session:
            await session.execute(
                update(Game)
                .where(Game.uuid == game_uuid)
                .values(kwargs)
            )
            await session.commit()

    async def get_user_by_uuid(self, uuid) -> User:
        async with self.app.database.session() as session:
            query = select(User).filter(User.uuid == uuid)
            return await session.scalar(query)

    async def get_or_create_user(self, update) -> User:
        async with self.app.database.session() as session:
            query = select(User).filter(User.user_id == update.object.from_id)
            user = await session.scalar(query)
            if user is None:
                user = User(
                    uuid=uuid.uuid4(),
                    user_id=update.object.from_id,
                    username=update.object.username,
                    score=10000,
                )
                session.add(user)
                await session.commit()
            return user

    async def get_users_from_game(self, game_uuid):
        async with self.app.database.session() as session:
            query = select(UserToGame).filter(UserToGame.game_uuid == game_uuid)
            return await session.scalars(query)

    async def join_user_to_game(self, game_uuid, user_uuid):
        async with self.app.database.session() as session:
            user_to_game = UserToGame(
                uuid=uuid.uuid4(),
                game_uuid=game_uuid,
                user_uuid=user_uuid,
                score=0,
            )
            session.add(user_to_game)
            await session.commit()

    async def get_themes(self):
        async with self.app.database.session() as session:
            query = select(Theme)
            return await session.scalars(query)

    async def insert_theme_to_game(self, game_uuid, theme_uuid, round, iteration):
        async with self.app.database.session() as session:
            theme_to_game = ThemeToGame(
                uuid=uuid.uuid4(),
                game_uuid=game_uuid,
                theme_uuid=theme_uuid,
                create_date=datetime.now(),
                update_date=datetime.now(),
                is_selected=False,
                round=round,
                iteration=iteration,
            )
            session.add(theme_to_game)
            await session.commit()

    async def get_thema_by_game_uuid_and_round(self, game_uuid, round, limit=3):
        async with self.app.database.session() as session:
            query = select(
                ThemeToGame).filter(
                ThemeToGame.game_uuid == game_uuid).filter(
                ThemeToGame.round == round).order_by(desc(ThemeToGame.iteration)).limit(limit)
            return await session.scalars(query)

    # async def insert_theme_to_game(self, kwargs):
    #     kwargs.update(uuid=uuid.uuid4(),
    #                   create_date=datetime.now(),
    #                   update_date=datetime.now())
    #     print(kwargs)
    #     async with self.app.database.session() as session:
    #         theme_to_game = ThemeToGame(kwargs)
    #         session.add(theme_to_game)
    #         await session.commit()