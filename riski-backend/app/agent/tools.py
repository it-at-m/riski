from logging import Logger
from typing import Any, TypedDict

from app.utils.logging import getLogger
from core.model.data_models import File
from langchain.tools import ToolRuntime, tool
from langchain_core.documents import Document
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import Column, select

from .types import AgentContext

logger: Logger = getLogger(name=__name__)


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
    file_ids = {doc.id for doc in documents}
    logger.info(f"Fetching proposals for file IDs: {file_ids}")
    import asyncio

    logger.info("current loop id = %s", id(asyncio.get_running_loop()))

    async with db_sessionmaker() as db_session:
        logger.info("session created")
        result = await db_session.execute(
            # test with first file only
            select(File).where(Column(File.db_id) == file_ids.pop()),
            # actual needed query
            # select(File).where(Column(File.db_id).in_(file_ids))
            execution_options={"timeout": 10},
        )
        logger.info("got result from db")

        files = result.scalars().all()
    # files = []
    logger.info(f"Look  for proposals in {len(files)} files from db.")
    # TODO: for each file find related proposals if existing
    proposals = [
        {"identifier": p.reference, "name": p.name, "risUrl": p.id} for f in files for p in f.papers if p.paper_type == "Stadtratsantrag"
    ]
    return proposals


@tool(
    description="Retrieve relevant documents and proposals based on a query.",
    return_direct=True,
    args_schema=RetrieveDocumentsArgs,
    parse_docstring=False,
    response_format="content",
)
async def retrieve_documents(
    query: str,
    runtime: ToolRuntime[AgentContext],
) -> RetrieveDocumentsOutput:
    """
    Retrieve relevant documents and proposals based on a query.

    Args:
        query (str): The search query string.
        runtime: (ToolRuntime[AgentContext]): The runtime context for the tool.

    Returns:
        RetrieveDocumentsOutput: A dictionary containing lists of retrieved documents and proposals.
    """
    # Step 1: Perform similarity search in the vector store
    logger.info(f"Retrieving documents for query: {query}")
    docs: list[Document] = await runtime.context.vectorstore.asimilarity_search(query=query, k=5)
    logger.debug(f"Retrieved {len(docs)} documents:\n{[doc.metadata for doc in docs]}")

    # Step 2: Fetch related proposals from the database
    logger.info("Get proposals for retrieved documents")
    proposals: list[dict] = await get_proposals(docs, runtime.context.db_sessionmaker)
    logger.debug(f"Retrieved {len(proposals)} proposals.")
    return RetrieveDocumentsOutput(documents=docs, proposals=proposals)
