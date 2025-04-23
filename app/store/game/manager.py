import random
import typing
from datetime import datetime, timedelta

from app.game.statuses import GameStatus
from app.store.telegram_api.dataclasses import Message

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.game_handlers = {
            GameStatus.wait_player: self.game_handler_wait_player,
            GameStatus.select_theme: self.game_handler_select_theme,
            GameStatus.ask_question: self.game_handler_ask_question,
            GameStatus.check_question: self._mock,
            GameStatus.end_game: self.game_handler_end_game,
        }

        self.time_handlers = {
            GameStatus.wait_player: self.check_wait_player,
            GameStatus.select_theme: self.check_select_theme,
            GameStatus.ask_question: self.check_ask_question,
        }

    async def handle_time_event(self):
        active_games = await self.app.store.game_accessor.get_active_games()
        for game in active_games:
            await self.time_handlers[game.status](game)

    async def check_ask_question(self, game):
        if datetime.now() - game.update_date > timedelta(seconds=self.app.config.game_settings.time_give_answer):
            if game.round < self.app.config.game_settings.number_questions:
                kwargs = {"status": GameStatus.select_theme, "round": game.round + 1}
                await self.app.store.game_accessor.update_game(game.uuid, kwargs)
            else:
                kwargs = {"status": GameStatus.end_game, "round": game.round + 1}
                await self.app.store.game_accessor.update_game(game.uuid, kwargs)
                message = Message(
                    chat_id=game.chat_id,
                    text="Игра закончена.",
                    inline_data=[[{"text": "Создать игру", "callback_data": "/create_game"}]],
                )
                await self.app.store.telegramm_api.send_message(message)

    async def check_select_theme(self, game):
        if datetime.now() - game.update_date > timedelta(seconds=self.app.config.game_settings.time_select_theme):
            thema_by_game = await self.app.store.game_accessor.get_thema_by_game_uuid_and_round(game.uuid, game.round)
            selected_theme = [theme for theme in thema_by_game if theme.is_selected]
            thema_by_game = await self.app.store.game_accessor.get_thema_by_game_uuid_and_round(game.uuid, game.round)
            iteration = max([i.iteration for i in thema_by_game] + [0])

            if len(selected_theme) > 0:
                await self.app.store.game_accessor.update_game(game.uuid, {"status": GameStatus.ask_question})
            elif iteration >= self.app.config.game_settings.number_questions:
                await self.app.store.game_accessor.update_game(game.uuid, {"status": GameStatus.end_game})
                message = Message(
                    chat_id=game.chat_id,
                    text="Доступное количество попыток выбора темы закончилось. "
                    "Игра отменена. Для продолжения создайте новую игру.",
                    inline_data=[[{"text": "Создать игру", "callback_data": "/create_game"}]],
                )
                await self.app.store.telegramm_api.send_message(message)
            else:
                users_from_game = [
                    i.user_uuid for i in await self.app.store.game_accessor.get_users_from_game(game.uuid)
                ]
                await self.select_theme(game, users_from_game)

    async def check_wait_player(self, game):
        users_from_game = [i.user_uuid for i in await self.app.store.game_accessor.get_users_from_game(game.uuid)]
        if datetime.now() - game.update_date > timedelta(seconds=self.app.config.game_settings.time_create_game):
            if len(users_from_game) < self.app.config.game_settings.min_player_counter:
                await self.app.store.game_accessor.update_game(game.uuid, {"status": GameStatus.end_game})
                message = Message(
                    chat_id=game.chat_id,
                    text="Не удалось набрать минимальное количество игроков для игры. "
                    "Игра отменена. Для продолжения создайте новую игру.",
                    inline_data=[[{"text": "Создать игру", "callback_data": "/create_game"}]],
                )
                await self.app.store.telegramm_api.send_message(message)
            else:
                await self.select_theme(game, users_from_game)

    async def select_theme(self, game, users=None):
        if users is None:
            users = [i.user_uuid for i in await self.app.store.game_accessor.get_users_from_game(game.uuid)]
        user_uuid = random.choice(users)
        user = await self.app.store.game_accessor.get_user_by_uuid(user_uuid)

        kwargs = {"status": GameStatus.select_theme, "active_user": user.uuid}
        await self.app.store.game_accessor.update_game(game.uuid, kwargs)
        themes = {theme.uuid: theme.title for theme in await self.app.store.game_accessor.get_themes()}

        thema_by_game = await self.app.store.game_accessor.get_thema_by_game_uuid_and_round(game.uuid, game.round)
        iteration = max([i.iteration for i in thema_by_game] + [0])

        theme_to_game = {"game_uuid": game.uuid, "round": game.round, "iteration": iteration + 1}
        for theme_uuid in random.sample(list(themes.keys()), 3):
            theme_to_game.update(theme_uuid=theme_uuid)
            await self.app.store.game_accessor.insert_theme_to_game(**theme_to_game)

        thema_by_game = await self.app.store.game_accessor.get_thema_by_game_uuid_and_round(game.uuid, game.round)

        inline_data = [{"text": themes[t.theme_uuid], "callback_data": str(t.theme_uuid)} for t in thema_by_game]
        message = Message(
            chat_id=game.chat_id,
            text=f"Пользователю {user.username} необходимо выбрать тему - 123:",
            inline_data=[inline_data],
        )
        await self.app.store.telegramm_api.send_message(message)

    # events
    async def handle_updates(self, updates):
        for update in updates:
            last_game = await self.app.store.game_accessor.get_last_game_by_chat_id(update.object.chat_id)
            game_status = GameStatus.end_game if last_game is None else last_game.status
            message = await self.game_handlers[game_status](update)

            await self.app.store.telegramm_api.send_message(message)

    async def game_handler_end_game(self, update):
        if update.type == "callback_query" and update.object.data == "/create_game":
            await self.app.store.game_accessor.create_game(update)
            message = Message(
                chat_id=update.object.chat_id,
                text="Создана новая игра. Присоединитесь для участия.",
                inline_data=[[{"text": "Присоединиться к игре", "callback_data": "/join_game"}]],
            )
        else:
            message = Message(
                chat_id=update.object.chat_id,
                text="Игра не создана. Создайте новую игру.",
                inline_data=[[{"text": "Создать игру", "callback_data": "/create_game"}]],
            )
        return message

    async def game_handler_wait_player(self, update):
        if update.type == "callback_query" and update.object.data == "/join_game":
            user = await self.app.store.game_accessor.get_or_create_user(update)
            game = await self.app.store.game_accessor.get_last_game_by_chat_id(update.object.chat_id)
            users_from_game = [i.user_uuid for i in await self.app.store.game_accessor.get_users_from_game(game.uuid)]

            if user.uuid in users_from_game:
                message = Message(
                    chat_id=update.object.chat_id,
                    text=f"Пользователь {user.username} уже в игре.",
                    inline_data=[[{"text": "Присоединиться к игре", "callback_data": "/join_game"}]],
                )
            else:
                await self.app.store.game_accessor.join_user_to_game(game.uuid, user.uuid)
                message = Message(
                    chat_id=update.object.chat_id,
                    text=f"Пользователь {user.username} добавлен в игру",
                    inline_data=[[{"text": "Присоединиться к игре", "callback_data": "/join_game"}]],
                )
        else:
            message = Message(
                chat_id=update.object.chat_id,
                text="Игра создана. Присоединитесь для участия.",
                inline_data=[[{"text": "Присоединиться к игре", "callback_data": "/join_game"}]],
            )
        return message

    async def game_handler_select_theme(self, update):
        last_game = await self.app.store.game_accessor.get_last_game_by_chat_id(update.object.chat_id)
        active_user = await self.app.store.game_accessor.get_user_by_uuid(last_game.active_user)
        current_user = await self.app.store.game_accessor.get_or_create_user(update)

        if "выбрать тему" in update.object.text and current_user.uuid == last_game.active_user:
            await self.app.store.game_accessor.update_game(
                last_game.uuid, {"status": GameStatus.ask_question, "round": last_game.round + 1}
            )
            thema_by_game = await self.app.store.game_accessor.get_thema_by_game_uuid_and_round(
                last_game.uuid, last_game.round
            )
            iteration = max([i.iteration for i in thema_by_game] + [0])
            kwargs = {"is_selected": True}
            await self.app.store.game_accessor.update_theme_to_game(last_game.uuid, iteration, kwargs)

            question = random.choice(
                [
                    (theme.title, theme.uuid)
                    for theme in await self.app.store.game_accessor.get_questions_by_theme_uuid(update.object.data)
                ]
            )

            await self.app.store.game_accessor.insert_question_to_game(
                game_uuid=last_game.uuid, question_uuid=question[1], round=last_game.round + 1
            )

            answers = await self.app.store.game_accessor.get_answers_by_question_uuid(question[1])
            inline_data = [[{"text": f"{answer.title}", "callback_data": str(answer.uuid)}] for answer in answers]
            message = Message(chat_id=last_game.chat_id, text=question[0], inline_data=[inline_data])
        else:
            themes = {theme.uuid: theme.title for theme in await self.app.store.game_accessor.get_themes()}

            thema_by_game = await self.app.store.game_accessor.get_thema_by_game_uuid_and_round(
                last_game.uuid, last_game.round
            )
            inline_data = [{"text": themes[t.theme_uuid], "callback_data": str(t.theme_uuid)} for t in thema_by_game]
            message = Message(
                chat_id=update.object.chat_id,
                text=f"Только пользователь {active_user.username} может выбрать тему - 321:",
                inline_data=[inline_data],
            )
        return message

    async def game_handler_ask_question(self, update):
        last_game = await self.app.store.game_accessor.get_last_game_by_chat_id(update.object.chat_id)
        user = await self.app.store.game_accessor.get_or_create_user(update)

        question_by_game = await self.app.store.game_accessor.get_question_by_game_uuid_and_round(
            last_game.uuid, last_game.round
        )
        question = await self.app.store.game_accessor.get_question_by_uuid(question_by_game.question_uuid)

        answers = await self.app.store.game_accessor.get_answers_by_question_uuid(question_by_game.question_uuid)
        inline_data = [[{"text": f"{answer.title}", "callback_data": str(answer.uuid)}] for answer in answers]

        if (
            update.type == "callback_query"
            and not update.object.text.endswith("необходимо выбрать тему:")
            and "/" not in update.object.text
        ):
            answer_to_game = await self.app.store.game_accessor.get_answer_to_game(
                last_game.uuid, update.object.data, user.uuid, last_game.round
            )
            if answer_to_game is None:
                await self.app.store.game_accessor.insert_answer_to_game(
                    last_game.uuid, update.object.data, user.uuid, last_game.round
                )

                message = Message(
                    chat_id=update.object.chat_id,
                    text=f"Ответ пользователя {user.username} записан \n{question.title}",
                    inline_data=inline_data,
                )
            else:
                message = Message(
                    chat_id=update.object.chat_id,
                    text=f"Пользователь {user.username} уже отвечал нa этот вопрос \n{question.title}",
                    inline_data=inline_data,
                )
        else:
            message = Message(chat_id=update.object.chat_id, text=f"{question.title}", inline_data=inline_data)
        return message

    async def _mock(self, update):
        return Message(chat_id=update.object.chat_id, text="Не найдена команда")

    async def _time_mock(self, game):
        return Message(chat_id=game.chat_id, text="Не найдена команда")
