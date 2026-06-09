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
from .tools import get_agent_capabilities, query_ris_database, retrieve_documents
from .types import AGENT_CAPABILITIES_PROMPT, CHECK_DOCUMENT_PROMPT_TEMPLATE

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

    The graph routes content questions through ``retrieve_documents`` and structured
    RIS database questions through ``query_ris_database``. Document retrieval
    results are relevance-checked before final generation; structured DB results
    are routed directly back to the model for the final answer.
    """

    # Build the chat model
    chat_model: ChatOpenAI = ChatOpenAI(
        model_name=settings.core.genai.chat_model,
        temperature=settings.core.genai.chat_temperature,
        max_retries=settings.core.genai.chat_max_retries,
        timeout=settings.core.genai.chat_timeout_seconds,
    )

    # Build the relevance check model
    relevance_check_model: ChatOpenAI = ChatOpenAI(
        model_name=settings.core.genai.relevance_check_model,
        temperature=settings.core.genai.relevance_check_temperature,
        max_retries=settings.core.genai.relevance_check_max_retries,
        timeout=settings.core.genai.relevance_check_timeout_seconds,
    )

    # Bind tools so the model knows about them
    tools = [retrieve_documents, query_ris_database, get_agent_capabilities]
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

    try:
        check_document_prompt_template: TextPromptClient | str = lf_client.get_prompt(
            name=settings.langfuse_check_document_prompt_name, label=settings.langfuse_check_document_prompt_label
        )
    except Exception as e:
        logger.warning(
            "Failed to fetch check-document prompt from Langfuse, using local template: %s",
            e,
        )
        check_document_prompt_template = CHECK_DOCUMENT_PROMPT_TEMPLATE

    try:
        agent_capabilities_prompt: TextPromptClient = lf_client.get_prompt(
            name=settings.langfuse_agent_capabilities_prompt_name,
            label=settings.langfuse_agent_capabilities_prompt_label,
        )
        agent_capabilities: str = agent_capabilities_prompt.compile()
    except Exception as e:
        logger.warning(
            "Failed to fetch agent-capabilities prompt from Langfuse, using local fallback: %s",
            e,
        )
        agent_capabilities = AGENT_CAPABILITIES_PROMPT

    graph = build_riski_graph(
        chat_model=chat_model,
        relevance_check_model=relevance_check_model,
        tools=tools,
        system_prompt=system_prompt,
        check_document_prompt_template=check_document_prompt_template,
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
        description="Der RISKI Agent unterstützt bei der Recherche und Analyse von Dokumenten, Beschlussvorlagen sowie strukturierten Personen-, Fraktions- und Antragsdaten aus dem Rats-Informations-System der Stadt München.",
        graph=compiled,
        config={
            "configurable": {
                "vectorstore": vectorstore,
                "db_sessionmaker": db_sessionmaker,
                "top_k_docs": settings.top_k_docs,
                "agent_capabilities": agent_capabilities,
                "db_query_timeout_seconds": settings.db_query_timeout_seconds,
                "db_query_total_timeout_seconds": settings.db_query_total_timeout_seconds,
                "vectorstore_timeout_seconds": settings.vectorstore_timeout_seconds,
                "force_vectorstore_timeout": settings.force_vectorstore_timeout,
                "force_db_timeout": settings.force_db_timeout,
                "force_llm_timeout": settings.force_llm_timeout,
            },
            "callbacks": callbacks,
            # Cap parallel check_document fan-out branches to avoid overwhelming
            # the LLM API with too many concurrent requests.
            "max_concurrency": settings.check_document_max_concurrency,
        },
    )
