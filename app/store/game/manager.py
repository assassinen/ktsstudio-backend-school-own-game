import typing
from datetime import datetime, timedelta
from tabnanny import check
from telebot import types

import random

from sqlalchemy.sql.functions import current_user

from app.game.statuses import GameStatus
from app.store.telegram_api.dataclasses import Message

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.game_handlers = {
            # GameStatus.wait_game: self._mock,
            GameStatus.wait_player: self.game_handler_wait_player,
            # GameStatus.select_player: self._mock,
            GameStatus.select_theme: self.game_handler_select_theme,
            GameStatus.ask_question: self._mock,
            GameStatus.check_question: self._mock,
            GameStatus.end_game: self.game_handler_end_game,
        }

        self.time_handlers = {
            GameStatus.wait_player: self.check_wait_player,
            # GameStatus.select_theme: self.check_select_theme,
            GameStatus.select_theme: self._mock,
        }


    async def handle_time_event(self):
        active_games = await self.app.store.game_accessor.get_active_games()
        for game in active_games:
            await self.time_handlers[game.status](game)


    async def check_select_theme(self, game):
        if datetime.now() - game.update_date > timedelta(seconds=self.app.config.game_settings.time_select_theme):
            thema_by_game = await self.app.store.game_accessor.get_thema_by_game_uuid_and_round(game.uuid, game.round)
            selected_theme = [theme for theme in thema_by_game if theme.is_selected]
            thema_by_game = await self.app.store.game_accessor.get_thema_by_game_uuid_and_round(game.uuid, game.round)
            iteration = max([i.iteration for i in thema_by_game] + [0])

            if len(selected_theme) > 0:
                await self.app.store.game_accessor.update_game(game.uuid, {'status': GameStatus.ask_question})
            elif iteration >= self.app.config.game_settings.number_questions:
                await self.app.store.game_accessor.update_game(game.uuid, {'status': GameStatus.end_game})
                message = Message(chat_id=game.chat_id,
                                  text="Доступное количество попыток выбора темы закончилось. "
                                       "Игра отменена. Для продолжения создайте новую игру.",
                                  inline_data=[{'text': 'Создать игру', 'callback_data': '/create_game'}])
                await self.app.store.telegramm_api.send_message(message)
            else:
                users_from_game = [i.user_uuid for i in
                                   await self.app.store.game_accessor.get_users_from_game(game.uuid)]
                await self.select_theme(game, users_from_game)


    async def check_wait_player(self, game):
        users_from_game = [i.user_uuid for i in await self.app.store.game_accessor.get_users_from_game(game.uuid)]
        if datetime.now() - game.update_date > timedelta(seconds=self.app.config.game_settings.time_create_game):
            if len(users_from_game) < self.app.config.game_settings.min_player_counter:
                await self.app.store.game_accessor.update_game(game.uuid, {'status': GameStatus.end_game})
                message = Message(chat_id=game.chat_id,
                                  text="Не удалось набрать минимальное количество игроков для игры. "
                                       "Игра отменена. Для продолжения создайте новую игру.",
                                  inline_data=[{'text': 'Создать игру', 'callback_data': '/create_game'}])
                await self.app.store.telegramm_api.send_message(message)
            else:
                await self.select_theme(game, users_from_game)


    async def select_theme(self, game, users=None):
        if users is None:
            users = [i.user_uuid for i in await self.app.store.game_accessor.get_users_from_game(game.uuid)]
        user_uuid = random.choice(users)
        user = await self.app.store.game_accessor.get_user_by_uuid(user_uuid)

        kwargs = {'status': GameStatus.select_theme,
                  'active_user': user.uuid}
        await self.app.store.game_accessor.update_game(game.uuid, kwargs)
        themes = {theme.uuid: theme.title for theme in await self.app.store.game_accessor.get_themes()}

        thema_by_game = await self.app.store.game_accessor.get_thema_by_game_uuid_and_round(game.uuid, game.round)
        iteration = max([i.iteration for i in thema_by_game] + [0])

        theme_to_game = {'game_uuid': game.uuid, 'round': game.round, 'iteration': iteration + 1}
        for theme_uuid in random.sample(list(themes.keys()), 3):
            theme_to_game.update(theme_uuid = theme_uuid)
            await self.app.store.game_accessor.insert_theme_to_game(**theme_to_game)

        thema_by_game = await self.app.store.game_accessor.get_thema_by_game_uuid_and_round(game.uuid, game.round)

        inline_data = [{'text': themes[t.theme_uuid], 'callback_data': str(t.theme_uuid)} for t in thema_by_game]
        message = Message(chat_id=game.chat_id,
                          text=f'Пользователю {user.username} необходимо выбрать тему:',
                          inline_data=inline_data)
        await self.app.store.telegramm_api.send_message(message)


    #events
    async def handle_updates(self, updates):
        for update in updates:
            last_game = await self.app.store.game_accessor.get_last_game_by_chat_id(update.object.chat_id)
            game_status = GameStatus.end_game if last_game is None else last_game.status
            message = await self.game_handlers[game_status](update)
            await self.app.store.telegramm_api.send_message(message)


    async def game_handler_end_game(self, update):
        if update.type == 'callback_query' and update.object.data == '/create_game':
            await self.app.store.game_accessor.create_game(update)
            message = Message(chat_id=update.object.chat_id,
                              text='Создана новая игра. Присоединитесь для участия.',
                              inline_data=[{'text': 'Присоединиться к игре', 'callback_data': '/join_game'}])
        else:
            message = Message(chat_id=update.object.chat_id,
                              text='Игра не создана. Создайте новую игру.',
                              inline_data=[{'text': 'Создать игру', 'callback_data': '/create_game'}])
        return message


    async def game_handler_wait_player(self, update):
        if update.type == 'callback_query' and update.object.data == '/join_game':
            user = await self.app.store.game_accessor.get_or_create_user(update)
            game = await self.app.store.game_accessor.get_last_game_by_chat_id(update.object.chat_id)
            users_from_game = [i.user_uuid for i in await self.app.store.game_accessor.get_users_from_game(game.uuid)]

            if user.uuid in users_from_game:
                message = Message(chat_id=update.object.chat_id,
                                  text=f"Пользователь {user.username} уже в игре.",
                                  inline_data=[{'text': 'Присоединиться к игре', 'callback_data': '/join_game'}])
            else:
                await self.app.store.game_accessor.join_user_to_game(game.uuid, user.uuid)
                message = Message(chat_id=update.object.chat_id,
                                  text=f"Пользователь {user.username} добавлен в игру",
                                  inline_data=[{'text': 'Присоединиться к игре', 'callback_data': '/join_game'}])
        else:
            message = Message(chat_id=update.object.chat_id,
                              text='Игра создана. Присоединитесь для участия.',
                              inline_data=[{'text': 'Присоединиться к игре', 'callback_data': '/join_game'}])
        return message


    async def game_handler_select_theme(self, update):
        last_game = await self.app.store.game_accessor.get_last_game_by_chat_id(update.object.chat_id)
        active_user = await self.app.store.game_accessor.get_user_by_uuid(last_game.active_user)
        current_user = await self.app.store.game_accessor.get_or_create_user(update)

        if update.object.text.endswith('необходимо выбрать тему:') and current_user.uuid == last_game.active_user:
                message = Message(chat_id=update.object.chat_id,
                                  text=f"Ща как выбиру тему")
        else:
            themes = {theme.uuid: theme.title for theme in await self.app.store.game_accessor.get_themes()}
            thema_by_game = await self.app.store.game_accessor.get_thema_by_game_uuid_and_round(last_game.uuid,
                                                                                                last_game.round)
            inline_data = [{'text': themes[t.theme_uuid], 'callback_data': str(t.theme_uuid)} for t in thema_by_game]
            message = Message(chat_id=update.object.chat_id,
                              text=f'Пользователю {active_user.username} необходимо выбрать тему:',
                              inline_data=inline_data)
        return message


    async def _mock(self, update):
        return Message(chat_id=update.object.chat_id, text="Не найдена команда")
