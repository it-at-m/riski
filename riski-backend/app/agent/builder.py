from datetime import datetime
from logging import Logger

from ag_ui_langgraph import LangGraphAgent
from app.core.settings import BackendSettings, InMemoryCheckpointerSettings, RedisCheckpointerSettings, get_settings
from app.utils.logging import getLogger
from langchain_core.callbacks import Callbacks
from langchain_openai import ChatOpenAI
from langchain_postgres import PGVectorStore
from langfuse import Langfuse
from langfuse.model import TextPromptClient
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.redis import AsyncShallowRedisSaver
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import async_sessionmaker

from .riski_agent import build_riski_graph
from .tools import retrieve_documents

settings: BackendSettings = get_settings()
logger: Logger = getLogger()


# ---------------------------------------------------------------------------
# Agent builder
# ---------------------------------------------------------------------------


async def build_agent(
    vectorstore: PGVectorStore, db_sessionmaker: async_sessionmaker, callbacks: Callbacks, lf_client: Langfuse
) -> LangGraphAgent:
    """
    Constructs and returns a configured RISKI LangGraphAgent with a custom graph.

    The graph enforces that the ``retrieve_documents`` tool is called and
    returns non-empty results **before** the model generates its final answer.
    If the tool is not called or returns no results, the agent deterministically
    responds with a fixed "no results" message — no LLM generation happens.
    """

    # Build the chat model
    chat_model: ChatOpenAI = ChatOpenAI(
        model_name=settings.core.genai.chat_model,
        temperature=settings.core.genai.chat_temperature,
        max_retries=settings.core.genai.chat_max_retries,
    )

    # Bind tools so the model knows about them
    tools = [retrieve_documents]
    try:
        system_prompt_template: TextPromptClient = lf_client.get_prompt(
            name=settings.langfuse_system_prompt_name, label=settings.langfuse_system_prompt_label
        )
        system_prompt = system_prompt_template.compile(
            date_written=datetime.now().strftime("%A, %d %B %Y - %H:%M"),
            date_isoformat=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to fetch system prompt from Langfuse: {e}")
        raise ValueError(
            f"Could not retrieve the {settings.langfuse_system_prompt_name} prompt (label={settings.langfuse_system_prompt_label}) from Langfuse. "
            "Ensure the prompt exists and Langfuse is reachable."
        )

    graph = build_riski_graph(
        chat_model=chat_model,
        tools=tools,
        system_prompt=system_prompt,
    )

    # -- Configure checkpointer --
    checkpointer: BaseCheckpointSaver
    if isinstance(settings.checkpointer, InMemoryCheckpointerSettings):
        checkpointer = InMemorySaver()
    elif isinstance(settings.checkpointer, RedisCheckpointerSettings):
        async_redis: AsyncRedis = AsyncRedis.from_url(
            url=settings.checkpointer.redis_url.encoded_string(),
        )
        checkpointer = AsyncShallowRedisSaver(
            redis_client=async_redis,
            ttl={
                "default_ttl": settings.checkpointer.ttl_minutes,
                "refresh_on_read": True,
            },
        )
        await checkpointer.asetup()
    else:
        raise ValueError("Unsupported checkpointer configuration")

    compiled = graph.compile(checkpointer=checkpointer)

    # Wrap in AG-UI LangGraphAgent
    return LangGraphAgent(
        name="RISKI Agent",
        description="Der RISKI Agent unterstützt bei der Recherche und Analyse von Dokumenten und Beschlussvorlagen aus dem Rats-Informations-System der Stadt München.",
        graph=compiled,
        config={
            "configurable": {"vectorstore": vectorstore, "db_sessionmaker": db_sessionmaker},
            "callbacks": callbacks,
        },
    )
