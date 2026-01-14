import asyncio
import urllib.parse
from logging import Logger

import httpx
import stamina
from config.config import Config, get_config
from core.db.db_access import request_batch, update_file_content
from core.model.data_models import File
from faststream.kafka import KafkaBroker
from httpx import Client
from src.kafka.message import Message
from src.logtools import getLogger

config: Config = get_config()


class Filehandler:
    logger: Logger

    def __init__(self, kafkaBroker: KafkaBroker) -> None:
        self.logger = getLogger(__name__)
        if config.https_proxy or config.http_proxy:
            self.client = Client(proxy=config.https_proxy or config.http_proxy, timeout=config.request_timeout)
        else:
            self.client = Client(timeout=config.request_timeout)
        self.broker = kafkaBroker
        self.logger.info("Filehandler created.")

    async def download_and_persist_files(self, batch_size: int = 100):
        self.logger.info("Persisting content of all scraped files to database.")
        tasks = []
        all_files = []
        offset = 0
        while True:
            files: list[File] = request_batch(File, offset=offset, limit=batch_size)

            if not files or len(files) < 1:
                break

            for file in files:
                tasks.append(self.download_and_persist_file(file=file))
                all_files.append(file)

            offset += batch_size
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for file, result in zip(all_files, results):
            if isinstance(result, Exception):
                self.logger.error(f"Could not download file '{file.id}'. - {result}")

    @stamina.retry(on=httpx.HTTPError, attempts=config.max_retries)
    async def download_and_persist_file(self, file: File):
        response = self.client.get(url=file.id)
        response.raise_for_status()
        content = response.content
        self.logger.debug(f"Checking necessity of inserting/updating file {file.name} to database.")
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

            file.content = content
            file.size = len(content)
            self.logger.debug(f"Saving content of file {file.name} to database.")
            update_file_content(file.db_id, content, fileName)
            self.logger.debug(f"Saved content of file {file.name} to database.")
            msg = Message(content=str(file.db_id))
            self.logger.debug(f"Publishing: {msg}.")
            try:
                await self.broker.publish(msg, topic=config.kafka_topic)
                self.logger.debug(f"Published: {msg}.")
            except Exception as e:
                # If Kafka Broker is unavailable rollback the file download to ensure
                # All Documents that have content, are published to the Kafka Queue
                update_file_content(file.db_id, None, "")
                self.logger.error(f"Publishing failed. Rolled file download back: {file.db_id}. - {e}")
