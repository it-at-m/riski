from logging import Logger
from typing import Any

from ag_ui_langgraph import LangGraphAgent
from app.core.settings import BackendSettings, InMemoryCheckpointerSettings, RedisCheckpointerSettings, get_settings
from app.utils.logging import getLogger
from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langchain.tools import BaseTool
from langchain_core.callbacks import Callbacks
from langchain_openai import ChatOpenAI
from langchain_postgres import PGVectorStore
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.redis import AsyncRedisSaver
from pydantic import BaseModel, Field
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import async_sessionmaker

from .tools import retrieve_documents
from .types import AgentContext

settings: BackendSettings = get_settings()
logger: Logger = getLogger()


class StructuredAgentResponse(BaseModel):
    response: str = Field(description="The final answer to the user's question.")
    documents: list[dict[str, Any]] = Field(description="List of documents supporting the answer.")
    proposals: list[dict[str, Any]] = Field(description="List of proposals related to the supporting documents.")


async def build_agent(vectorstore: PGVectorStore, db_sessionmaker: async_sessionmaker, callbacks: Callbacks) -> LangGraphAgent:
    """Build and return the RISKI agent."""

    # Build the chat model
    chat_model: ChatOpenAI = ChatOpenAI(
        model_name=settings.core.genai.chat_model,
        temperature=settings.core.genai.chat_temperature,
        max_retries=settings.core.genai.chat_max_retries,
    )

    # Configure the checkpointer
    checkpointer: BaseCheckpointSaver
    if isinstance(settings.checkpointer, InMemoryCheckpointerSettings):
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

    system_prompt: str = """
        You are the RISKI Agent, an AI assistant designed to help users research and analyze documents and proposals from the City of Munich's Council Information System. 
        Your goal is to provide accurate, concise, and relevant information based on the user's queries and the documents available to you.
        
        Tools:
        You have access to the following tools to assist you in your tasks:
        1. retrieve_documents: Use this tool to search for and retrieve documents relevant to the user's query.
    """

    # Create the agent via the factory method
    agent = create_agent(
        model=chat_model,
        system_prompt=system_prompt,
        tools=available_tools,
        response_format=ProviderStrategy(StructuredAgentResponse),
        context_schema=AgentContext,  # type: ignore
        checkpointer=checkpointer,
    )

    # Context usage probably supported in future LangGraphAgent versions
    # agent_result = await agent.ainvoke(
    #     input={"messages": [{"role": "user", "content": "Wird in München über eine Zweitwohnungssteuer diskutiert?"}]},
    #     config={
    #         "configurable": {"thread_id": uuid4(), "vectorstore": vectorstore, "db_sessionmaker": db_sessionmaker},
    #         "callbacks": callbacks,
    #     },
    #     # context=AgentContext(vectorstore=vectorstore, db_sessionmaker=db_sessionmaker),
    # )

    # logger.info(f"Agent test invocation result: {agent_result}")

    # Wrap the agent in a AG-UI LangGraphAgent
    return LangGraphAgent(
        name="RISKI Agent",
        description="Der RISKI Agent unterstützt bei der Recherche und Analyse von Dokumenten und Beschlussvorlagen aus dem Rats-Informations-System der Stadt München.",
        graph=agent,  # type: ignore
        config={
            "configurable": {"vectorstore": vectorstore, "db_sessionmaker": db_sessionmaker},
            "callbacks": callbacks,
        },  # Workaround as LangGraphAgent doesnt yet support context parameter
    )
