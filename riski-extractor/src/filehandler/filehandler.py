import asyncio
import urllib.parse
from logging import Logger

import httpx
import stamina
from config.config import Config, get_config
from core.db.db_access import request_all_ids, request_object_by_risid, update_file_content
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

    async def download_and_persist_files(self):
        self.logger.info("Persisting content of all scraped files to database.")

        fileUrls = request_all_ids(File)

        semaphore = asyncio.Semaphore(250)
        tasks = []

        async def sem_task(fileUrl):
            async with semaphore:
                try:
                    await self.download_and_persist_file(fileUrl=fileUrl)
                except Exception as e:
                    self.logger.exception(f"Could not download file '{fileUrl} - {e}'")

        for fileUrl in fileUrls:
            tasks.append(sem_task(fileUrl))

        self.logger.info("Queued files for downloading.")
        await asyncio.gather(*tasks, return_exceptions=True)
        self.logger.info("Finished processing files.")

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    async def download_and_persist_file(self, fileUrl: str):
        file = request_object_by_risid(fileUrl, File)
        response = await self.client.get(url=file.id)
        self.logger.debug(f"Finished downloading: {fileUrl}")

        response.raise_for_status()
        content = response.content
        if file.content is None or content != file.content:
            self.logger.debug(f"Update file: {fileUrl}")
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
            else:
                self.logger.debug(f"No Content-Disposition header for {file.id}")
            self.logger.debug(f"Saving content of file {file.name} to database.")
            update_file_content(file.db_id, content, fileName)
