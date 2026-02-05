import base64
from io import BytesIO

from core.db.db_access import _get_session_ctx, request_batch
from core.model.data_models import File
from mistralai import Mistral
from pypdf import PdfReader, PdfWriter

from src.logtools import getLogger

logger = getLogger()


# TODO: probably add summary for each text content
def run_ocr_for_documents(settings):
    api_key = settings.openai_api_key
    server_url = settings.openai_api_base
    client = Mistral(api_key=api_key, server_url=server_url)
    ocr_model = settings.ocr_model_name
    max_docs = settings.max_documents_to_process
    batch_size = settings.ocr_batch_size

    if max_docs is not None and max_docs <= 0:
        logger.info("max_documents_to_process is %s; skipping OCR run.", max_docs)
        return

    with _get_session_ctx() as session:
        offset = 0
        if max_docs is not None:
            logger.info(
                "Processing up to %s documents",
                max_docs,
            )
        logger.info("Start processing.")
        while True:
            if max_docs is not None and batch_size + offset > max_docs:
                limit = max_docs - offset
            else:
                limit = batch_size
            docs_to_process: list[File] = request_batch(File, offset=offset, limit=limit)

            if not docs_to_process:
                logger.info("Processed all available documents.")
                break

            docs_without_content = [doc for doc in docs_to_process if doc.content is not None and doc.text is None]

            for doc in docs_without_content:
                logger.debug(f"Processing doc id={doc.id}")
                pages_text = []
                for pdf_chunk in chunk_pdf_into_max_page_blocks(doc.content, chunk_size=30):
                    base64_pdf = base64.b64encode(pdf_chunk).decode("utf-8")
                    try:
                        resp = client.ocr.process(
                            model=ocr_model,
                            document={"type": "document_url", "document_url": f"data:application/pdf;base64,{base64_pdf}"},
                        )
                        chunk_pages_text = [page.markdown for page in resp.pages]
                        logger.debug(chunk_pages_text[: min(3, len(chunk_pages_text))])

                        pages_text.extend(chunk_pages_text)
                    except Exception as e:
                        logger.error(f"Error processing OCR for doc id={doc.id}: {e}")
                        continue

                # Combine all pages' markdown into one text blob
                full_markdown = "\n\n".join(pages_text)
                # Save to db object
                doc.text = full_markdown
                session.add(doc)
                session.commit()
            session.expunge_all()

            if max_docs is not None and offset + batch_size >= max_docs:
                logger.info("Processed max documents (%d).", max_docs)
                break

            logger.info("Parsed Files %d - %d.", offset, offset + batch_size)
            offset += batch_size


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
