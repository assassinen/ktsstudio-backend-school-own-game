from typing import TYPE_CHECKING, Any

from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.store.database.sqlalchemy_base import db

if TYPE_CHECKING:
    from app.web.app import Application


class Database:
    def __init__(self, app: "Application") -> None:
        self.app = app

        self.engine: AsyncEngine | None = None
        self._db: type[DeclarativeBase] = db
        self.session: async_sessionmaker[AsyncSession] | None = None

    async def connect(self, *args: Any, **kwargs: Any) -> None:
        database_url = URL.create(
            drivername=self.app.config.database.drivername,
            host=self.app.config.database.host,
            database=self.app.config.database.database,
            username=self.app.config.database.username,
            password=self.app.config.database.password,
            port=self.app.config.database.port,
        )
        engine = create_async_engine(database_url, echo=True)
        self.session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def disconnect(self, *args: Any, **kwargs: Any) -> None:
        self.logger.info("Отключаем БД")
        await self.engine.dispose()
