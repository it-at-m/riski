import asyncio
import json
from datetime import datetime
from enum import Enum
from logging import Logger
from typing import Any, TypedDict

from app.utils.logging import getLogger
from core.db.ris_queries import count_papers, find_persons, list_factions, person_factions, person_papers
from core.model.data_models import File, PaperTypeEnum
from langchain.tools import ToolException, ToolRuntime, tool
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig, RunnableLambda
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import defer, selectinload
from sqlmodel import select

from .state import TrackedDocument, TrackedProposal
from .types import AGENT_CAPABILITIES_PROMPT, AgentContext

logger: Logger = getLogger()


class RetrieveDocumentsArgs(BaseModel):
    query: str = Field(description="The search query string.")


class RetrieveDocumentsArtifact(TypedDict):
    """Shape of the artifact returned to the agent (plain dicts for state)."""

    documents: list[dict]
    proposals: list[dict]


async def get_proposals(
    documents: list[Document],
    db_sessionmaker: async_sessionmaker,
    config: RunnableConfig,
    db_query_timeout_seconds: int,
    db_query_total_timeout_seconds: int,
    force_db_timeout: bool = False,
) -> list[TrackedProposal]:
    """Fetch proposals related to the given documents from the database.

    Args:
        documents (list[Document]): List of documents to find related proposals for.
        db_sessionmaker (async_sessionmaker): The async session maker for database access.
        db_query_timeout_seconds (int): Per-statement asyncio timeout for the database query (seconds).
        db_query_total_timeout_seconds (int): Total asyncio timeout including connection overhead (seconds).
        force_db_timeout (bool): If True, immediately raise TimeoutError (for testing).

    Returns:
        list[TrackedProposal]: A list of proposals related to the documents.
    """
    proposals_by_key: dict[tuple[str, str], TrackedProposal] = {}
    if documents:
        file_ids = {doc.id for doc in documents}
        logger.debug(f"Fetching proposals for file IDs: {file_ids}")

        if force_db_timeout:
            raise asyncio.TimeoutError("forced DB timeout for testing")

        async with db_sessionmaker() as db_session:
            try:

                async def call_db(_):
                    result = await asyncio.wait_for(
                        db_session.execute(
                            select(File)
                            .where(File.db_id.in_(file_ids))
                            .options(
                                selectinload(File.papers),
                                defer(File.text),
                                defer(File.content),
                                defer(File.embed),
                            ),  # type: ignore[arg-type, attr-defined]
                        ),
                        timeout=db_query_total_timeout_seconds,
                    )
                    files = result.scalars().all()
                    return files

                files = await RunnableLambda(call_db).ainvoke(None, config)  # type: ignore
            except asyncio.TimeoutError:
                logger.error(
                    f"get_proposals timed out waiting for DB query (timeout={db_query_total_timeout_seconds}s, file_ids={file_ids})"
                )
                raise

            logger.debug(f"Look for proposals in {len(files)} files from db.")
            for f in files:
                if not f.papers:
                    continue
                file_id = str(f.db_id)
                for p in f.papers:
                    if p.paper_type != "Stadtratsantrag":
                        continue
                    key = (str(p.reference or ""), str(p.id or ""))
                    existing = proposals_by_key.get(key)
                    if existing:
                        if file_id not in existing.source_document_ids:
                            existing.source_document_ids.append(file_id)
                    else:
                        proposals_by_key[key] = TrackedProposal(
                            identifier=str(p.reference or ""),
                            name=str(p.name or ""),
                            subject=str(p.subject or ""),
                            date=p.date.isoformat() if p.date else None,
                            risUrl=str(p.id or ""),
                            source_document_ids=[file_id],
                        )
    return list(proposals_by_key.values())


