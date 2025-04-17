from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import declarative_base

db = declarative_base()

class BaseModel(DeclarativeBase):
    pass
