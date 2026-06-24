from collections.abc import Iterator

from sqlalchemy import Engine
from sqlmodel import Session, create_engine

_engine: Engine | None = None


def init_engine(database_url: str) -> Engine:
    """Initialise the module-level synchronous engine. Idempotent."""
    global _engine
    if _engine is None:
        _engine = create_engine(database_url, echo=False, pool_pre_ping=True, pool_recycle=1800)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Database engine not initialised. Call init_engine(url) first.")
    return _engine


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a synchronous SQLModel session."""
    with Session(get_engine()) as session:
        yield session
