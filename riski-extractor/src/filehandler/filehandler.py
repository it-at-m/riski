import asyncio
import urllib.parse
from logging import Logger

import httpx
from config.config import Config, get_config
from httpx import AsyncClient
from src.data_models import File
from src.db.db_access import request_batch, update_or_insert_objects_to_database
from src.logtools import getLogger

config: Config = get_config()


class Filehandler:
    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        if config.https_proxy or config.http_proxy:
            limits = httpx.Limits(max_keepalive_connections=10001, max_connections=10001)
            self.client = AsyncClient(proxy=config.https_proxy or config.http_proxy, timeout=config.request_timeout, limits=limits)
        else:
            self.client = AsyncClient(timeout=config.request_timeout)

    async def download_and_persist_files(self, batch_size: int = 20):
        self.logger.info("Persisting content of all scraped files to database.")

        offset = 0
        tasks = []
        batch_files = []
        while True:
            files: list[File] = request_batch(File, offset=offset, limit=batch_size)

            if not files or len(files) < 1:
                break

            for file in files:
                self.logger.debug(f"Checking necessity of inserting/updating file {file.name} to database.")
                try:
                    tasks.append(self.download_and_persist_file(file=file))
                    batch_files.append(file)
                    self.logger.info(f"Queued file {file.name} for downloading.")
                except Exception:
                    self.logger.exception(f"Could not schedule file download for '{file.id}'")

            offset += batch_size

        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful_files = []
        for file, result in zip(files, results):
            if isinstance(result, Exception):
                self.logger.error(f"Could not download file '{file.id}'. - {result}")
            else:
                successful_files.append(file)

        if successful_files:
            self.logger.debug(f"Saving content of {len(successful_files)} files to database.")
            update_or_insert_objects_to_database(successful_files)

    # @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
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
                    file.fileName = fileName
                else:
                    self.logger.warning(f"No filename found in Content-Disposition header for {file.id}")
            else:
                self.logger.debug(f"No Content-Disposition header for {file.id}")
            file.content = content
            file.size = len(content)
            self.logger.debug(f"Saving content of file {file.name} to database.")
            update_or_insert_objects_to_database([file])
