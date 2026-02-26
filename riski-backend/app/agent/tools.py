import json
from logging import Logger
from typing import TypedDict

from app.utils.logging import getLogger
from core.model.data_models import File
from langchain.tools import ToolException, ToolRuntime, tool
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload
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


async def get_proposals(documents: list[Document], db_sessionmaker: async_sessionmaker) -> list[TrackedProposal]:
    """Fetch proposals related to the given documents from the database.

    Args:
        documents (list[Document]): List of documents to find related proposals for.
        db_sessionmaker (async_sessionmaker): The async session maker for database access.

    Returns:
        list[TrackedProposal]: A list of proposals related to the documents.
    """
    proposals_by_key: dict[tuple[str, str], TrackedProposal] = {}
    if documents:
        file_ids = {doc.id for doc in documents}
        logger.debug(f"Fetching proposals for file IDs: {file_ids}")

        async with db_sessionmaker() as db_session:
            result = await db_session.execute(
                select(File).where(File.db_id.in_(file_ids)).options(selectinload(File.papers)),  # type: ignore[arg-type, attr-defined]
                execution_options={"timeout": 10},
            )

            files = result.scalars().all()
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
        else:
            vectorstore = runtime.context["vectorstore"]
            db_sessionmaker = runtime.context["db_sessionmaker"]
            top_k_docs = runtime.context["top_k_docs"]
            logger.debug(f"Using context: {runtime.context} of type {type(runtime.context)}")

        # Step 1: Perform similarity search in the vector store
        docs: list[Document] = await vectorstore.asimilarity_search(query=query, k=top_k_docs)
        logger.debug(f"Retrieved {len(docs)} documents:\n{[doc.metadata for doc in docs]}")

        if not docs:
            logger.info("No documents found for query.")
            empty_artifact: RetrieveDocumentsArtifact = {"documents": [], "proposals": []}
            return json.dumps({"documents": [], "proposals": []}), empty_artifact

        # Step 2: Fetch related proposals from the database
        logger.info("Get proposals for retrieved documents")
        proposals: list[TrackedProposal] = await get_proposals(docs, db_sessionmaker)

        # Build TrackedDocument entries (is_checked=False, is_relevant=True by default)
        tracked_docs = [
            TrackedDocument(
                id=doc.id or "",
                page_content=doc.page_content,
                metadata=doc.metadata,
            )
            for doc in docs
        ]

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
    except Exception as e:
        logger.error(f"Error in retrieve_documents tool: {e}", exc_info=True)
        raise ToolException(f"Failed to retrieve documents: {str(e)}")


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
