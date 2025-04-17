from select import select
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import text
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine

from app.store.database.sqlalchemy_base import BaseModel
from app.store.database.sqlalchemy_base import db

from app.store.database import Game


if TYPE_CHECKING:
    from app.web.app import Application


class Database:
    def __init__(self, app: "Application") -> None:
        self.app = app

        self.engine: AsyncEngine | None = None
        self._db: type[DeclarativeBase] = db
        self.session: async_sessionmaker[AsyncSession] | None = None

    async def connect(self, *args: Any, **kwargs: Any) -> None:
        print("Connecting to database...")
        database_url = URL.create(
                drivername=self.app.config.database.drivername,
                host=self.app.config.database.host,
                database=self.app.config.database.database,
                username=self.app.config.database.username,
                password=self.app.config.database.password,
                port=self.app.config.database.port,
            )
        engine = create_async_engine(database_url, echo=True)

        # async with engine.connect() as conn:
        #     result = await conn.execute(text("""select * from game"""))
        #     print(result.all())

        self.session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        #
        # async with self.session() as session:
        #     # async with session.begin():
        #
        #     result = await session.execute(select(Game))
        #     print(result)



    async def disconnect(self, *args: Any, **kwargs: Any) -> None:
        self.logger.info("Отключаем БД")
        await self.engine.dispose()
