import base64
from io import BytesIO

from core.db.db_access import _get_session_ctx
from core.model.data_models import File
from mistralai import Mistral
from pypdf import PdfReader, PdfWriter
from sqlmodel import select

from src.logtools import getLogger

logger = getLogger()


def run_ocr_for_documents(settings):
    api_key = settings.openai_api_key
    server_url = settings.openai_api_base
    client = Mistral(api_key=api_key, server_url=server_url)

    LOCAL_TEST = False
    if LOCAL_TEST:
        # Process only first 2 for testing
        NUM_DOCS_TO_PROCESS = 2

    with _get_session_ctx() as session:
        # Query documents which haven't had OCR yet TODO: replace with kafka consumer
        docs = session.exec(select(File).where(File.content != None, File.text == None)).all()  # noqa: E711
        logger.info(f"Found {len(docs)} documents to process.")
        for doc in docs[:NUM_DOCS_TO_PROCESS] if LOCAL_TEST else docs:
            logger.debug(f"Processing doc id={doc.id}")
            pages_text = []
            for pdf_chunk in chunk_pdf_into_max_page_blocks(doc.content, chunk_size=30):
                base64_pdf = base64.b64encode(pdf_chunk).decode("utf-8")
                resp = client.ocr.process(
                    model="mistral-document-ai-2505",
                    document={"type": "document_url", "document_url": f"data:application/pdf;base64,{base64_pdf}"},
                )
                chunk_pages_text = [page.markdown for page in resp.pages]
                logger.debug(chunk_pages_text[: min(3, len(chunk_pages_text))])

                pages_text.extend(chunk_pages_text)

            # Combine all pages' markdown into one text blob
            full_markdown = "\n\n".join(pages_text)
            # Save to db object
            doc.text = full_markdown
            session.add(doc)
            session.commit()


def chunk_pdf_into_max_page_blocks(pdf_bytes: bytes, chunk_size: int = 30) -> list[bytes]:
    """
    Split a PDF (from bytes) into chunks of up to `chunk_size` pages.
    Returns a list where each item is a PDF (as bytes) containing ≤ chunk_size pages.
    """
    reader = PdfReader(BytesIO(pdf_bytes))
    total_pages = len(reader.pages)

    output_chunks = []

    for start in range(0, total_pages, chunk_size):
        writer = PdfWriter()

        end = min(start + chunk_size, total_pages)

        # Add pages into this chunk
        for page_num in range(start, end):
            writer.add_page(reader.pages[page_num])

        # Serialize this chunk into bytes
        stream = BytesIO()
        writer.write(stream)
        output_chunks.append(stream.getvalue())

    logger.debug(f"Split PDF into {len(output_chunks)} chunks of up to {chunk_size} pages each.")
    return output_chunks
