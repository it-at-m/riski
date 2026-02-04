from langchain_postgres import PGVectorStore
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.util.typing import TypedDict


class AgentContext(TypedDict):
    vectorstore: PGVectorStore
    db_sessionmaker: async_sessionmaker
