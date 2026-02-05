from core.db.db_access import _get_session_ctx, request_batch
from core.lm.helper import create_embedding_model
from core.model.data_models import File
from langchain_text_splitters import TokenTextSplitter

from src.logtools import getLogger

logger = getLogger()


def embed_documents(settings):
    embedding_model = create_embedding_model(settings)
    batch_size = settings.ocr_batch_size
    offset = 0

    with _get_session_ctx() as session:
        # TODO: add chunking
        # find in file_chunk table
        # docs = session.exec(select(File).where(File.chunks != None)).all()  # noqa: E711
        logger.info("Start emebdding")
        while True:
            docs_to_process: list[File] = request_batch(File, offset=offset, limit=batch_size)

            if not docs_to_process:
                logger.info("Processed all available documents.")
                break

            docs_without_embedding = [doc for doc in docs_to_process if doc.embed is None and doc.text is not None]

            for doc in docs_without_embedding:
                try:
                    doc.embed = embedding_model.embed_documents([temp_chunk(doc.text)])[0]
                except Exception as e:
                    logger.error(f"Error embedding doc id={doc.id}: {e}")
                    continue
                session.add(doc)
                session.commit()
            session.expunge_all()
            logger.info("Embedded Files %d - %d.", offset, offset + batch_size)
            offset += batch_size


def temp_chunk(text: str):
    splitter = TokenTextSplitter(
        # TODO: from settings + reasonable values 500/100?
        chunk_size=5000,
        chunk_overlap=200,
        encoding_name="cl100k_base",
    )

    chunks = splitter.split_text(text)
    return chunks[0]
