import typing

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.telegram_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application


class TelegramApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: ClientSession | None = None
        self.URL = "https://api.telegram.org/bot"
        self.TOKEN = "тут стоит токен, который будет перенесен в config"
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
        if self.session:
            await self.session.close()
        if self.poller:
            await self.poller.stop()

    async def _get_long_poll_service(self):
        async with self.session.get(f"{self.URL}{self.TOKEN}/getUpdates") as resp:
            data = await resp.json()
            update_ids = [update.get("update_id") for update in data.get("result", {})]
            self.offset = max(update_ids) + 1 if len(update_ids) > 0 else 0

    async def poll(self):
        async with self.session.get(f"{self.URL}{self.TOKEN}/getUpdates?offset={self.offset}") as resp:
            data = await resp.json()
            raw_updates = data.get("result", [])
            update_ids = [update.get("update_id") for update in raw_updates]
            self.offset = max(update_ids) + 1 if len(update_ids) > 0 else 0
            await self.app.store.bots_manager.handle_updates(raw_updates)

    async def send_message(self, message):
        await self.session.post(f"{self.URL}{self.TOKEN}/sendMessage", data=message)
