from logging import Logger
from typing import Any, TypedDict

from app.utils.logging import getLogger
from core.model.data_models import File
from langchain.tools import ToolException, ToolRuntime, tool
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlmodel import select

from .types import AgentContext

logger: Logger = getLogger()


class RetrieveDocumentsArgs(BaseModel):
    query: str = Field(description="The search query string.")


class RetrieveDocumentsOutput(TypedDict):
    documents: list[Document]
    proposals: list[dict[str, Any]]


async def get_proposals(documents: list[Document], db_sessionmaker: async_sessionmaker) -> list[dict[str, Any]]:
    """Fetch proposals related to the given documents from the database.

    Args:
        documents (list[Document]): List of documents to find related proposals for.
        db_sessionmaker (async_sessionmaker): The async session maker for database access.

    Returns:
        list[dict[str, Any]]: A list of proposals related to the documents.
    """
    proposals = []
    if documents:
        file_ids = {doc.id for doc in documents}
        logger.debug(f"Fetching proposals for file IDs: {file_ids}")

        async with db_sessionmaker() as db_session:
            result = await db_session.execute(
                select(File).where(File.db_id.in_(file_ids)).options(selectinload(File.papers)),
                execution_options={"timeout": 10},
            )

            files = result.scalars().all()
            # files = []
            logger.debug(f"Look for proposals in {len(files)} files from db.")
            # for each file find related proposals if existing
            proposals = [
                {"identifier": p.reference, "name": p.name, "risUrl": p.id}
                for f in files
                if f.papers
                for p in f.papers
                if p.paper_type == "Stadtratsantrag"
            ]
    return proposals


@tool(
    description="Retrieve relevant documents and proposals based on a query.",
    args_schema=RetrieveDocumentsArgs,
    parse_docstring=False,
    response_format="content",
)
async def retrieve_documents(query: str, runtime: ToolRuntime[AgentContext], config: RunnableConfig) -> RetrieveDocumentsOutput:
    """
    Retrieve relevant documents and proposals based on a query.

    Args:
        query (str): The search query string.
        runtime: (ToolRuntime[AgentContext]): The runtime context for the tool.

    Returns:
        RetrieveDocumentsOutput: A dictionary containing lists of retrieved documents and proposals.
    """
    # raise ToolException("DB down - try again later.")
    try:
        logger.info(f"Retrieving documents for query: {query}")
        if runtime.context is None:
            vectorstore = config["configurable"]["vectorstore"]
            db_sessionmaker = config["configurable"]["db_sessionmaker"]
        # currently not supported in AG-UI langgraph agent - but future
        else:
            vectorstore = runtime.context["vectorstore"]
            db_sessionmaker = runtime.context["db_sessionmaker"]
            logger.debug(f"Using context: {runtime.context} of type {type(runtime.context)}")
        # Step 1: Perform similarity search in the vector store
        docs: list[Document] = await vectorstore.asimilarity_search(query=query, k=5)
        logger.debug(f"Retrieved {len(docs)} documents:\n{[doc.metadata for doc in docs]}")

        # Step 2: Fetch related proposals from the database
        logger.info("Get proposals for retrieved documents")
        proposals: list[dict] = await get_proposals(docs, db_sessionmaker)
        logger.debug(f"Retrieved {len(proposals)} proposals.")
        return RetrieveDocumentsOutput(documents=docs, proposals=proposals)
    except Exception as e:
        logger.error(f"Error in retrieve_documents tool: {e}", exc_info=True)
        raise ToolException(f"Failed to retrieve documents: {str(e)}")