@tool(
    description="Retrieve relevant documents and proposals based on a query.",
    args_schema=RetrieveDocumentsArgs,
    parse_docstring=False,
    # Use content_and_artifact so the raw dict is available in on_tool_end as `artifact`
    response_format="content_and_artifact",
)
async def retrieve_documents(
    query: str, runtime: ToolRuntime[AgentContext], config: RunnableConfig
) -> tuple[str, RetrieveDocumentsArtifact]:
    """
    Retrieve relevant documents and proposals based on a query.

    The artifact carries ``TrackedDocument`` / ``TrackedProposal`` dicts
    so the guard node can write them directly into state without parsing
    message content.
    """
    try:
        logger.info(f"Retrieving documents for query: {query}")
        if runtime.context is None:
            vectorstore = config["configurable"]["vectorstore"]
            db_sessionmaker = config["configurable"]["db_sessionmaker"]
            top_k_docs = config["configurable"]["top_k_docs"]
            db_query_timeout_seconds = config["configurable"]["db_query_timeout_seconds"]
            db_query_total_timeout_seconds = config["configurable"]["db_query_total_timeout_seconds"]
            vectorstore_timeout_seconds = config["configurable"]["vectorstore_timeout_seconds"]
            force_vectorstore_timeout: bool = config["configurable"].get("force_vectorstore_timeout", False)
            force_db_timeout: bool = config["configurable"].get("force_db_timeout", False)
        else:
            vectorstore = runtime.context["vectorstore"]
            db_sessionmaker = runtime.context["db_sessionmaker"]
            top_k_docs = runtime.context["top_k_docs"]
            db_query_timeout_seconds = runtime.context["db_query_timeout_seconds"]
            db_query_total_timeout_seconds = runtime.context["db_query_total_timeout_seconds"]
            vectorstore_timeout_seconds = runtime.context["vectorstore_timeout_seconds"]
            force_vectorstore_timeout = runtime.context.get("force_vectorstore_timeout", False)
            force_db_timeout = runtime.context.get("force_db_timeout", False)
            logger.debug(f"Using context: {runtime.context} of type {type(runtime.context)}")

        # Step 1: Perform similarity search in the vector store
        if force_vectorstore_timeout:
            raise asyncio.TimeoutError("forced vectorstore timeout for testing")
        try:

            async def call_vectorstore(_):
                docs: list[Document] = await asyncio.wait_for(
                    vectorstore.asimilarity_search(query=query, k=top_k_docs),
                    timeout=vectorstore_timeout_seconds,
                )
                return docs

            docs = await RunnableLambda(call_vectorstore).ainvoke(None, config)  # type: ignore
        except asyncio.TimeoutError:
            logger.error(f"retrieve_documents timed out waiting for vector store (timeout={vectorstore_timeout_seconds}s)")
            raise ToolException("TIMEOUT: vector store query timed out")
        logger.debug(f"Retrieved {len(docs)} documents:\n{[doc.metadata for doc in docs]}")

        if not docs:
            logger.info("No documents found for query.")
            empty_artifact: RetrieveDocumentsArtifact = {"documents": [], "proposals": []}
            return json.dumps({"documents": [], "proposals": []}), empty_artifact

        # Step 2: Fetch related proposals from the database
        logger.info("Get proposals for retrieved documents")
        proposals: list[TrackedProposal] = await get_proposals(
            docs,
            db_sessionmaker,
            config,
            db_query_timeout_seconds,
            db_query_total_timeout_seconds,
            force_db_timeout=force_db_timeout,
        )

        # Build TrackedDocument entries (is_checked=False, is_relevant=True by default)
        tracked_docs = [TrackedDocument(id=doc.id or "", page_content=doc.page_content, metadata=doc.metadata) for doc in docs]

        # Artifact carries serialised TrackedDocument / TrackedProposal dicts
        artifact: RetrieveDocumentsArtifact = {
            "documents": [d.model_dump() for d in tracked_docs],
            "proposals": [p.model_dump() for p in proposals],
        }

        # Content is a human-readable summary for the ToolMessage text
        content_summary = json.dumps(
            {
                "documents": [{"id": d.id, "name": d.metadata.get("name", d.id)} for d in tracked_docs],
                "proposals": [{"identifier": p.identifier, "name": p.name} for p in proposals],
            }
        )

        return content_summary, artifact
    except asyncio.TimeoutError:
        logger.error(f"retrieve_documents timed out waiting for DB query (timeout={db_query_total_timeout_seconds}s)")
        raise ToolException("TIMEOUT: database query timed out")
    except Exception as e:
        logger.error(f"Error in retrieve_documents tool: {e}", exc_info=True)
        raise ToolException(f"Failed to retrieve documents: {str(e)}")


class RisDbOperation(str, Enum):
    """Allowed structured RIS database operations for the agent tool."""

    LIST_FACTIONS = "list_factions"
    SEARCH_PERSONS = "search_persons"
    PERSON_FACTIONS = "person_factions"
    PERSON_PAPERS = "person_papers"
    COUNT_PAPERS = "count_papers"


class QueryRisDatabaseArgs(BaseModel):
    operation: RisDbOperation = Field(
        description=(
            "Structured RIS database operation. Use list_factions for questions like "
            "'Welche Fraktionen gibt es?'; search_persons for ambiguous person lookups; "
            "person_factions for 'In welcher Fraktion ist XY?'; person_papers for "
            "'Welche Anträge hat XY eingereicht?'; count_papers for "
            "'Wie viele Anträge wurden seit/bis/in einem Zeitraum eingereicht?'."
        )
    )
    person_name: str | None = Field(
        default=None,
        description="Person name. Required for search_persons, person_factions and person_papers.",
    )
    since: str | None = Field(
        default=None,
        description="Inclusive start date as ISO date/datetime, e.g. YYYY-MM-DD. Resolve relative dates before calling.",
    )
    until: str | None = Field(
        default=None,
        description="Inclusive end date as ISO date/datetime, e.g. YYYY-MM-DD. Resolve relative dates before calling.",
    )
    paper_type: PaperTypeEnum | None = Field(
        default=PaperTypeEnum.COUNCIL_PROPOSAL,
        description=(
            "Paper/proposal type filter. Default is Stadtratsantrag. Set to null only if the user explicitly asks across all paper types."
        ),
    )
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of returned rows.")
    include_inactive: bool = Field(
        default=False,
        description="Whether inactive factions/organizations should be included for list_factions.",
    )


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


