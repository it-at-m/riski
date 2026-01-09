from urllib.parse import urlsplit

from pydantic import PostgresDsn
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine
from src.logtools import getLogger

_engine = None
_SessionLocal = None
logger = getLogger()


###########################################################
#############  Create Database Schema #####################
###########################################################
def init_db(db_url: PostgresDsn) -> None:
    """
    Initialize the module-level engine and session factory.
    Call this from the application before using get_session()/create_db_and_tables().
    """
    global _engine, _SessionLocal
    if _engine is None:
        logger.info(
            f"########## Initializing DB connection: {db_url.scheme}://<user><pw>@{urlsplit(str(db_url)).hostname}:{urlsplit(str(db_url)).port}{db_url.path} ##########"
        )
        _engine = create_engine(str(db_url), echo=False)
        _SessionLocal = sessionmaker(bind=_engine, class_=Session, expire_on_commit=False)


def get_engine():
    """
    Return initialized engine. If not available, raises.
    """
    global _engine
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_db(db_url) first.")
    return _engine


def get_session() -> Session:
    """
    Return a new Session instance from the module-level session factory.
    Application must call init_db(db_url) before this.
    Use as context manager: `with get_session() as sess: ...`
    """
    global _SessionLocal
    if _SessionLocal is None:
        raise RuntimeError("Session factory not initialized. Call init_db(db_url) first.")
    return _SessionLocal()


def create_db_and_tables() -> None:
    """
    Create DB tables.
    """
    SQLModel.metadata.create_all(get_engine())
