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
    client = Mistral(api_key=api_key.get_secret_value(), server_url=server_url)
    ocr_model = settings.ocr_model_name
    max_docs = settings.max_documents_to_process
    batch_size = settings.ocr_batch_size
    max_pages_per_chunk = settings.ocr_max_pages_per_chunk
    max_chunk_size_mb = settings.ocr_max_chunk_size_mb
    if not batch_size:
        batch_size = 0

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
                logger.info("Processed all available documents. (Parsing)")
                break

            docs_with_content = [doc for doc in docs_to_process if doc.content is not None and doc.text is None]

            logger.info("Parsing %d files of batch (%d - %d).", len(docs_with_content), offset, offset + batch_size)

            for doc in docs_with_content:
                logger.debug(f"Processing doc id={doc.id}")
                pages_text = []
                try:
                    for pdf_chunk in chunk_pdf_into_max_page_blocks(
                        doc.content, max_pages_per_chunk=max_pages_per_chunk, max_chunk_size_mb=max_chunk_size_mb
                    ):
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
                except Exception as e:
                    logger.error(f"Error chunking for doc id={doc.id}: {e}")
                    continue

                # Combine all pages' markdown into one text blob
                full_markdown = "\n\n".join(pages_text)

                if not full_markdown or not full_markdown.strip():
                    full_markdown = None

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


def is_chunk_size_valid(pdf_bytes: bytes, max_size_mb: int) -> bool:
    """
    Checks if the size of a PDF file, when encoded in Base64, is within the specified maximum size.

    Args:
        pdf_bytes (bytes): The PDF file content in bytes.
        max_size_mb (int): The maximum allowed size in megabytes.

    Returns:
        bool: True if the Base64-encoded size of the PDF is within the limit, False otherwise.

    Notes:
        - "data:application/pdf;base64," is the prefix added to Base64-encoded data URIs.
        - ((len(pdf_bytes) + 2) // 3) * 4 calculates the size of the Base64-encoded content.
          This formula accounts for the 4:3 ratio of Base64 encoding, where every 3 bytes of input
          are encoded into 4 bytes of output, with padding as necessary.
        - max_size_mb * 1024 * 1024 converts the maximum size from megabytes to bytes.
    """
    payload_bytes = len("data:application/pdf;base64,") + ((len(pdf_bytes) + 2) // 3) * 4
    size_in_bytes = max_size_mb * 1024 * 1024
    return payload_bytes <= size_in_bytes


def split_pdf_with_size_guard(
    reader: PdfReader,
    start: int,
    end: int,
    max_size_mb: int,
) -> list[bytes]:
    writer = PdfWriter()

    for page_num in range(start, end):
        writer.add_page(reader.pages[page_num])

    stream = BytesIO()
    writer.write(stream)
    chunk_bytes = stream.getvalue()

    if is_chunk_size_valid(chunk_bytes, max_size_mb):
        return [chunk_bytes]

    num_pages = end - start
    if num_pages <= 1:
        logger.warning("Single page exceeds max size limit.")
        return [chunk_bytes]

    mid = start + num_pages // 2

    logger.debug(f"Chunk too large ({len(chunk_bytes)} bytes). Splitting further...")

    return split_pdf_with_size_guard(reader, start, mid, max_size_mb) + split_pdf_with_size_guard(reader, mid, end, max_size_mb)


def chunk_pdf_into_max_page_blocks(
    pdf_bytes: bytes,
    max_pages_per_chunk: int,
    max_chunk_size_mb: float,
) -> list[bytes]:
    """
    Split a PDF (from bytes) into chunks of up to `chunk_size` pages.
    Returns a list where each item is a PDF (as bytes) containing ≤ chunk_size pages.
    """
    reader = PdfReader(BytesIO(pdf_bytes))
    total_pages = len(reader.pages)

    output_chunks = []

    for start in range(0, total_pages, max_pages_per_chunk):
        end = min(start + max_pages_per_chunk, total_pages)

        chunks = split_pdf_with_size_guard(
            reader,
            start,
            end,
            max_chunk_size_mb,
        )
        output_chunks.extend(chunks)

    logger.debug(f"Split PDF into {len(output_chunks)} chunks (max_pages={max_pages_per_chunk}, max_size={max_chunk_size_mb}MB)")

    return output_chunks
