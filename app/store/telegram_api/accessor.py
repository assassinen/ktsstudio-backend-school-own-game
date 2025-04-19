import typing

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.telegram_api.dataclasses import Message, UpdateMessage, UpdateObject
from app.store.telegram_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application


class TelegramApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: ClientSession | None = None
        self.base_url = f"{app.config.bot.url}{app.config.bot.token}"
        self.offset = 0
        self.poller: Poller | None = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        try:
            await self._get_long_poll_service()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)
        self.poller = Poller(app.store)
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.poller:
            await self.poller.stop()
        if self.session:
            await self.session.close()

    async def _set_offset(self, resp):
        updates = []
        data = await resp.json()
        for update in data.get("result", []):
            self.offset = update["update_id"] + 1
            if "message" in update:
                updates.append(
                    UpdateObject(
                        id=update["update_id"],
                        type="message",
                        object=UpdateMessage(
                            id=update["message"]["message_id"],
                            from_id=update["message"]["from"]["id"],
                            chat_id=update["message"]["chat"]["id"],
                            username=update["message"]["from"]["username"],
                            text=update["message"]["text"],
                        ),
                    )
                )
        return updates

    async def _get_long_poll_service(self):
        async with self.session.get(f"{self.base_url}/getUpdates") as resp:
            # TODO добавиить обработку сообщение в простое
            await self._set_offset(resp)

    async def poll(self):
        async with self.session.get(f"{self.base_url}/getUpdates?offset={self.offset}") as resp:
            raw_updates = await self._set_offset(resp)
            await self.app.store.bots_manager.handle_updates(raw_updates)

    async def send_message(self, message: Message):
        data = {"chat_id": message.chat_id, "text": message.text}
        await self.session.post(f"{self.base_url}/sendMessage", data=data)
