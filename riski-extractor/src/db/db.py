from config.config import get_config
from sqlmodel import Session, SQLModel, create_engine

_engine = create_engine(str(get_config().database_url), echo=False)
_session = Session(_engine)


def create_tables():
    SQLModel.metadata.create_all(_engine)
