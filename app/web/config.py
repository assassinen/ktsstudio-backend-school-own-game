import typing
from dataclasses import dataclass

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class BotConfig:
    token: str
    url: str


@dataclass
class Database:
    drivername: str
    host: str
    database: str
    username: str
    password: str
    port: str


@dataclass
class Config:
    bot: BotConfig | None = None
    database: Database | None = None


def setup_config(app: "Application", config_path: str):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(
        bot=BotConfig(**raw_config["bot"]),
        database=Database(**raw_config["database"]),
    )
