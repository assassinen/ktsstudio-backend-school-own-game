import typing

from app.game.statuses import GameStatus
from app.store.telegram_api.dataclasses import Message

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.game_status = {
            GameStatus.wait_game: self._mock,
            GameStatus.wait_player: self._mock,
            GameStatus.select_player: self._mock,
            GameStatus.select_theme: self._mock,
            GameStatus.ask_question: self._mock,
            GameStatus.check_question: self._mock,
            GameStatus.end_game: self._create_new_game,
        }

    async def handle_updates(self, updates):
        for update in updates:
            last_game = await self.app.store.game_accessor.get_last_game_by_chat_id(update)
            game_status = GameStatus.end_game if last_game is None else last_game.status
            message = await self.game_status[game_status](update)
            await self.app.store.telegramm_api.send_message(message)

    async def _create_new_game(self, update):
        if update.object.text == "/create_game":
            await self.app.store.game_accessor.create_game(update.object.chat_id)
            message = Message(chat_id=update.object.chat_id, text="Создали новую игру")
        else:
            message = Message(chat_id=update.object.chat_id, text="Недопустимая команды для текущего статуса")
        return message

    async def _mock(self, update):
        return Message(chat_id=update.object.chat_id, text="Не найдена команда")
