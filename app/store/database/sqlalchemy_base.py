from sqlalchemy.orm import DeclarativeBase, declarative_base

db = declarative_base()


class BaseModel(DeclarativeBase):
    pass
