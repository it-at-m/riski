from logging import Logger

from config.config import Config, get_config
from sqlmodel import Session, SQLModel, create_engine
from src.logtools import getLogger

config: Config = get_config()
logger: Logger = getLogger(__name__)

_engine = None
_session = None


###########################################################
#############  Create Database Schema ###################
###########################################################
def get_engine():
    """Lazy initialization of database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(str(config.database_url), echo=True)
    return _engine


def get_session():
    """Lazy initialization of database session."""
    global _session
    if _session is None:
        _session = Session(get_engine())
    return _session


def create_db_and_tables():
    SQLModel.metadata.create_all(get_engine())


def check_tables_exist():
    engine = get_engine()
    with engine.connect() as conn:
        from sqlalchemy import inspect as _inspect

        inspector = _inspect(conn)
        # Only use 'public' schema for Postgres; None for others like SQLite
        schema = "public" if engine.url.get_backend_name() == "postgresql" else None
        tables = inspector.get_table_names(schema=schema)
        logger.debug("Existing tables:", tables)


if __name__ == "__main__":
    try:
        create_db_and_tables()
        check_tables_exist()
    except Exception as e:
        logger.exception(f"Error initializing database: {e}")
        raise
