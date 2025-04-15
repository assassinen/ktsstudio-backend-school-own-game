from aiohttp.web import (
    Application as AiohttpApplication,
)

from app.store.store import setup_store

from .routes import setup_routes

__all__ = ("Application",)


class Application(AiohttpApplication):
    config = None
    store = None
    database = None


app = Application()


def setup_app(config_path: str) -> Application:
    setup_routes(app)
    setup_store(app)
    return app
