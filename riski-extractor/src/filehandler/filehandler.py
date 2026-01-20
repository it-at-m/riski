import urllib.parse
from logging import Logger

import stamina
from config.config import Config, get_config
from core.db.db_access import request_batch, update_file_content
from core.model.data_models import File
from httpx import Client, HTTPError

from src.logtools import getLogger

config: Config = get_config()


class Filehandler:
    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        if config.https_proxy or config.http_proxy:
            self.client = Client(proxy=config.https_proxy or config.http_proxy, timeout=config.request_timeout)
        else:
            self.client = Client(timeout=config.request_timeout)

    def download_and_persist_files(self, batch_size: int = 100):
        self.logger.info("Persisting content of all scraped files to database.")

        offset = 0
        while True:
            files: list[File] = request_batch(File, offset=offset, limit=batch_size)

            if not files:
                break

            for file in files:
                self.logger.debug(f"Checking necessity of inserting/updating file {file.name} to database.")
                try:
                    self.download_and_persist_file(file=file)
                except Exception:
                    self.logger.exception(f"Could not download file '{file.id}'")

            offset += batch_size

    @stamina.retry(on=HTTPError, attempts=config.max_retries)
    def download_and_persist_file(self, file: File):
        response = self.client.get(url=file.id)
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
            else:
                self.logger.debug(f"No Content-Disposition header for {file.id}")
            self.logger.debug(f"Saving content of file {file.name} to database.")
            update_file_content(file.db_id, content, fileName)
