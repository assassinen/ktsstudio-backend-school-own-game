import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.bot.manager import BotManager
        from app.store.telegram_api.accessor import TelegramApiAccessor
        from app.users.accessor import UserAccessor

        self.user = UserAccessor(app)
        self.bots_manager = BotManager(app)
        self.telegramm_api = TelegramApiAccessor(app)


def setup_store(app: "Application") -> None:
    app.store = Store(app)
