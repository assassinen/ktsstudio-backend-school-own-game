import json
import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app

    async def handle_updates(self, updates):
        for update in updates:
            chat_id = update.get("message", {}).get("chat", {}).get("id")
            text = update.get("message", {}).get("text")
            message = {"chat_id": chat_id, "text": text}
            await self.app.store.telegramm_api.send_message(message)
