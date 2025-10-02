from logging import Logger

import httpx
import stamina
from config.config import Config, get_config
from httpx import Client
from src.data_models import File
from src.db.db_access import request_all, update_or_insert_objects_to_database
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

    def download_and_persist_files(self):
        self.logger.info("Persisting content of all scraped files to database.")
        files: list[File] = request_all(File)
        for file in files:
            self.logger.debug(f"Checking necessity of inserting/updating file {file.name} to database.")
            self.download_and_persist_file(file=file)

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def download_and_persist_file(self, file: File):
        content = self.client.get(url=file.id).content
        if not bytes(content) == file.content:
            file.content = bytes(content)
            file.size = len(content)
            self.logger.debug(f"Saving content of file {file.name} to database.")
            update_or_insert_objects_to_database([file])
