from dataclasses import dataclass

from langchain_postgres import PGVectorStore
from sqlalchemy.ext.asyncio import async_sessionmaker


@dataclass
class AgentContext:
    vectorstore: PGVectorStore
    db_sessionmaker: async_sessionmaker
