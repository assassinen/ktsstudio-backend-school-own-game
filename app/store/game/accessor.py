import uuid
from datetime import datetime

from sqlalchemy import desc, select, update

from app.base.base_accessor import BaseAccessor
from app.game.models import Answer, AnswerToGame, Game, Question, QuestionToGame, Theme, ThemeToGame, User, UserToGame
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
            await session.execute(update(Game).where(Game.uuid == game_uuid).values(kwargs))
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
            query = (
                select(ThemeToGame)
                .filter(ThemeToGame.game_uuid == game_uuid)
                .filter(ThemeToGame.round == round)
                .order_by(desc(ThemeToGame.iteration))
                .limit(limit)
            )
            return await session.scalars(query)

    async def update_theme_to_game(self, game_uuid, iteration, kwargs):
        kwargs.update(update_date=datetime.now())
        async with self.app.database.session() as session:
            await session.execute(
                update(ThemeToGame)
                .where(ThemeToGame.game_uuid == game_uuid)
                .where(ThemeToGame.iteration == iteration)
                .values(kwargs)
            )
            await session.commit()

    async def get_questions_by_theme_uuid(self, theme_uuid):
        async with self.app.database.session() as session:
            query = select(Question).filter(Question.theme_uuid == theme_uuid)
            return await session.scalars(query)

    async def get_question_by_uuid(self, uuid):
        async with self.app.database.session() as session:
            query = select(Question).filter(Question.uuid == uuid)
            return await session.scalar(query)

    async def get_answers_by_question_uuid(self, question_uuid):
        async with self.app.database.session() as session:
            query = select(Answer).filter(Answer.question_uuid == question_uuid)
            return await session.scalars(query)

    async def insert_answer_to_game(self, game_uuid, answer_uuid, user_uuid, round):
        async with self.app.database.session() as session:
            theme_to_game = AnswerToGame(
                uuid=uuid.uuid4(),
                game_uuid=game_uuid,
                user_uuid=user_uuid,
                answer_uuid=answer_uuid,
                create_date=datetime.now(),
                update_date=datetime.now(),
                round=round,
            )
            session.add(theme_to_game)
            await session.commit()

    async def get_answer_to_game(self, game_uuid, answer_uuid, user_uuid, round):
        async with self.app.database.session() as session:
            query = (
                select(AnswerToGame)
                .filter(AnswerToGame.game_uuid == game_uuid)
                .filter(AnswerToGame.answer_uuid == answer_uuid)
                .filter(AnswerToGame.user_uuid == user_uuid)
                .filter(AnswerToGame.round == round)
            )
            return await session.scalar(query)

    async def insert_question_to_game(self, game_uuid, question_uuid, round):
        async with self.app.database.session() as session:
            question_to_game = QuestionToGame(
                uuid=uuid.uuid4(),
                game_uuid=game_uuid,
                question_uuid=question_uuid,
                round=round,
            )
            session.add(question_to_game)
            await session.commit()

    async def get_question_by_game_uuid_and_round(self, game_uuid, round):
        async with self.app.database.session() as session:
            query = (
                select(QuestionToGame)
                .filter(QuestionToGame.game_uuid == game_uuid)
                .filter(QuestionToGame.round == round)
            )
            return await session.scalar(query)
