from collections.abc import AsyncGenerator

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session from app state."""
    db_sessionmaker: async_sessionmaker[AsyncSession] | None = getattr(request.app.state, "db_sessionmaker", None)
    if db_sessionmaker is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database session factory is not initialized")

    async with db_sessionmaker() as session:
        yield session
