import asyncio
import typing
from asyncio import Task

if typing.TYPE_CHECKING:
    from app.store import Store


class Poller:
    def __init__(self, store: "Store"):
        self.store = store
        self.is_running = False
        self.poll_task: Task | None = None

    async def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())

    async def stop(self):
        if self.poll_task is not asyncio.current_task():
            self.is_running = False
            self.poll_task.cancel()

    async def poll(self):
        while self.is_running:
            await self.store.game_manager.handle_time_event()
            await self.store.telegramm_api.poll()
            # await asyncio.sleep(5)
