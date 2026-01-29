from logging import Logger
from typing import Any

from ag_ui_langgraph import LangGraphAgent
from app.core.settings import BackendSettings, RedisCheckpointerSettings, get_settings
from app.utils.logging import getLogger
from langchain.agents import create_agent
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_postgres import PGVectorStore
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.redis import AsyncRedisSaver
from langgraph.graph.state import CompiledStateGraph
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import async_sessionmaker

from .tools import retrieve_documents
from .types import AgentContext

settings: BackendSettings = get_settings()
logger: Logger = getLogger()


async def build_agent(vectorstore: PGVectorStore, db_sessionmaker: async_sessionmaker) -> LangGraphAgent:
    """Build and return the RISKI agent."""

    # Build the chat model
    chat_model: ChatOpenAI = ChatOpenAI(
        model_name=settings.core.genai.chat_model,
        temperature=settings.core.genai.chat_temperature,
        max_retries=settings.core.genai.chat_max_retries,
    )

    # Configure the checkpointer
    checkpointer: BaseCheckpointSaver
    if settings.checkpointer is None:
        checkpointer = InMemorySaver()
    elif isinstance(settings.checkpointer, RedisCheckpointerSettings):
        # Instantiate Redis client and saver directly
        logger.info(f"{settings.checkpointer.redis_url.encoded_string()=}")
        async_redis: AsyncRedis = AsyncRedis.from_url(
            url=settings.checkpointer.redis_url.encoded_string(),
        )
        checkpointer = AsyncRedisSaver(
            redis_client=async_redis,
            ttl={
                "default_ttl": settings.checkpointer.ttl_minutes,
                "refresh_on_read": True,
            },
        )
        # Setup the checkpointer inside an async context
        await checkpointer.setup()
    else:
        raise ValueError("Unsupported checkpointer configuration")

    # Configure the tools
    available_tools: list[BaseTool] = [retrieve_documents]

    # Create the agent via the factory method
    agent: CompiledStateGraph[Any, AgentContext, Any, Any] = create_agent(
        model=chat_model,
        tools=available_tools,
        context_schema=AgentContext,
        checkpointer=checkpointer,
    )

    # Wrap the agent in a AG-UI LangGraphAgent
    return LangGraphAgent(
        name="RISKI Agent",
        description="Der RISKI Agent unterstützt bei der Recherche und Analyse von Dokumenten und Beschlussvorlagen aus dem Rats-Informations-System der Stadt München.",
        graph=agent,  # type: ignore
        config={
            "configurable": {"vectorstore": vectorstore, "db_sessionmaker": db_sessionmaker}
        },  # Workaround as LangGraphAgent doesnt yet support context parameter
    )
