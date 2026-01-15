import asyncio
import urllib.parse
from logging import Logger

import httpx
import stamina
from config.config import Config, get_config
from core.db.db_access import request_batch, update_file_content
from core.model.data_models import File
from httpx import AsyncClient

from src.logtools import getLogger

config: Config = get_config()


class Filehandler:
    logger: Logger
    client: AsyncClient

    def __init__(self) -> None:
        self.logger = getLogger()
        if config.https_proxy or config.http_proxy:
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=250)
            self.client = AsyncClient(proxy=config.https_proxy or config.http_proxy, timeout=config.request_timeout, limits=limits)
        else:
            self.client = AsyncClient(timeout=config.request_timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def download_and_persist_files(self, batch_size: int = 100):
        self.logger.info("Persisting content of all scraped files to database.")

        offset = 0
        while True:
            files: list[File] = request_batch(File, offset=offset, limit=batch_size)
            if not files or len(files) < 1:
                break
            semaphore = asyncio.Semaphore(batch_size)
            tasks = []

            async def sem_task(file_in):
                async with semaphore:
                    try:
                        await self.download_and_persist_file(file=file_in)
                    except Exception as e:
                        self.logger.exception(f"Could not download file '{file_in.id} - {e}'")

            for file in files:
                tasks.append(sem_task(file))

            self.logger.info(f"Queued filebatch for downloading. {offset} - {offset + batch_size}")
            await asyncio.gather(*tasks, return_exceptions=True)
            self.logger.info(f"Finished processing filebatch. {offset} - {offset + batch_size}")

            offset += batch_size

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    async def download_and_persist_file(self, file: File):
        response = await self.client.get(url=file.id)
        response.raise_for_status()
        content = response.content
        if file.content is None or content != file.content:
            content_disposition = response.headers.get("content-disposition")
            if content_disposition:
                # Parse using cgi module for robust header parsing
                import cgi

                _, params = cgi.parse_header(content_disposition)
                fileName = params.get("filename")
                if fileName:
                    fileName = urllib.parse.unquote(fileName)
                    self.logger.debug(f"Extracted fileName: {fileName}")
                else:
                    self.logger.warning(f"No filename found in Content-Disposition header for {file.id}")
                    fileName = file.name
            else:
                self.logger.debug(f"No Content-Disposition header for {file.id}")
                fileName = file.name
            self.logger.debug(f"Saving content of file {file.name} to database.")
            update_file_content(file.db_id, content, fileName)
