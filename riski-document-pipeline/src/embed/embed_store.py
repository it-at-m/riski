from core.db.db_access import _get_session_ctx
from core.genai import create_embedding_model
from core.model.data_models import File
from langchain_text_splitters import TokenTextSplitter
from sqlmodel import select

from src.logtools import getLogger

logger = getLogger()


def embed_documents(settings):
    embedding_model = create_embedding_model(settings)

    with _get_session_ctx() as session:
        # TODO: add chunking
        # find in file_chunk table
        # docs = session.exec(select(File).where(File.chunks != None)).all()  # noqa: E711
        docs = session.exec(select(File).where(File.embed == None, File.text != None)).all()  # noqa: E711
        logger.info(f"Found {len(docs)} documents to process.")
        for doc in docs:
            try:
                doc.embed = embedding_model.embed_documents([temp_chunk(doc.text)])[0]
            except Exception as e:
                logger.error(f"Error embedding doc id={doc.id}: {e}")
                continue
            session.add(doc)
            session.commit()


def temp_chunk(text: str):
    splitter = TokenTextSplitter(
        # TODO: from settings + reasonable values 500/100?
        chunk_size=5000,
        chunk_overlap=200,
        encoding_name="cl100k_base",
    )

    chunks = splitter.split_text(text)
    return chunks[0]