@tool(
    description=(
        "Query structured RIS database tables for persons, factions/organizations, memberships and papers/proposals. "
        "Use this for factual data questions such as 'Welche Fraktionen gibt es?', "
        "'In welcher Fraktion ist XY?', 'Welche Anträge hat Person XY eingereicht?' or "
        "'Wie viele Anträge wurden seit einem Datum eingereicht?'. Do not use this tool for "
        "questions about the content/text of documents; use retrieve_documents for that."
    ),
    args_schema=QueryRisDatabaseArgs,
    parse_docstring=False,
    response_format="content_and_artifact",
)
async def query_ris_database(
    operation: RisDbOperation,
    runtime: ToolRuntime[AgentContext],
    config: RunnableConfig,
    person_name: str | None = None,
    since: str | None = None,
    until: str | None = None,
    paper_type: PaperTypeEnum | None = PaperTypeEnum.COUNCIL_PROPOSAL,
    limit: int = 20,
    include_inactive: bool = False,
) -> tuple[str, dict[str, Any]]:
    """Run a safe, structured RIS database query and return JSON data to the model."""
    try:
        if runtime.context is None:
            db_sessionmaker = config["configurable"]["db_sessionmaker"]
            db_query_total_timeout_seconds = config["configurable"]["db_query_total_timeout_seconds"]
            force_db_timeout: bool = config["configurable"].get("force_db_timeout", False)
        else:
            db_sessionmaker = runtime.context["db_sessionmaker"]
            db_query_total_timeout_seconds = runtime.context["db_query_total_timeout_seconds"]
            force_db_timeout = runtime.context.get("force_db_timeout", False)

        if force_db_timeout:
            raise asyncio.TimeoutError("forced DB timeout for testing")

        since_dt = _parse_optional_datetime(since)
        until_dt = _parse_optional_datetime(until)

        async with db_sessionmaker() as db_session:

            async def call_db(_):
                if operation == RisDbOperation.LIST_FACTIONS:
                    return await list_factions(db_session, include_inactive=include_inactive, limit=limit)

                if operation == RisDbOperation.SEARCH_PERSONS:
                    if not person_name:
                        raise ValueError("person_name is required for search_persons")
                    return await find_persons(db_session, person_name=person_name, limit=limit)

                if operation == RisDbOperation.PERSON_FACTIONS:
                    if not person_name:
                        raise ValueError("person_name is required for person_factions")
                    return await person_factions(db_session, person_name=person_name, limit=limit)

                if operation == RisDbOperation.PERSON_PAPERS:
                    if not person_name:
                        raise ValueError("person_name is required for person_papers")
                    return await person_papers(
                        db_session,
                        person_name=person_name,
                        paper_type=paper_type,
                        since=since_dt,
                        until=until_dt,
                        limit=limit,
                    )

                if operation == RisDbOperation.COUNT_PAPERS:
                    return await count_papers(
                        db_session,
                        paper_type=paper_type,
                        since=since_dt,
                        until=until_dt,
                    )

                raise ValueError(f"Unsupported RIS DB operation: {operation}")

            data = await asyncio.wait_for(
                RunnableLambda(call_db).ainvoke(None, config),  # type: ignore[arg-type]
                timeout=db_query_total_timeout_seconds,
            )

        artifact: dict[str, Any] = {
            "operation": operation.value,
            "data": data,
        }
        return json.dumps(artifact, ensure_ascii=False, default=str), artifact

    except asyncio.TimeoutError:
        logger.error("query_ris_database timed out waiting for DB query")
        raise ToolException("TIMEOUT: database query timed out")
    except Exception as e:
        logger.error("Error in query_ris_database tool: %s", e, exc_info=True)
        raise ToolException(f"Failed to query RIS database: {str(e)}")


class GetAgentCapabilitiesArgs(BaseModel):
    """No arguments needed – the tool returns static capability information."""


@tool(
    description=(
        "Return information about the RISKI agent's current knowledge base, capabilities, and the topics it can answer questions about."
    ),
    args_schema=GetAgentCapabilitiesArgs,
    parse_docstring=False,
    response_format="content_and_artifact",
)
async def get_agent_capabilities(config: RunnableConfig) -> tuple[str, dict]:
    """
    Return a description of the agent's knowledge and capabilities.

    The content is sourced from a Langfuse prompt so it can be updated
    without redeploying the service.  A plain-text fallback is used when
    the prompt is not available via context.
    """
    try:
        capabilities_text: str = config.get("configurable", {}).get("agent_capabilities", AGENT_CAPABILITIES_PROMPT)

        logger.info("Returning agent capabilities.")
        artifact: dict = {"capabilities": capabilities_text}
        return capabilities_text, artifact
    except Exception as e:
        logger.error(f"Error in get_agent_capabilities tool: {e}", exc_info=True)
        raise ToolException(f"Failed to retrieve agent capabilities: {str(e)}")
