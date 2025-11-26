from logging import Logger

import httpx
import stamina
from config.config import Config, get_config
from httpx import Client
from src.data_models import File
from src.db.db_access import request_batch
from src.kafka.broker import LhmKafkaBroker
from src.kafka.message import Message
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
        self.broker = LhmKafkaBroker()

    def download_and_persist_files(self, batch_size: int = 100):
        self.logger.info("Persisting content of all scraped files to database.")

        offset = 0
        while True:
            files: list[File] = request_batch(File, offset=offset, limit=batch_size)
            if not files or len(files) < 1:
                break

            for file in files:
                self.logger.debug(f"Checking necessity of inserting/updating file {file.name} to database.")
                try:
                    self.download_and_persist_file(file=file)
                except Exception:
                    self.logger.exception(f"Could not download file '{file.id}'")

            offset += batch_size

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    def download_and_persist_file(self, file: File):
        # response = self.client.get(url=file.id)
        # response.raise_for_status()
        # content = response.content
        # if file.content is None or content != file.content:
        #   file.content = content
        #   file.size = len(content)
        #   self.logger.debug(f"Saving content of file {file.name} to database.")
        #   update_or_insert_objects_to_database([file])
        msg = Message(file.db_id)
        self.broker.publish(msg)
