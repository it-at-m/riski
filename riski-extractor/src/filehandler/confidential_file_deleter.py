import datetime
from logging import Logger

from config.config import get_config
from core.db.db_access import remove_object_by_id, request_batch
from core.model.data_models import File
from src.filehandler.file_id_collector import get_all_found_file_ids
from src.logtools import getLogger


class ConfidentialFileDeleter:
    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.config = get_config()

    def delete_confidential_files(self):
        doc_ids = get_all_found_file_ids()
        limit = self.config.riski_batch_size
        offset = 0
        while True:
            files: list[File] = request_batch(File, offset=offset, limit=limit)

            if not files:
                break

            for file in files:
                if not file.modified:
                    continue

                if file.id not in doc_ids and datetime.datetime.strptime(self.config.start_date, "%Y-%m-%d") < file.modified:
                    remove_object_by_id(file.id, File)
                    self.logger.info(f"Deleted File: {file.id}")

            offset += limit
